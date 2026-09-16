from pharma.metrics import analyze, benchmark
from pharma.reports import render_docx, build_bindings
from docx import Document

def test_reader_report_has_no_internal_objects(tmp_path):
    s=analyze('中药一厂','板蓝根颗粒','2026-05')
    p=tmp_path/'report.docx'
    render_docx(s,{'status':'DEGRADED','model_live':False,'findings':[{'claim_type':'numeric_fact','rendered_text':'本期成本需核查。','metric_refs':['unit_cost'],'suggestion':''}]},{'evidence':[]},p,benchmark(s['product'],s['month']))
    d=Document(p);t='\n'.join(x.text for x in d.paragraphs)
    assert 'metric_refs' not in t
    assert '右键' not in t
    assert 'SHA256' not in t
    assert '基础分析' in t
    assert len(d.inline_shapes)>=4

def test_yoy_elements_are_bound():
    v=build_bindings(analyze('中药一厂','板蓝根颗粒','2026-05'),{})
    assert [v.get(k) for k in ('去年材料成本','去年人工成本','去年制造费用')]==['4.42','1.04','1.64']

def test_file_success_is_not_report_acceptance():
    from pharma.reports import assess_report
    r=assess_report({'docx':{'status':'PASS'},'pdf':{'status':'PASS'},'narrative':{'status':'DEGRADED','model_live':False},'evidence':{'status':'PASS'}})
    assert r['overall']!='PASS'
    assert r['model_participation']['status']=='FAIL'
    assert r['visual_quality']['status']=='PENDING'
