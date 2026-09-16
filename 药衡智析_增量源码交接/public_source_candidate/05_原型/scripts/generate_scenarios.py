from pathlib import Path
import json,time,urllib.request,os,subprocess,sys,argparse
if os.environ.get('PHARMA_PYTHON') and Path(os.environ['PHARMA_PYTHON']).resolve()!=Path(sys.executable).resolve():
    raise SystemExit(subprocess.call([os.environ['PHARMA_PYTHON']]+sys.argv))
ROOT=Path(__file__).resolve().parents[2]
BASE=os.getenv('PHARMA_BASE_URL','http://127.0.0.1:8765')
parser=argparse.ArgumentParser();parser.add_argument('--output',default=str(ROOT/'06_评测/incremental_20260916/scenario_reports.json'));parser.add_argument('--scenario',choices=['S1','S2','S3','Q2']);args=parser.parse_args()
scenarios=[('S1','银黄口服液','2026-05','monthly'),('S2','板蓝根颗粒','2026-05','special'),('S3','六味地黄胶囊','2026-03','monthly'),('Q2','银黄口服液','2026-06','quarterly')]
if args.scenario:scenarios=[s for s in scenarios if s[0]==args.scenario]
def request(path,data=None):
    req=urllib.request.Request(BASE+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=30) as r:return json.load(r)
manifest=[]
for name,product,month,kind in scenarios:
    payload={'factory':'中药一厂','product':product,'month':month,'analysis_type':kind,'basis':'unit'}
    j=request('/api/reports',payload)
    manifest.append({'scenario':name,'input':payload,'job_id':j['job_id']});print(name,j,flush=True)
output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
for item in manifest:
    previous=None
    for _ in range(240):
        job=request('/api/jobs/'+item['job_id'])
        if job['stage']!=previous:print(item['scenario'],job['stage'],job.get('error'),flush=True);previous=job['stage']
        if job['status'] in ('SUCCEEDED','DEGRADED','FAILED'):
            item['status']=job['status'];item['error']=job.get('error');item['artifacts']={k:job['result'].get(k) for k in ('docx','pdf','audit')};item['acceptance']=job['result'].get('acceptance');item['model']=job['result'].get('narrative',{}).get('model');item['model_live']=job['result'].get('narrative',{}).get('model_live');break
        time.sleep(2)
    else:item['status']='TIMEOUT'
    output.write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('FINAL',[(x['scenario'],x['status']) for x in manifest],flush=True)
