"""Current-commit HTTP acceptance. Private scenarios are an external opt-in JSON.
Receipts contain verdicts/identifiers, never source business data or full prose.
"""
from pathlib import Path
import argparse,json,os,sys,time,urllib.request
APP=Path(__file__).resolve().parents[1];ROOT=APP.parent
sys.path.insert(0,str(APP/'backend'))
from pharma.revision import revision_record

def main():
 p=argparse.ArgumentParser();p.add_argument('--run-id',required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--private-scenarios',type=Path);p.add_argument('--base-url',default='http://127.0.0.1:8765');a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
 revision=revision_record(ROOT)
 def call(path,data=None):
  req=urllib.request.Request(a.base_url+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req,timeout=180) as response:return json.load(response)
 scenarios=[{'id':i,'context_id':c,'product':'DEMO-01','month':'2026-06','analysis_type':'monthly'} for i,c in [('mechanical','mechanical_demo:synthetic-mechanical'),('chemical','chemical_demo:synthetic-chemical'),('pharma_synthetic','pharmaceutical:synthetic-pharma')]]
 if a.private_scenarios:scenarios+=json.loads(a.private_scenarios.read_text())
 result=[]
 for row in scenarios:
  data={k:v for k,v in row.items() if k!='id'};data['run_id']=a.run_id
  job=call('/api/reports',data);result.append({'id':row['id'],'job_id':job['job_id']});print('queued',row['id'],flush=True)
 manifest={'run_id':a.run_id,**revision,'required_scenarios':[x['id'] for x in result],'scenarios':result,'receipts':{},'human_review':'PENDING','privacy':'Local only: private scenario products and prose are excluded'}
 path=a.output_dir/'manifest.json';path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 narrative=[];retrieval=[];rpa=[]
 for row in result:
  for _ in range(480):
   job=call('/api/jobs/'+row['job_id'])
   if job['status'] in ('SUCCEEDED','DEGRADED','FAILED'):break
   time.sleep(1)
  body=job['result'];n=body.get('narrative',{});ev=body.get('evidence',{})
  row.update(status=job['status'],docx=body.get('docx',{}).get('status'),pdf=body.get('pdf',{}).get('status'),error=job.get('error'))
  narrative.append({'id':row['id'],'status':n.get('status','NOT_RUN'),'generation_mode':n.get('generation_mode'),'model_live':n.get('model_live'),'identity':n.get('model_identity'),'usage':n.get('usage'),'alert_coverage':n.get('alert_coverage'),'failures':n.get('failure_reasons',[])})
  retrieval.append({'id':row['id'],'status':ev.get('status'),'mode':ev.get('mode'),'framework':ev.get('framework'),'recall_status':ev.get('recall_status'),'count':len(ev.get('evidence',[]))})
  # Explicit integration test confirmation: localhost simulator only, never real WeChat.
  if body.get('snapshot'):
   f=next((x for x in n.get('findings',[]) if x.get('suggestion') and x.get('verification_target')),None)
   if f:
    payload={'snapshot_id':body['snapshot']['snapshot_id'],'finding':'合成验收：'+f.get('rendered_text','核对合成记录')[:1000],'suggestion':f['suggestion'],'assignee':{'name':'合成验收责任人','department':f.get('department') or '成本管理'},'priority':f.get('priority','medium'),**{k:f[k] for k in ('verification_target','expected_evidence','responsible_role','deadline_basis')}}
    action=call('/api/actions',payload);confirmed=call('/api/actions/'+action['id']+'/confirm',{'payload_hash':action['payload_hash']})
    for _ in range(30):
     action=call('/api/actions/'+action['id'])
     if action['status'] not in ('QUEUED','SENDING'):break
     time.sleep(1)
    again=call('/api/actions/'+action['id']+'/confirm',{'payload_hash':action['payload_hash']})
    rpa.append({'id':row['id'],'status':'PASS' if action['delivery']['notification']=='SIMULATED_SENT' and again['id']==action['id'] else 'FAIL','action_id':action['id'],'notification':action['delivery']['notification'],'human_acknowledgement':'NOT_ENTERED'})
  print(row['id'],row['status'],row['docx'],row['pdf'],n.get('status'),flush=True)
  path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
 receipts={'model_live':{'status':'PASS' if len(narrative)==len(result) and all(x['status']=='PASS' and x['model_live'] and (x.get('identity') or {}).get('status')=='VERIFIED' for x in narrative) else 'FAIL','scenarios':narrative},'retrieval':{'status':'PASS' if all(x['status']=='PASS' and x['mode']=='hybrid' for x in retrieval) else 'FAIL','scenarios':retrieval},'rpa':{'status':'PASS' if len(rpa)==len(result) and all(x['status']=='PASS' for x in rpa) else 'FAIL','scenarios':rpa}}
 for name,data in receipts.items():
  filename=name+'.json';(a.output_dir/filename).write_text(json.dumps({'run_id':a.run_id,**revision,**data},ensure_ascii=False,indent=2));manifest['receipts'][name]=filename
 path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('manifest',path)
if __name__=='__main__':main()
