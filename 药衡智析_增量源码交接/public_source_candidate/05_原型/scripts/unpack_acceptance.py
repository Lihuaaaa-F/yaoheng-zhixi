#!/usr/bin/env python3
"""Unzip a delivered archive and actually bootstrap/start/use its relocated source."""
import hashlib,json,os,subprocess,sys,tempfile,time,zipfile,socket
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[2]
archive=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'07_交付/可运行源码交接包/药衡智析_可运行源码交接包.zip'
out=ROOT/'07_交付/可运行源码交接包/unpack_acceptance.json'
work=Path(tempfile.mkdtemp(prefix='pharma-unpacked-',dir=None if os.name=='nt' else '/tmp'))
with zipfile.ZipFile(archive) as z:
 for n in z.namelist():
  if not (work/n).resolve().is_relative_to(work):raise ValueError('Unsafe member')
 z.extractall(work)
package=next(work.iterdir());manifest=json.loads((package/'SHA256.json').read_text())
checks=[]
def check(name,ok):
 checks.append({'name':name,'status':'PASS' if ok else 'FAIL'})
 if not ok:raise AssertionError(name)
check('every_archived_file_hash',all(hashlib.sha256((package/rel).read_bytes()).hexdigest()==sha for rel,sha in manifest.items()))
subprocess.run([sys.executable,str(package/'prepare_team_workspace.py')],check=True)
project=package/'public_source_candidate';log=work/'startup.log'
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
api_port,rpa_port=port(),port()
env={k:v for k,v in os.environ.items() if not (k.startswith('PHARMA_') or k in ('GLM_API_KEY','ZHIPU_API_KEY','RPA_BASE_URL'))}
env.update(PHARMA_PYTHON=sys.executable,PHARMA_EMBEDDING_DIR=str(ROOT/'05_原型/.runtime/models/bge-small-zh-v1.5'),PHARMA_API_PORT=str(api_port),PHARMA_RPA_PORT=str(rpa_port),TMPDIR=(os.environ.get('TEMP') if os.name=='nt' else '/tmp'))
status='FAIL';job=None
try:
 with log.open('w') as f:
  subprocess.run(['bash','05_原型/scripts/bootstrap.sh'],cwd=project,env=env,stdout=f,stderr=f,check=True,timeout=120)
  subprocess.run(['bash','05_原型/scripts/start.sh'],cwd=project,env=env,stdout=f,stderr=f,check=True,timeout=45)
 check('actual_relocated_bootstrap_start',True)
 with httpx.Client(base_url=f'http://127.0.0.1:{api_port}',timeout=20) as c:
  check('http_ui',c.get('/').status_code==200)
  check('worker_alive',c.get('/health').json()['worker']['alive'])
  body={'factory':'中药一厂','product':'板蓝根颗粒','month':'2026-05','analysis_type':'special','basis':'unit'}
  snapshot=c.post('/api/analyses',json=body).json();check('core_unit_cost',snapshot['metrics']['unit_cost']['value']=='7.47')
  check('comparison_is_bound',snapshot['elements'][0]['comparisons']['yoy']['unit']['contribution'].startswith('89.189'))
  search=c.post('/api/kb/search',json={'query':'板蓝根颗粒 提取收率 单耗 工艺参数','product':'板蓝根颗粒','month':'2026-05','factory':'中药一厂'}).json()
  check('actual_hybrid_retrieval',search['status']=='PASS' and bool(search['evidence']))
  response=c.post('/api/reports',json=body);response.raise_for_status();id=response.json()['job_id']
  for _ in range(180):
   job=c.get('/api/jobs/'+id).json()
   if job['status'] in ('SUCCEEDED','DEGRADED','FAILED'):break
   time.sleep(1)
  check('report_export_terminal',job['status']=='DEGRADED')
  check('missing_model_never_accepted',job['result']['acceptance']['model_participation']['status']=='FAIL' and job['result']['acceptance']['overall']!='PASS')
  for fmt in ('docx','pdf','audit'):
   record=job['result'][fmt];r=c.get('/api/artifacts/'+record['artifact_id']);r.raise_for_status()
   check('download_'+fmt,hashlib.sha256(r.content).hexdigest()==record['sha256'])
  check('updated_toc',job['result']['pdf']['toc_updated'])
 status='PASS'
except Exception as exc:checks.append({'failure':type(exc).__name__+': '+str(exc)[:200]})
finally:
 with log.open('a') as f:subprocess.run(['bash','05_原型/scripts/stop.sh'],cwd=project,env=env,stdout=f,stderr=f,timeout=20)
result={'status':status,'scope':'新临时目录解压后的真实bootstrap/API/worker/混合检索/报告生成/三附件下载；复用同机兼容解释器和经SHA核验的外置embedding，不宣称净系统安装','archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'archive':str(archive),'work_directory':str(work),'checks':checks,'reused_python':sys.executable,'model_runtime':'BLOCKED_NO_KEY','human_review':'PENDING','job_id':job.get('id') if job else None}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2))
(ROOT/'06_评测/incremental_20260916/unpack_acceptance.json').write_text(out.read_text())
(ROOT/'06_评测/incremental_20260916/unpack_startup.log').write_text(log.read_text())
print(json.dumps(result,ensure_ascii=False,indent=2));sys.exit(0 if status=='PASS' else 1)
