"""[房玄龄·2026-11-03] Non-destructive RecordChat backup on dev.
Run as root: python3 /opt/recordchat/ops/backup.py staging|prod
No pruning or retention deletion. Copy the reported private directory off-host.
"""
from pathlib import Path
import subprocess, json, base64, urllib.request, time, datetime, sqlite3, shutil, hashlib, sys

env=sys.argv[1] if len(sys.argv)>1 else 'prod'
assert env in ['staging','prod']
ns='recordchat-'+env
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out=Path('/var/backups/recordchat')/ns/stamp
out.mkdir(mode=0o700,parents=True,exist_ok=False)
root=Path('/var/lib/recordchat')/ns
source=sqlite3.connect('file:'+str(root/'app-state/recordchat.db')+'?mode=ro',uri=True)
dest=sqlite3.connect(out/'recordchat.db');source.backup(dest)
assert dest.execute('pragma integrity_check').fetchone()[0]=='ok'
dest.close();source.close()
secret=json.loads(subprocess.check_output(['kubectl','get','secret','recordchat-secrets','-n',ns,'-o','json']))
(out/'secret.private.json').write_text(json.dumps(secret));(out/'secret.private.json').chmod(0o600)
key=base64.b64decode(secret['data']['QDRANT_API_KEY']).decode()
p=subprocess.Popen(['kubectl','port-forward','-n',ns,'svc/qdrant','16335:6333','--address=127.0.0.1'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
try:
    for _ in range(30):
        try:
            urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:16335/healthz',headers={'api-key':key}),timeout=2);break
        except Exception:time.sleep(1)
    else:raise RuntimeError('Qdrant port-forward unavailable')
    request=urllib.request.Request('http://127.0.0.1:16335/collections/recordchat_one_record/snapshots',headers={'api-key':key},method='POST')
    name=json.load(urllib.request.urlopen(request,timeout=120))['result']['name']
    request=urllib.request.Request('http://127.0.0.1:16335/collections/recordchat_one_record/snapshots/'+name,headers={'api-key':key})
    with urllib.request.urlopen(request,timeout=120) as r,(out/'qdrant.snapshot').open('wb') as f:shutil.copyfileobj(r,f)
    request=urllib.request.Request('http://127.0.0.1:16335/collections/recordchat_one_record',headers={'api-key':key})
    (out/'qdrant-collection.json').write_bytes(urllib.request.urlopen(request).read())
finally:p.terminate();p.wait(timeout=15)
subprocess.run(['tar','-czf',str(out/'corpus.tar.gz'),'-C',str(root/'corpus'),'.'],check=True)
subprocess.run(['tar','-czf',str(out/'logs.tar.gz'),'-C',str(root/'logs'),'.'],check=True)
subprocess.run(['tar','-czf',str(out/'deployment-source.tar.gz'),'-C','/opt/recordchat','deploy','ops'],check=True)
if Path('/opt/recordchat/state').exists():subprocess.run(['tar','-czf',str(out/'release-state.tar.gz'),'-C','/opt/recordchat','state'],check=True)
(out/'pods.json').write_bytes(subprocess.check_output(['kubectl','get','pods','-n',ns,'-o','json']))
(out/'resources.yaml').write_bytes(subprocess.check_output(['kubectl','get','deploy,sts,svc,cm,pvc,networkpolicy','-n',ns,'-o','yaml']))
if env=='prod':
    cp=out/'control-plane';cp.mkdir(mode=0o700)
    source=sqlite3.connect('file:/var/lib/rancher/k3s/server/db/state.db?mode=ro',uri=True)
    dest=sqlite3.connect(cp/'state.db');source.backup(dest);dest.close();source.close()
    for name,src in [('server-token','/var/lib/rancher/k3s/server/token'),('encryption-config.json','/var/lib/rancher/k3s/server/cred/encryption-config.json'),('k3s-config.yaml','/etc/rancher/k3s/config.yaml')]:
        shutil.copy2(src,cp/name);(cp/name).chmod(0o600)
for name in ['recordchat-backup.service','recordchat-backup.timer']:
    unit=Path('/etc/systemd/system')/name
    if unit.exists():shutil.copy2(unit,out/name)
manifest={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()} for p in out.rglob('*') if p.is_file()}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'backup_path':str(out),'files':len(manifest),'bytes':sum(v['bytes'] for v in manifest.values())}),flush=True)

