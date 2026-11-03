"""[房玄龄·2026-11-03] Restore a dev backup into an isolated, new recovery namespace.
No existing data is overwritten; no objects/files are deleted. Recovered workloads
are scaled to zero after verification. Real model keys are removed and kill=true.
Usage on dev: python3 /opt/recordchat/ops/restore_rehearsal.py --backup ABS_PATH --target recordchat-recovery-UNIQUE
"""
from pathlib import Path
import argparse,subprocess,json,yaml,hashlib,sqlite3,shutil,tarfile,secrets,base64,urllib.request,time
p=argparse.ArgumentParser();p.add_argument('--backup',required=True);p.add_argument('--target',required=True);a=p.parse_args()
b=Path(a.backup).resolve();assert str(b).startswith('/var/backups/recordchat/')
ns=a.target;assert ns.startswith('recordchat-recovery-') and all(c.islower() or c.isdigit() or c=='-' for c in ns)
assert subprocess.run(['kubectl','get','namespace',ns],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode!=0,'Namespace exists; choose a new target'
m=json.loads((b/'manifest.json').read_text())
for name,v in m.items():assert hashlib.file_digest((b/name).open('rb'),'sha256').hexdigest()==v['sha256']
root=Path('/var/lib/recordchat')/ns;root.mkdir(mode=0o700,parents=True,exist_ok=False)
for name in ['app-state','corpus','logs','qdrant-storage']:(root/name).mkdir(mode=0o700)
shutil.copy2(b/'recordchat.db',root/'app-state/recordchat.db')
with tarfile.open(b/'corpus.tar.gz') as t:t.extractall(root/'corpus',filter='data')
for name in ['app','logs']:(root/'corpus'/name).mkdir(exist_ok=True)
c=sqlite3.connect('file:'+str(root/'app-state/recordchat.db')+'?mode=ro',uri=True);assert c.execute('pragma integrity_check').fetchone()[0]=='ok';counts={t:c.execute('select count(*) from '+t).fetchone()[0] for t in ['users','sessions','usage_daily','audit_events']};c.close()
secret=json.loads((b/'secret.private.json').read_text());values={k:base64.b64decode(v).decode() for k,v in secret['data'].items()}
values.update({'LLM_API_KEY':'','EMBEDDING_API_KEY':'','LLM_KILL_SWITCH':'true','INTERNAL_AUTH_SECRET':secrets.token_hex(32),'EMAIL_HASH_PEPPER':secrets.token_hex(32),'QDRANT_API_KEY':secrets.token_hex(32),'ADMIN_EMAILS':'','ADMIN_IDP_USER_IDS':''})
items=[{'apiVersion':'v1','kind':'Namespace','metadata':{'name':ns}},{'apiVersion':'v1','kind':'Secret','metadata':{'name':'recordchat-secrets','namespace':ns},'type':'Opaque','stringData':values}]
saved=yaml.safe_load((b/'resources.yaml').read_text())
for obj in saved['items']:
    if not obj:continue
    kind=obj['kind'];name=obj['metadata']['name']
    if kind=='ConfigMap' and name=='kube-root-ca.crt':continue
    obj.pop('status',None)
    obj['metadata']={k:v for k,v in obj['metadata'].items() if k in ['name','labels']}
    if kind=='Service':
        for field in ['clusterIP','clusterIPs','ipFamilies','ipFamilyPolicy','healthCheckNodePort']:obj['spec'].pop(field,None)
    if kind=='Deployment' and name in ['frontend','gateway']:continue
    if kind=='Service' and name=='frontend':continue
    if kind=='ConfigMap' and name=='gateway-config':continue
    if kind=='PersistentVolume':
        claim=obj['spec']['claimRef']['name'];obj['metadata']['name']=ns+'-'+claim;obj['spec']['claimRef']['namespace']=ns;obj['spec']['hostPath']['path']=str(root/claim)
    else:
        obj['metadata']['namespace']=ns
        if kind=='PersistentVolumeClaim':
            obj['spec']['volumeName']=ns+'-'+name
            pv_spec={'capacity':obj['spec']['resources']['requests'],'accessModes':['ReadWriteOnce'],'persistentVolumeReclaimPolicy':'Retain','storageClassName':'','claimRef':{'namespace':ns,'name':name},'hostPath':{'path':str(root/name),'type':'Directory'}}
            pv_spec['nodeAffinity']={'required':{'nodeSelectorTerms':[{'matchExpressions':[{'key':'kubernetes.io/hostname','operator':'In','values':['sololakehouse']}]}]}}
            items.append({'apiVersion':'v1','kind':'PersistentVolume','metadata':{'name':ns+'-'+name},'spec':pv_spec})
    items.append(obj)
subprocess.run(['kubectl','apply','-f','-'],input=json.dumps({'apiVersion':'v1','kind':'List','items':items}).encode(),check=True,stdout=subprocess.DEVNULL)
subprocess.run(['kubectl','rollout','status','statefulset/qdrant','-n',ns,'--timeout=90s'],check=True)
proc=subprocess.Popen(['kubectl','port-forward','-n',ns,'svc/qdrant','16337:6333','--address=127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(60):
        try:urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:16337/healthz',headers={'api-key':values['QDRANT_API_KEY']}),timeout=2);break
        except Exception:time.sleep(1)
    else:raise RuntimeError('Recovery Qdrant unavailable')
    data=(b/'qdrant.snapshot').read_bytes();boundary='RecordChat'+secrets.token_hex(12)
    body=('--'+boundary+'\r\nContent-Disposition: form-data; name="snapshot"; filename="restore.snapshot"\r\nContent-Type: application/octet-stream\r\n\r\n').encode()+data+('\r\n--'+boundary+'--\r\n').encode()
    req=urllib.request.Request('http://127.0.0.1:16337/collections/recordchat_one_record/snapshots/upload?priority=snapshot',data=body,headers={'api-key':values['QDRANT_API_KEY'],'Content-Type':'multipart/form-data; boundary='+boundary},method='POST');urllib.request.urlopen(req,timeout=180).read()
    req=urllib.request.Request('http://127.0.0.1:16337/collections/recordchat_one_record',headers={'api-key':values['QDRANT_API_KEY']})
    result=json.load(urllib.request.urlopen(req))['result'];expected=json.loads((b/'qdrant-collection.json').read_text())['result']
    assert result['points_count']==expected['points_count'] and result['config']['params']['vectors']==expected['config']['params']['vectors']
finally:proc.terminate();proc.wait(timeout=15)
subprocess.run(['kubectl','rollout','status','deployment/backend','-n',ns,'--timeout=90s'],check=True)
report={'namespace':ns,'backup':str(b),'sqlite_integrity':'ok','counts':counts,'qdrant_points':result['points_count'],'model_calls_disabled':True,'external_gateway':False}
(root/'recovery-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
subprocess.run(['kubectl','scale','deployment/backend','statefulset/qdrant','--replicas=0','-n',ns],check=True)
print('RECOVERY_VERIFIED_AND_STOPPED_DATA_RETAINED',ns,flush=True)

