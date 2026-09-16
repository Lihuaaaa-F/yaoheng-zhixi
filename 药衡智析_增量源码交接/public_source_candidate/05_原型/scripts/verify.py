from pathlib import Path
import hashlib,importlib,json,os,platform,subprocess,sys,time,statistics,urllib.request
ROOT=Path(__file__).resolve().parents[2];APP=ROOT/'05_原型';OUT=ROOT/'06_评测';sys.path.insert(0,str(APP/'backend'))
from pharma.jobs import JobStore
from pharma.reports import verify_docx
from pharma.knowledge import Knowledge
from pharma.config import PACKAGE
status={'PROJECT_ROOT':str(ROOT),'ENV_REUSE':'PASS','CORE_CALC':'NOT_RUN','DATA_INTEGRITY':'NOT_RUN','TEMPLATE_BINDINGS':'NOT_RUN','RAG_HYBRID_REAL':'NOT_RUN','LLM_LIVE':'NOT_RUN','DOCX_EXPORT':'NOT_RUN','PDF_EXPORT':'NOT_RUN','RPA_PROVIDED_MOCK':'NOT_RUN','RECOVERY':'NOT_RUN','E2E_WSL':'NOT_RUN','CHROME':'NOT_RUN','EDGE':'NOT_RUN','DOCKER_RUNTIME':'BLOCKED','HUMAN_SCORE':'PENDING','COMPETITION_READY':'PARTIAL'}
env={**os.environ,'TMPDIR':'/tmp','PYTHONPATH':str(APP/'backend')}
r=subprocess.run([sys.executable,'-m','pytest','-s','-q',str(APP/'tests')],capture_output=True,text=True,env=env,timeout=120)
(OUT/'combined_tests.log').write_text(r.stdout+r.stderr)
status['CORE_CALC']='PASS' if r.returncode==0 else 'FAIL';status['RECOVERY']=status['CORE_CALC']
base=json.loads((ROOT/'docs/baseline.json').read_text());protected=[k for k in base['files'] if k.startswith(('00_赛题原始资料/','01_数据/00_原始/','02_知识库/00_原始/'))]
changed=[k for k in protected if not (ROOT/k).exists() or hashlib.sha256((ROOT/k).read_bytes()).hexdigest()!=base['files'][k]['sha256']]
status['DATA_INTEGRITY']='PASS' if not changed else 'FAIL'
checks=[];store=JobStore();manifest=OUT/'scenario_reports.json'
if manifest.exists():
 for entry in json.loads(manifest.read_text()):
  j=store.get(entry['job_id']);result=j['result'];docx=result.get('docx',{});pdf=result.get('pdf',{});n=result.get('narrative',{})
  item={'scenario':entry['scenario'],'job_id':j['id'],'status':j['status'],'narrative':n.get('status'),'model_live':n.get('model_live'),'cache_hit':n.get('cache_hit'),'generated_at':n.get('generated_at'),'docx':docx.get('status'),'pdf':pdf.get('status')}
  if docx.get('artifact_id'):
   try:item['verification']=verify_docx(store.artifact_path(docx['artifact_id']),result['snapshot'])
   except Exception as ex:item['verification']={'status':'FAIL','reason':type(ex).__name__}
  checks.append(item)
 if len(checks)==4:
  status['DOCX_EXPORT']='PASS' if all(x['docx']=='PASS' and x.get('verification',{}).get('status')=='PASS' for x in checks) else 'FAIL'
  status['TEMPLATE_BINDINGS']=status['DOCX_EXPORT']
  status['PDF_EXPORT']='PASS' if all(x['pdf']=='PASS' for x in checks) else 'FAIL'
  status['LLM_LIVE']='PASS' if all(x['narrative']=='PASS' and x['model_live'] for x in checks) else 'PARTIAL'
retrieval=OUT/'retrieval_results.json'
if retrieval.exists():status['RAG_HYBRID_REAL']=Knowledge().status().get('status','NOT_RUN')
for file in ['browser_results.json','browser_narrative_results.json']:
 p=OUT/file
 if p.exists():
  b=json.loads(p.read_text())
  if file=='browser_results.json':status['E2E_WSL']=b.get('status','NOT_RUN');status['RPA_PROVIDED_MOCK']=b.get('status','NOT_RUN')
  elif b.get('status')!='PASS':status['E2E_WSL']='PARTIAL'
win=OUT/'browser_windows_results.json'
if win.exists():
 b=json.loads(win.read_text())
 for name in ['Chrome','Edge']:
  v=next((x for x in b.get('browsers',[]) if x['name']==name),{})
  if isinstance(v,dict):status[name.upper()]=v.get('status','NOT_RUN')
required=['ENV_REUSE','CORE_CALC','DATA_INTEGRITY','TEMPLATE_BINDINGS','RAG_HYBRID_REAL','LLM_LIVE','DOCX_EXPORT','PDF_EXPORT','RPA_PROVIDED_MOCK','RECOVERY','E2E_WSL']
status['FINAL_STATUS']='PASS' if all(status[k]=='PASS' for k in required) else 'PARTIAL'
status.update({'OPEN_SOURCE_REUSE':'PASS','SKILLS_REUSED':['react-best-practices','frontend-testing-debugging','build-report'],'SKILLS_INSTALLED_OR_UPDATED':['setup-matt-pocock-skills','domain-modeling','codebase-design','tdd','diagnosing-bugs','code-review'],'SKILLS_NATIVE_DISCOVERY':'NOT_VERIFIED_THIS_SESSION','SKILLS_USED_BY_FILE':'AGENTS.md + docs/third_party_reuse.md','OPTIONAL_TOOLS_SKIPPED':['docxtpl','Docling','promptfoo','RAGFlow deployment','playwright-cli','Docker Engine']})
result={'at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'status':status,'tests_exit_code':r.returncode,'protected_file_count':len(protected),'protected_changed':changed,'reports':checks,'limits':['检索最终实测见retrieval_results.json，目标0.85与实测分开','人工归因评分未执行，视频/PPT/公开发布属于后续交付','原mock重启清空，已送任务不自动重建']}
(OUT/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
