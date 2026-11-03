"""[房玄龄·2026-11-03] Real private-endpoint migration acceptance.
Authored test questions only. Evidence and credentials go to a private local directory.
"""
from pathlib import Path
import httpx, json, secrets, time, datetime

out = Path.home()/'.local/share/recordchat/verification'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out.mkdir(parents=True,mode=0o700,exist_ok=False)
base = 'http://dev.tail0f631b.ts.net:13001'
questions = [
 'What is IATA ONE Record? Explain briefly and cite your sources.',
 'Explain the difference between a Shipment and a Piece in ONE Record.',
 'What is a LogisticsObject in ONE Record?',
 'How does JSON-LD use @id and @type in ONE Record?',
 'What is a LogisticsEvent and how is it related to an object?',
 'How do the ONE Record data model and REST API relate?',
 'How should a developer distinguish normative ONE Record specifications from community examples?',
 'How does ONE Record differ from Cargo-XML? State the limits of your sources.',
 'What is NE:ONE and what role does it play in ONE Record development?',
 'Which ONE Record objects would you examine for a shipment tracking integration?',
]
summary=[];credentials=[];quota=[]
with httpx.Client(base_url=base,timeout=180,follow_redirects=False,trust_env=False) as c:
    for i, question in enumerate(questions):
        if i % 3 == 0:
            cred={'email':'migration-eval-'+secrets.token_hex(5)+'@example.invalid','password':secrets.token_urlsafe(24)}
            credentials.append(cred)
            r=c.post('/api/auth/signup',json=cred);r.raise_for_status()
            r=c.post('/api/auth/login',json=cred);r.raise_for_status()
        started=time.monotonic()
        r=c.post('/api/chat',json={'messages':[{'role':'user','parts':[{'type':'text','text':question}]}],'synthetic_mode':'local'})
        events=[]
        for line in r.text.splitlines():
            if line.startswith('data: ') and line[6:]!='[DONE]':
                try:events.append(json.loads(line[6:]))
                except json.JSONDecodeError:pass
        result=next((e['data'] for e in events if e.get('type')=='data-recordchat'),{})
        finished=any(e.get('type')=='finish' for e in events)
        errors=[e for e in events if e.get('type')=='error']
        sources=result.get('sources',[])
        good=r.status_code==200 and finished and not errors and bool(result.get('answer')) and bool(sources)
        item={'question':question,'status':r.status_code,'seconds':round(time.monotonic()-started,2),'finished':finished,'errors':errors,'source_count':len(sources),'http_source_count':sum(str(s.get('source_url','')).startswith('http') for s in sources),'passed_transport_and_sources':good}
        summary.append(item)
        (out/f'staging-eval-{i+1:02}.json').write_text(json.dumps({'summary':item,'result':result},ensure_ascii=False,indent=2))
        print(json.dumps(item),flush=True)
        if not good:raise RuntimeError('Real-answer acceptance failed; evidence preserved')
        if i % 3 == 2:
            limited=c.post('/api/chat',json={'messages':[{'role':'user','parts':[{'type':'text','text':'What is ONE Record?'}]}]})
            quota.append(limited.status_code)
            assert limited.status_code==429,limited.text[:300]
    r=c.post('/api/auth/logout');assert r.status_code==200
(out/'staging-eval-users.private.json').write_text(json.dumps(credentials));(out/'staging-eval-users.private.json').chmod(0o600)
(out/'staging-eval-summary.json').write_text(json.dumps({'answers':summary,'quota_statuses':quota,'limitation':'Sources and stream delivery checked; no claim of full semantic correctness or source URL availability.'},indent=2))
print('STAGING_REAL_ACCEPTANCE_PASS',len(summary),'quota',quota,flush=True)

