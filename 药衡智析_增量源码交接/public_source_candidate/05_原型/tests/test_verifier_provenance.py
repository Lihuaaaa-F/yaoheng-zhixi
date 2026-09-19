import importlib.util
from pathlib import Path
import subprocess

spec=importlib.util.spec_from_file_location('verify_run',Path(__file__).parents[1]/'scripts/verify.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def test_documentation_descendant_does_not_allow_code_or_pack_changes(tmp_path):
    def git(*args):return subprocess.check_output(['git',*args],cwd=tmp_path,text=True).strip()
    git('init','-q');git('config','user.name','Synthetic test');git('config','user.email','test@example.invalid')
    (tmp_path/'app.py').write_text('version=1\n');git('add','app.py');git('commit','-qm','code');base=git('rev-parse','HEAD')
    (tmp_path/'README.md').write_text('Evidence from the tested commit.');git('add','README.md');git('commit','-qm','docs');doc=git('rev-parse','HEAD')
    assert module.documentation_only_since(tmp_path,base,doc)
    (tmp_path/'app.py').write_text('version=2\n');git('add','app.py');git('commit','-qm','code changed')
    assert not module.documentation_only_since(tmp_path,base,git('rev-parse','HEAD'))
    assert not module.documentation_only_since(tmp_path,git('rev-parse','HEAD'),base)

def test_receipts_remain_bound_to_executed_commit(tmp_path):
    import json
    path=tmp_path/'receipt.json';path.write_text(json.dumps({'run_id':'new','commit':'executed','status':'PASS'}))
    assert module.check_receipt(path,'new','executed')['status']=='PASS'
    assert module.check_receipt(path,'old','executed')['status']=='STALE'
    assert module.check_receipt(path,'new','documentation-descendant')['status']=='STALE'

def test_scenario_receipt_cannot_mix_jobs_or_artifact_bytes(tmp_path):
    import json
    manifest={'run_id':'run','attempt_id':'attempt','commit':'code','scenarios':[{'id':'S1','job_id':'job','snapshot_id':'snap','artifacts':{'pdf':{'sha256':'hash'}}}]}
    row={**manifest['scenarios'][0],'status':'PASS'}
    path=tmp_path/'receipt.json'
    data={**manifest,'status':'PASS','scenarios':[row]};path.write_text(json.dumps(data))
    assert module.check_receipt(path,'run','code',manifest)['status']=='PASS'
    for key,value in [('job_id','other'),('snapshot_id','other'),('artifacts',{'pdf':{'sha256':'changed'}})]:
        path.write_text(json.dumps({**data,'scenarios':[{**row,key:value}]}))
        assert module.check_receipt(path,'run','code',manifest)['status']=='FAIL'
    path.write_text(json.dumps({**data,'attempt_id':'different'}))
    assert module.check_receipt(path,'run','code',manifest)['status']=='FAIL'
