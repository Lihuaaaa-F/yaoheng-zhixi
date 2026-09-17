"""Current-run verifier. 0=automatic dimensions pass, 1=failed, 2=incomplete.
Human reviews remain separate and can never be inferred from automatic tests.
"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[2];APP=ROOT/'05_原型'
sys.path.insert(0,str(APP/'backend'))
AUTOMATIC=('environment','regression','scenarios','retrieval','rpa','browser','model_live')

def check_receipt(path,run_id,commit):
    if not path or not Path(path).is_file():return {'status':'NOT_RUN','reason':'No current receipt'}
    try:r=json.loads(Path(path).read_text())
    except (ValueError,OSError):return {'status':'FAIL','reason':'Invalid receipt'}
    if r.get('run_id')!=run_id or r.get('commit')!=commit:return {'status':'STALE','reason':'Receipt is not bound to this run/commit'}
    return r

def documentation_path(path):
    path="/"+path.lstrip("/")
    return path.endswith(".md") or "/docs/validation/" in path or path.endswith("/docs/current_run.json")

def documentation_only_since(repo, tested_commit, current_commit):
    """Permit documentation-only descendants; never relabel an old model receipt.

    All receipts and jobs stay bound to the actual tested commit. Code, pack,
    prompt, dependency or configuration changes always require a new run.
    """
    if tested_commit == current_commit:
        return True
    if not tested_commit or subprocess.run(['git', 'merge-base', '--is-ancestor', tested_commit, current_commit], cwd=repo, capture_output=True).returncode:
        return False
    paths = subprocess.check_output(['git', 'diff', '--name-only', '-z', tested_commit, current_commit], cwd=repo, text=True).split('\0')
    return all(documentation_path(path) for path in paths if path)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',required=True,help='Current run manifest with run_id, commit, receipts and scenario job IDs')
    p.add_argument('--output-dir')
    args=p.parse_args();manifest_path=Path(args.manifest).resolve();m=json.loads(manifest_path.read_text())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    dirty=subprocess.check_output(['git','diff','HEAD','--name-only','-z'],cwd=ROOT,text=True).split('\0')
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=ROOT,text=True).split('\0')
    if any(not documentation_path(path) for path in dirty+untracked if path):p.error('uncommitted code/configuration: commit before current-run verification')
    tested_commit=m.get('commit')
    if not documentation_only_since(ROOT,tested_commit,commit) or not m.get('run_id'):p.error('manifest requires current code commit (documentation-only descendants allowed) and run_id')
    out=Path(args.output_dir) if args.output_dir else ROOT/'06_评测'/m['run_id'];out.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'PYTHONPATH':str(APP/'backend'),'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1','TMPDIR':'/tmp' if os.name!='nt' else os.environ.get('TEMP','.'),'OTEL_SDK_DISABLED':'true','ANONYMIZED_TELEMETRY':'False'}
    dimensions={k:{'status':'NOT_RUN'} for k in AUTOMATIC}
    checks=[('environment',[sys.executable,str(APP/'scripts/check_environment.py'),'--strict']),('regression',[sys.executable,'-m','pytest','-q',str(APP/'tests')])]
    for key,cmd in checks:
        try:
            r=subprocess.run(cmd,cwd=ROOT,env=env,capture_output=True,text=True,timeout=600)
            (out/(key+'.log')).write_text(r.stdout+r.stderr)
            dimensions[key]={'status':'PASS' if r.returncode==0 else 'FAIL','exit_code':r.returncode}
        except subprocess.TimeoutExpired:dimensions[key]={'status':'FAIL','reason':'Timeout'}
    from pharma.jobs import JobStore
    from pharma.reports import verify_docx
    store=JobStore();scenario_checks=[]
    for scenario in m.get('scenarios',[]):
        item={'id':scenario['id'],'status':'NOT_RUN'}
        try:
            job=store.get(scenario['job_id']);result=job['result']
            if job['input'].get('run_id')!=m['run_id'] or job['input'].get('commit')!=tested_commit:raise ValueError('SCENARIO_RUN_BINDING_MISMATCH')
            for fmt in ('docx','pdf'):store.artifact_path(result[fmt]['artifact_id'])
            check=verify_docx(store.artifact_path(result['docx']['artifact_id']),result['snapshot'],narrative=result.get('narrative'))
            item={'id':scenario['id'],'status':check['status'],'job_id':job['id'],'generation_mode':result.get('narrative',{}).get('generation_mode'),'human_review':'PENDING'}
        except (ValueError,KeyError,OSError) as exc:item={'id':scenario['id'],'status':'FAIL','reason':str(exc)}
        scenario_checks.append(item)
    expected=set(m.get('required_scenarios',[]));actual={x['id'] for x in scenario_checks}
    if expected and actual==expected:
        dimensions['scenarios']={'status':'PASS' if all(x['status']=='PASS' for x in scenario_checks) else 'FAIL'}
    for key in ('retrieval','rpa','browser','model_live'):
        ref=m.get('receipts',{}).get(key)
        dimensions[key]=check_receipt(manifest_path.parent/ref if ref else None,m['run_id'],tested_commit)
    failed=any(x.get('status')=='FAIL' for x in dimensions.values())
    complete=all(x.get('status')=='PASS' for x in dimensions.values())
    result={'run_id':m['run_id'],'commit':commit,'tested_code_commit':tested_commit,'dimensions':dimensions,'scenarios':scenario_checks,'human_review':'PENDING','competition_ready':False,'status':'FAIL' if failed else 'PASS' if complete else 'INCOMPLETE'}
    (out/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if failed else 0 if complete else 2
if __name__=='__main__':raise SystemExit(main())
