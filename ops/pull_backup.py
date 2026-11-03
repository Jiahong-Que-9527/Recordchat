"""[房玄龄·2026-11-03] Pull and verify a private dev backup into WSL.
With --create, first create a new prod backup. Otherwise pull the latest completed one.
Never prunes local or remote files. No credentials are printed.
"""
from pathlib import Path
import argparse,subprocess,json,hashlib,sqlite3
p=argparse.ArgumentParser();p.add_argument('--create',action='store_true');a=p.parse_args()
ssh=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','dev']
if a.create:
    raw=subprocess.check_output(ssh+['python3 /opt/recordchat/ops/backup.py prod'],text=True)
    remote=json.loads(raw.strip().splitlines()[-1])['backup_path']
else:
    code="from pathlib import Path; p=Path('/var/backups/recordchat/recordchat-prod'); print(sorted(x.parent for x in p.glob('*/manifest.json'))[-1])"
    remote=subprocess.check_output(ssh+['python3 -c '+__import__('shlex').quote(code)],text=True).strip()
assert remote.startswith('/var/backups/recordchat/recordchat-prod/')
root=Path.home()/'.local/share/recordchat/backups';root.mkdir(parents=True,mode=0o700,exist_ok=True)
dest=root/Path(remote).name
assert not dest.exists(),'This backup already exists locally; verify it, never overwrite it.'
subprocess.run(['scp','-r','-p','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','dev:'+remote,str(root)],check=True)
m=json.loads((dest/'manifest.json').read_text())
for name,v in m.items():
    f=dest/name;assert f.stat().st_size==v['bytes'] and hashlib.file_digest(f.open('rb'),'sha256').hexdigest()==v['sha256']
c=sqlite3.connect('file:'+str(dest/'recordchat.db')+'?mode=ro',uri=True);assert c.execute('pragma integrity_check').fetchone()[0]=='ok';c.close()
print('OFFHOST_BACKUP_VERIFIED',dest,len(m),sum(v['bytes'] for v in m.values()))

