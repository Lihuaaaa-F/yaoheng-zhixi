from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];APP=ROOT/'05_原型';sys.path.insert(0,str(APP/'backend'))
from pharma.jobs import JobStore
from pharma.reports import verify_docx
from pharma.knowledge import Knowledge

# Baseline contract (docs/baseline.json): a flat {relative path -> sha256} map
# pinned at packaging time. Protected prefixes are originals that must never
# drift; every other file may legitimately change during development.
PROTECTED_PREFIXES=('00_赛题原始资料/','01_数据/00_原始/','02_知识库/00_原始/')

def load_baseline():
    path=ROOT/'docs/baseline.json'
    if not path.exists():return None
    raw=json.loads(path.read_text(encoding='utf-8'))
    if isinstance(raw,dict) and isinstance(raw.get('files'),dict):return raw['files']  # legacy nested form
    return {k:v['sha256'] if isinstance(v,dict) else v for k,v in raw.items()}        # flat form

def original_manifests(baseline):
    """Sources of truth for immutable originals: the packaged baseline plus, when
    the workspace sits inside an intact handoff package, its outer SHA256.json
    (team_internal/<path> pins the pre-merge originals)."""
    manifests={k:v for k,v in baseline.items() if k.startswith(PROTECTED_PREFIXES)}
    outer=ROOT.parent/'SHA256.json'
    if outer.exists():
        try:
            for rel,sha in json.loads(outer.read_text(encoding='utf-8')).items():
                if rel.startswith('team_internal/'):
                    working=rel[len('team_internal/'):]
                    if working.startswith(PROTECTED_PREFIXES):manifests.setdefault(working,sha)
        except (ValueError,OSError):pass
    return manifests

def verify_originals(baseline):
    protected=original_manifests(baseline)
    changed=[k for k,expected in protected.items() if not (ROOT/k).exists() or hashlib.sha256((ROOT/k).read_bytes()).hexdigest()!=expected]
    missing_keys=[k for k in baseline if not (ROOT/k).exists() and not k.startswith('05_原型/frontend/dist')]
    return protected,changed,missing_keys

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output-dir',default=None,help='本次运行证据目录；默认 06_评测/verify_<timestamp>')
    args=parser.parse_args()
    out=Path(args.output_dir) if args.output_dir else ROOT/'06_评测'/('verify_'+time.strftime('%Y%m%d_%H%M%S'))
    out.mkdir(parents=True,exist_ok=True)
    status={'PROJECT_ROOT':str(ROOT),'python':sys.executable,'ENV_REUSE':'PASS','CORE_CALC':'NOT_RUN','DATA_INTEGRITY':'NOT_RUN','BASELINE_CONTRACT':'NOT_RUN','TEMPLATE_BINDINGS':'NOT_RUN','RAG_HYBRID_REAL':'NOT_RUN','LLM_LIVE':'NOT_RUN','DOCX_EXPORT':'NOT_RUN','PDF_EXPORT':'NOT_RUN','RPA_PROVIDED_MOCK':'NOT_RUN','RECOVERY':'NOT_RUN','E2E':'NOT_RUN','DOCKER_RUNTIME':'NOT_IN_SCOPE','HUMAN_SCORE':'PENDING','COMPETITION_READY':'PARTIAL'}
    env={**os.environ,'PYTHONPATH':str(APP/'backend'),'ANONYMIZED_TELEMETRY':'False','OTEL_SDK_DISABLED':'true'}
    if os.name=='nt':env['TMPDIR']=env.get('TEMP','\tmp')
    else:env.setdefault('TMPDIR','/tmp')
    r=subprocess.run([sys.executable,'-m','pytest','-s','-q',str(APP/'tests')],capture_output=True,text=True,env=env,timeout=600)
    (out/'combined_tests.log').write_text(r.stdout+r.stderr,encoding='utf-8')
    status['CORE_CALC']='PASS' if r.returncode==0 else 'FAIL';status['RECOVERY']=status['CORE_CALC']

    baseline=load_baseline()
    if baseline is None:
        status['DATA_INTEGRITY']='FAIL';status['BASELINE_CONTRACT']='MISSING_BASELINE'
    else:
        protected,changed,missing=verify_originals(baseline)
        # A vacuous protection set is a broken contract, not a pass.
        status['DATA_INTEGRITY']='PASS' if protected and not changed else 'FAIL'
        status['BASELINE_CONTRACT']='PASS' if not missing else 'FAIL'
        status['protected_file_count']=len(protected);status['protected_changed']=changed[:20]
        status['baseline_missing_paths']=[m for m in missing if not m.startswith(PROTECTED_PREFIXES)][:20]
        if not protected:status['data_integrity_reason']='没有任何原件被钉入保护清单'

    # Report checks read this runtime's own jobs; a fresh machine starts empty
    # and reports NOT_RUN instead of crashing on foreign job ids.
    checks=[];store=JobStore()
    manifest=ROOT/'06_评测/incremental_20260916/scenario_reports.json'
    if manifest.exists():
        for entry in json.loads(manifest.read_text(encoding='utf-8')):
            try:j=store.get(entry['job_id'])
            except KeyError:
                checks.append({'scenario':entry.get('scenario'),'job_id':entry['job_id'],'status':'NOT_IN_THIS_RUNTIME','note':'历史job不在当前runtime数据库；重跑generate_scenarios.py生成新证据'})
                continue
            result=j['result'];docx=result.get('docx',{});pdf=result.get('pdf',{});n=result.get('narrative',{})
            item={'scenario':entry['scenario'],'job_id':j['id'],'status':j['status'],'narrative':n.get('status'),'model_live':n.get('model_live'),'model_identity':n.get('model_identity',{}).get('status'),'required_explanation_sections':n.get('required_explanation_sections'),'generation_mode':n.get('generation_mode'),'cache_hit':n.get('cache_hit'),'generated_at':n.get('generated_at'),'docx':docx.get('status'),'pdf':pdf.get('status')}
            if docx.get('artifact_id'):
                try:item['verification']=verify_docx(store.artifact_path(docx['artifact_id']),result['snapshot'])
                except Exception as ex:item['verification']={'status':'FAIL','reason':type(ex).__name__}
                checks.append(item)
        present=[x for x in checks if x.get('status')!='NOT_IN_THIS_RUNTIME']
        if len(present)==4:
            status['DOCX_EXPORT']='PASS' if all(x['docx']=='PASS' and x.get('verification',{}).get('status')=='PASS' for x in present) else 'FAIL'
            status['TEMPLATE_BINDINGS']=status['DOCX_EXPORT']
            status['PDF_EXPORT']='PASS' if all(x['pdf']=='PASS' for x in present) else 'FAIL'
            status['LLM_LIVE']='PASS' if all(x['narrative']=='PASS' and x['model_live'] and x.get('model_identity')=='VERIFIED' for x in present) else 'PARTIAL'
        elif present:
            status['DOCX_EXPORT']='PARTIAL'
    retrieval=out/'retrieval_results.json'
    if not retrieval.exists():retrieval=ROOT/'06_评测/retrieval_results.json'
    if retrieval.exists():status['RAG_HYBRID_REAL']=Knowledge().status().get('status','NOT_RUN')
    for file,key in [('browser_results.json','E2E'),('browser_results.json','RPA_PROVIDED_MOCK')]:
        for base_dir in (out,ROOT/'06_评测/incremental_20260916'):
            p=base_dir/file
            if p.exists():
                b=json.loads(p.read_text(encoding='utf-8'));status[key]=b.get('status','NOT_RUN')
    required=['ENV_REUSE','CORE_CALC','DATA_INTEGRITY','BASELINE_CONTRACT','TEMPLATE_BINDINGS','RAG_HYBRID_REAL','LLM_LIVE','DOCX_EXPORT','PDF_EXPORT','RPA_PROVIDED_MOCK','RECOVERY','E2E']
    status['FINAL_STATUS']='PASS' if all(status.get(k)=='PASS' for k in required) else 'PARTIAL'
    status['PHARMA_PYTHON_NOTE']='所有入口统一经 scripts/pharma_python.sh 或当前解释器解析'
    result={'at':time.strftime('%Y-%m-%dT%H:%M:%S%z'),'status':status,'tests_exit_code':r.returncode,'reports':checks,'limits':['LLM_LIVE需真实凭据+响应身份核验+必要解释覆盖','HUMAN_SCORE只能由真人审核录入','历史job不在当前runtime时按NOT_IN_THIS_RUNTIME记录，不冒充新证据']}
    (out/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
