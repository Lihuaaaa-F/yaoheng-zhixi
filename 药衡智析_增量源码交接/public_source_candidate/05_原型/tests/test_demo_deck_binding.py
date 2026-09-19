"""Presentation inputs must remain bound to the scenario that produced them."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('build_demo_deck',Path(__file__).parents[1]/'scripts/build_demo_deck.py')
deck=importlib.util.module_from_spec(spec);spec.loader.exec_module(deck)


def fixture_run(tmp_path):
    reports=tmp_path/'reports';scene=reports/'S1';scene.mkdir(parents=True)
    report=scene/'report.pdf';report.write_bytes(b'bound artifact')
    (scene/'snapshot.json').write_text(json.dumps({'snapshot_id':'snap','product':'synthetic','metrics':{}}))
    manifest={'run_id':'new-run','attempt_id':'attempt','scenarios':[{'id':'S1','job_id':'job','snapshot_id':'snap',
        'attempt_id':'attempt','artifacts':{'pdf':{'sha256':sha256(report.read_bytes()).hexdigest()}}}],
        'receipts':{'rpa':'rpa.json'}}
    receipt={'run_id':'new-run','attempt_id':'attempt','scenarios':[{'id':'S1','job_id':'job','snapshot_id':'snap','attempt_id':'attempt','status':'PASS','notification':'SIMULATED_SENT'}]}
    path=tmp_path/'manifest.json';path.write_text(json.dumps(manifest))
    (tmp_path/'rpa.json').write_text(json.dumps(receipt))
    return path,reports,manifest,receipt


def test_loads_only_bound_report_and_keeps_unfinished_scenarios_visible(tmp_path):
    path,reports,_,_=fixture_run(tmp_path)
    manifest,items=deck.load_run(path,reports)
    assert items['S1']['snapshot']['snapshot_id']=='snap'
    slides=deck.build_slides(manifest,items)
    assert len(slides)==10 and 'S2' in slides[3]['title']
    assert '待生成' in slides[3]['title']
    assert any('1/3' in line for line in slides[6]['lines'])


def test_rejects_changed_report_even_if_directory_name_matches(tmp_path):
    path,reports,_,_=fixture_run(tmp_path)
    (reports/'S1'/'report.pdf').write_bytes(b'old different report')
    with pytest.raises(ValueError,match='REPORT_HASH_MISMATCH'):deck.load_run(path,reports)


def test_rejects_snapshot_from_another_job(tmp_path):
    path,reports,_,_=fixture_run(tmp_path)
    (reports/'S1'/'snapshot.json').write_text(json.dumps({'snapshot_id':'old-snap'}))
    with pytest.raises(ValueError,match='SNAPSHOT_BINDING_MISMATCH'):deck.load_run(path,reports)


@pytest.mark.parametrize('field,value,error',[('run_id','old-run','RECEIPT_RUN'),('attempt_id','old-attempt','RECEIPT_ATTEMPT'),('job_id','old-job','RECEIPT_SCENARIO')])
def test_rejects_receipt_from_other_run_attempt_or_job(tmp_path,field,value,error):
    path,reports,_,receipt=fixture_run(tmp_path)
    target=receipt['scenarios'][0] if field=='job_id' else receipt
    target[field]=value;(tmp_path/'rpa.json').write_text(json.dumps(receipt))
    with pytest.raises(ValueError,match=error):deck.load_run(path,reports)
