#!/usr/bin/env python3
"""Isolated original local mock; only synthetic test identities, no real recipients."""
import sys,subprocess,tempfile,time,json,socket
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
from pharma.config import PACKAGE,ROOT
from pharma.actions import ActionStore
import httpx
out=ROOT/'06_评测/incremental_20260916/rpa_live.json'
results=[]
def check(name,ok):
 results.append({'name':name,'status':'PASS' if ok else 'FAIL'})
 if not ok:raise AssertionError(name)
with tempfile.TemporaryDirectory(prefix='pharma-rpa-test-',dir='/tmp') as tmp:
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 base=f'http://127.0.0.1:{port}'
 log=(Path(tmp)/'mock.log').open('w')
 def start():
  p=subprocess.Popen([sys.executable,'-m','uvicorn','mock_rpa_server:app','--app-dir',str(PACKAGE/'05_RPA接口文档'),'--host','127.0.0.1','--port',str(port)],stdout=log,stderr=log)
  for _ in range(60):
   try:
    if httpx.get(base+'/health').status_code==200:return p
   except httpx.HTTPError:pass
   time.sleep(.1)
  raise RuntimeError('mock startup timeout')
 p=start();s=ActionStore(Path(tmp)/'state.sqlite')
 snapshot={'snapshot_id':'synthetic-rpa-live','analysis_type':'monthly','month':'2026-05','product':'自动回归合成产品'}
 def draft(finding):return s.draft(snapshot,finding,{'name':'自动回归待分配','department':'合成测试部'},'只核对合成记录；不通知真人')
 try:
  a=draft('模拟通知回归');check('confirmation_required',s.pending()==[])
  a=s.confirm(a['id'],a['payload_hash']);s.confirm(a['id'],a['payload_hash']);check('duplicate_confirm_single_outbox',len(s.pending())==1)
  with httpx.Client(timeout=5) as c:
   sent=s.deliver_one(a['id'],c,base);check('original_mock_ack_verified',sent['delivery']['notification']=='SIMULATED_SENT')
   stats=c.get(base+'/api/stats').json();s.deliver_one(a['id'],c,base);check('duplicate_delivery_no_second_notification',c.get(base+'/api/stats').json()['data']==stats['data'])
   t=draft('读取响应超时回归');t=s.confirm(t['id'],t['payload_hash']);posts=[]
   def timeout_after_accept(request):
    if request.method=='POST':
     posts.append(1);res=c.post(base+'/api/rpa/tasks',content=request.content,headers={'Content-Type':'application/json'});res.raise_for_status();raise httpx.ReadTimeout('synthetic response-loss after real accept',request=request)
    return httpx.Response(200,json=c.get(base+'/api/rpa/tasks/'+t['id']).json())
   with httpx.Client(transport=httpx.MockTransport(timeout_after_accept)) as simulated:
    reconciled=s.deliver_one(t['id'],simulated,base);check('timeout_queries_real_original_mock',reconciled['status']=='SENT' and len(posts)==1)
    s.deliver_one(t['id'],simulated,base);check('timeout_no_duplicate_post',len(posts)==1)
   conflict=draft('载荷冲突回归');c.post(base+'/api/rpa/tasks',json={**conflict['payload'],'suggestion':'不同合成内容'}).raise_for_status()
   conflict=s.confirm(conflict['id'],conflict['payload_hash']);check('remote_payload_conflict',s.deliver_one(conflict['id'],c,base)['status']=='CONFLICT')
  p.terminate();p.wait(timeout=10);p=start()
  with httpx.Client(timeout=5) as c:
   check('remote_restart_state_unknown',s.refresh(a['id'],c,base)['status']=='REMOTE_UNKNOWN')
   before=c.get(base+'/api/stats').json()['data'];s.deliver_one(a['id'],c,base);check('restart_never_resends',c.get(base+'/api/stats').json()['data']==before)
  status='PASS'
 except Exception as exc:status='FAIL';results.append({'error':type(exc).__name__+': '+str(exc)})
 finally:p.terminate();p.wait(timeout=10);log.close()
out.write_text(json.dumps({'status':status,'scope':'原题包本地mock；合成身份；超时由client transport模拟响应丢失，接收及查询为真实HTTP；重启为真实子进程重启','checks':results},ensure_ascii=False,indent=2));print(out.read_text());sys.exit(0 if status=='PASS' else 1)
