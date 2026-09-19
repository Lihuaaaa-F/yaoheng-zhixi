"""Bound HTTP acceptance; automatic confirmation is restricted to local simulators."""
from pathlib import Path
import argparse,hashlib,json,sys,time,urllib.request,uuid
APP=Path(__file__).resolve().parents[1];ROOT=APP.parent
sys.path.insert(0,str(APP/'backend'))
from pharma.revision import revision_record
from pharma.local_validation import require_loopback,require_simulation,local_opener

def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--private-scenarios',type=Path);p.add_argument('--base-url',default='http://127.0.0.1:8765');a=p.parse_args()
 base=require_loopback(a.base_url);opener=local_opener();revision=revision_record(ROOT)
 a.output_dir.mkdir(parents=True,exist_ok=True);path=a.output_dir/'manifest.json'
 if path.exists():p.error('Existing run manifest is immutable; use a new run/output directory')
 attempt_id=uuid.uuid4().hex
 def call(route,data=None,raw=False):
  req=urllib.request.Request(base+route,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
  with opener.open(req,timeout=180) as response:return response.read() if raw else json.load(response)
 require_simulation(call('/health'))
 scenarios=[{'id':i,'context_id':c,'product':'DEMO-01','month':'2026-06','analysis_type':'monthly'} for i,c in [('mechanical','mechanical_demo:synthetic-mechanical'),('chemical','chemical_demo:synthetic-chemical'),('pharma_synthetic','pharmaceutical:synthetic-pharma')]]
 if a.private_scenarios:scenarios+=json.loads(a.private_scenarios.read_text())
 if len({x['id'] for x in scenarios})!=len(scenarios):raise ValueError('DUPLICATE_SCENARIO')
 result=[]
 for row in scenarios:
  data={k:v for k,v in row.items() if k!='id'};data['run_id']=a.run_id
  job=call('/api/reports',data);result.append({'id':row['id'],'job_id':job['job_id'],'attempt_id':attempt_id});print('queued',row['id'],flush=True)
 manifest={'run_id':a.run_id,'attempt_id':attempt_id,**revision,'required_scenarios':[x['id'] for x in result],'scenarios':result,'receipts':{},'human_review':'PENDING','competition_ready':False}
 def save():path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 save();narrative=[];retrieval=[];rpa=[]
 for row in result:
  deadline=time.monotonic()+1800
  while True:
   job=call('/api/jobs/'+row['job_id'])
   if job['status'] in ('SUCCEEDED','DEGRADED','FAILED'):break
   if time.monotonic()>deadline:raise TimeoutError('REPORT_TIMEOUT:'+row['id'])
   time.sleep(1)
  if job['input'].get('run_id')!=a.run_id or job['input'].get('commit')!=revision['commit']:raise ValueError('JOB_REVISION_MISMATCH')
  body=job['result'];n=body.get('narrative',{});ev=body.get('evidence',{});artifacts={}
  for fmt in ('docx','pdf'):
   artifact=body.get(fmt,{})
   if artifact.get('status')=='PASS' and artifact.get('artifact_id'):
    blob=call('/api/artifacts/'+artifact['artifact_id'],raw=True);sha=hashlib.sha256(blob).hexdigest()
    if sha!=artifact['sha256']:raise ValueError('ARTIFACT_HASH_MISMATCH')
    artifacts[fmt]={'artifact_id':artifact['artifact_id'],'sha256':sha,'bytes':len(blob)}
  row.update(status=job['status'],docx=body.get('docx',{}).get('status'),pdf=body.get('pdf',{}).get('status'),error=job.get('error'),snapshot_id=body.get('snapshot',{}).get('snapshot_id'),artifacts=artifacts)
  binding={k:row[k] for k in ('id','job_id','attempt_id','snapshot_id','artifacts')}
  narrative.append({**binding,'status':n.get('status','NOT_RUN'),'generation_mode':n.get('generation_mode'),'model_live':n.get('model_live'),'identity':n.get('model_identity'),'usage':n.get('usage'),'alert_coverage':n.get('alert_coverage'),'failures':n.get('failure_reasons',[])})
  retrieval.append({**binding,'status':ev.get('status'),'mode':ev.get('mode'),'framework':ev.get('framework'),'recall_status':ev.get('recall_status'),'knowledge_version':ev.get('knowledge_version'),'count':len(ev.get('evidence',[]))})
  if body.get('snapshot'):
   f=next((x for x in n.get('findings',[]) if x.get('suggestion') and x.get('verification_target')),None)
   if f:
    require_simulation(call('/health'))
    payload={'snapshot_id':body['snapshot']['snapshot_id'],'finding':'本地模拟验收：'+f.get('rendered_text','核对记录')[:1000],'suggestion':f['suggestion'],'assignee':{'name':'模拟验收责任人','department':f.get('department') or '成本管理'},'priority':f.get('priority','medium'),**{k:f[k] for k in ('verification_target','expected_evidence','responsible_role','deadline_basis')}}
    action=call('/api/actions',payload);confirmed_hash=action['payload_hash'];call('/api/actions/'+action['id']+'/confirm',{'payload_hash':confirmed_hash})
    for _ in range(30):
     action=call('/api/actions/'+action['id'])
     if action['status'] not in ('QUEUED','SENDING'):break
     time.sleep(1)
    require_simulation(call('/health'))
    again=call('/api/actions/'+action['id']+'/confirm',{'payload_hash':confirmed_hash})
    rpa.append({**binding,'status':'PASS' if action['delivery']['notification']=='SIMULATED_SENT' and again['id']==action['id'] and action['payload_hash']==confirmed_hash else 'FAIL','action_id':action['id'],'confirmed_payload_hash':confirmed_hash,'receipt_sha256':hashlib.sha256(json.dumps(action.get('remote'),sort_keys=True,ensure_ascii=False).encode()).hexdigest(),'notification':action['delivery']['notification'],'human_acknowledgement':'NOT_ENTERED'})
  print(row['id'],row['status'],row['docx'],row['pdf'],n.get('status'),flush=True);save()
 receipts={'model_live':{'status':'PASS' if len(narrative)==len(result) and all(x['status']=='PASS' and x['model_live'] and (x.get('identity') or {}).get('status')=='VERIFIED' for x in narrative) else 'FAIL','scenarios':narrative},'retrieval':{'status':'PASS' if len(retrieval)==len(result) and all(x['status']=='PASS' and x['mode']=='hybrid' for x in retrieval) else 'FAIL','scenarios':retrieval},'rpa':{'status':'PASS' if len(rpa)==len(result) and all(x['status']=='PASS' for x in rpa) else 'FAIL','scenarios':rpa}}
 for name,data in receipts.items():
  filename=name+'.json';(a.output_dir/filename).write_text(json.dumps({'run_id':a.run_id,'attempt_id':attempt_id,**revision,**data},ensure_ascii=False,indent=2)+'\n');manifest['receipts'][name]=filename
 save();print('manifest',path)
if __name__=='__main__':main()
