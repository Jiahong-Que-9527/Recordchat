"""[房玄龄·2026-11-03] WSL build-once / import / deploy workflow.
No public registry, secret transfer in logs, file deletion or automatic Git pushes.
prepare: build current clean Git revision and save a private release bundle.
deploy: import that exact artifact, dry-run, Ansible --limit dev, wait for rollout.
"""
from pathlib import Path
import argparse, subprocess, json, hashlib, gzip, shutil, datetime, re, sys

p=argparse.ArgumentParser()
p.add_argument('action',choices=['prepare','deploy'])
p.add_argument('--release')
p.add_argument('--env',choices=['staging','prod'],default='staging')
p.add_argument('--staging-accepted',action='store_true',help='Operator confirms acceptance of this same release on staging before prod')
a=p.parse_args()
repo=Path(__file__).resolve().parents[1]
private=Path.home()/'.local/share/recordchat/releases';private.mkdir(parents=True,mode=0o700,exist_ok=True)
docker=str(Path.home()/'.local/bin/recordchat-docker')
ssh=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','dev']
scp=['scp','-p','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes']

def run(args,**kw):return subprocess.run(args,check=True,**kw)

if a.action=='prepare':
    dirty=subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=repo,text=True)
    if dirty:sys.exit('Commit tracked changes before creating a release; no reset or cleanup is performed.')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    tag=revision[:12]
    if a.release and a.release!=tag:sys.exit('Release must match the clean Git revision prefix')
    dest=private/tag;dest.mkdir(mode=0o700,exist_ok=False)
    run([str(Path.home()/'.local/bin/uv'),'run','--project',str(repo/'backend'),'--frozen','pytest','-q','-p','no:cacheprovider'],cwd=repo/'backend')
    for component in ['backend','frontend']:
        args=[docker,'build','--label','org.opencontainers.image.revision='+revision,'-t',f'recordchat/{component}:{tag}']
        if component=='frontend':args+=['--build-arg','AUTH_MODE=enforced']
        with (dest/(component+'-build.log')).open('w') as log:run(args+[str(repo/component)],stdout=log,stderr=subprocess.STDOUT)
    images=[f'recordchat/{c}:{tag}' for c in ['frontend','backend']]
    # Qdrant/gateway stay at the pinned references in configuration; import cache already exists on dev.
    with gzip.open(dest/'images.tar.gz','wb',compresslevel=1) as f:
        proc=subprocess.Popen([docker,'save']+images,stdout=subprocess.PIPE)
        shutil.copyfileobj(proc.stdout,f);assert proc.wait()==0
    run(['tar','-czf',str(dest/'source.tar.gz'),'-C',str(repo),'deploy','ops','docs/k3s_operations.md'])
    run(['git','bundle','create',str(dest/'source.git.bundle'),'HEAD'],cwd=repo)
    manifest={'release':tag,'git_revision':revision,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':{}}
    for name in ['images.tar.gz','source.tar.gz','source.git.bundle']:
        q=dest/name;manifest['files'][name]={'bytes':q.stat().st_size,'sha256':hashlib.file_digest(q.open('rb'),'sha256').hexdigest()}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2));print('PREPARED',tag,dest)
else:
    tag=a.release or '';assert re.fullmatch('[0-9a-f]{12}',tag),'--release must be a 12-character Git SHA'
    if a.env=='prod' and not a.staging_accepted:sys.exit('Run staging acceptance for this release, then pass --staging-accepted to promote the same artifact.')
    dest=private/tag;m=json.loads((dest/'manifest.json').read_text())
    for name,v in m['files'].items():assert hashlib.file_digest((dest/name).open('rb'),'sha256').hexdigest()==v['sha256']
    remote='/opt/recordchat/releases/'+tag
    run(ssh+['install -d -m 700 '+remote])
    run(scp+[str(dest/n) for n in ['images.tar.gz','source.tar.gz','source.git.bundle','manifest.json']]+['dev:'+remote+'/'])
    script='''from pathlib import Path
import json,hashlib,subprocess,gzip,sys
root=Path(sys.argv[1]);env=sys.argv[2];m=json.loads((root/'manifest.json').read_text())
for name,v in m['files'].items():assert hashlib.file_digest((root/name).open('rb'),'sha256').hexdigest()==v['sha256']
with gzip.open(root/'images.tar.gz','rb') as f:subprocess.run(['k3s','ctr','-n','k8s.io','images','import','-'],stdin=f,check=True)
subprocess.run(['tar','-xzf',str(root/'source.tar.gz'),'-C',str(root)],check=True)
p=root/'deploy/k8s/overlays'/env/'kustomization.yaml';d=json.loads(p.read_text());d['images']=[{'name':'recordchat/'+c,'newTag':m['release']} for c in ['frontend','backend']];p.write_text(json.dumps(d,indent=2)+'\\n')
subprocess.run(['kubectl','apply','--dry-run=server','-k',str(p.parent)],check=True)
'''
    run(ssh+['python3 - '+remote+' '+a.env],input=script.encode())
    if a.env=='prod':run(ssh+['python3 /opt/recordchat/ops/backup.py prod'])
    args=[str(Path.home()/'.local/bin/ansible-playbook'),'-i',str(repo/'ops/ansible/inventory.yml'),str(repo/'ops/ansible/deploy.yml'),'--limit','dev','-e','target_env='+a.env,'-e','release_root='+remote]
    run(args+['--check','--diff']);run(args)
    for name in ['backend','frontend','gateway']:
        run(ssh+['kubectl rollout status deployment/'+name+' -n recordchat-'+a.env+' --timeout=120s'])
    run(ssh+['kubectl rollout status statefulset/qdrant -n recordchat-'+a.env+' --timeout=120s'])
    marker_script = """from pathlib import Path
import json,subprocess,datetime,sys,shutil
root=Path('/opt/recordchat/state');root.mkdir(mode=0o700,exist_ok=True)
env,tag,config=sys.argv[1:];now=datetime.datetime.now(datetime.timezone.utc);stamp=now.strftime('%Y%m%dT%H%M%S%fZ')
state={'environment':env,'release':tag,'config_root':config,'verified_utc':now.isoformat(),'pods':json.loads(subprocess.check_output(['kubectl','get','pods','-n','recordchat-'+env,'-o','json']))}
current=root/('current-'+env+'.json')
if current.exists():shutil.copy2(current,root/(env+'-'+stamp+'-previous.json'))
text=json.dumps(state,indent=2);(root/(env+'-'+stamp+'.json')).write_text(text);current.write_text(text)
"""
    run(ssh+['python3 - '+a.env+' '+tag+' '+remote],input=marker_script.encode())
    # Append-only evidence; no overwritten release history.
    print('DEPLOYED',a.env,tag,'CONFIG_ROOT',remote,'Run acceptance; image rollback does not roll back database schema.')

