"""Independent synthetic dashboard examples; never read or mutate contest bytes."""
from copy import deepcopy
from decimal import Decimal
import pytest

from pharma.dashboard import focus_analysis, product_month_grid


def snapshot(rates=('10', '-10')):
    elements=[]
    for i,rate in enumerate(rates):
        base=Decimal('100') if rate is not None else None
        current=base+Decimal(rate) if base is not None else Decimal('9')
        comparison={'base':str(base) if base is not None else None,'current':str(current),
                    'rate':rate, 'delta':rate, 'reason':'缺少基期' if base is None else None}
        elements.append({'key':f'e{i}','name':f'独立要素{i}','unit':str(current),'total':str(current*2),
                         'comparisons':{'mom':{'unit':comparison,'total':deepcopy(comparison)}}})
    return {'snapshot_id':'synthetic-snapshot','context_id':'synthetic:company','factory':'F',
            'product':'P','month':'2026-06','analysis_type':'monthly','basis':'unit',
            'period':{'start':'2026-06','end':'2026-06'},'elements':elements,
            'metrics':{'unit_cost':{'unit':'USD/item'},'total_cost':{'unit':'USD'}}}


def test_focus_strict_threshold_both_directions_and_multiple_elements():
    assert focus_analysis(snapshot())['items']==[]
    result=focus_analysis(snapshot(('10.0001','-10.0001',None)))
    assert len(result['items'])==4
    assert len(result['missing'])==2
    assert '110.0001' in result['items'][0]['text']
    assert Decimal(result['items'][0]['rate'])==Decimal('10.0001')
    assert all(item['missing_evidence'] for item in result['items'])
    assert result['model_status']=='DISABLED'


def test_zero_baseline_is_missing_never_an_alert():
    s=snapshot(('50',));s['elements'][0]['comparisons']['mom']['unit']['base']='0'
    result=focus_analysis(s)
    assert len(result['items'])==1 and len(result['missing'])==1


def test_model_queue_requires_explicit_configuration_and_reuses_failed_attempt():
    calls=[]
    def enqueue():
        calls.append(1);return {'id':'same-job','status':'QUEUED'}
    s=snapshot(('11',))
    assert focus_analysis(s,enqueue=enqueue)['model_status']=='DISABLED'
    assert focus_analysis(s,enqueue=enqueue,enabled=True)['model_status']=='NO_MODEL'
    assert not calls
    first=focus_analysis(s,enqueue=enqueue,enabled=True,model_available=True)
    assert first['job_id']=='same-job' and len(calls)==1
    for status in ('QUEUED','FAILED'):
        repeat=focus_analysis(s,enqueue=enqueue,enabled=True,model_available=True,
                              latest_job={'id':'same-job','status':status})
        assert repeat['job_id']=='same-job'
    assert len(calls)==1


def test_two_product_month_grid_keeps_precise_values_missing_months_and_units():
    calls=[]
    def analyze(cid,**kw):
        calls.append((cid,kw))
        if kw['month']=='2026-05' and kw['product']=='P2':raise ValueError('INCOMPLETE_PERIOD')
        s=snapshot(('11',))
        s['metrics']['unit_cost']['value']='1.23456789' if kw['product']=='P1' else '9.87654321'
        s['metrics']['total_cost']['value']='100'
        return s
    result=product_month_grid('synthetic:company','F','2026-06','unit',
        options={'products':['P1','P2'],'factories':['F'],'months':['2026-04','2026-06']},analyze=analyze)
    assert result['months']==['2026-01','2026-02','2026-03','2026-04','2026-05','2026-06']
    assert len(result['cells'])==12
    p1=next(c for c in result['cells'] if c['product']=='P1' and c['month']=='2026-06')
    assert p1['values']['all']['value']=='1.23456789'
    assert p1['values']['all']['unit']=='USD/item'
    absent=next(c for c in result['cells'] if c['product']=='P2' and c['month']=='2026-05')
    assert absent['status']=='MISSING' and absent['values']=={}
    assert all(c[1]['analysis_type']=='monthly' for c in calls)


def test_api_focus_is_opt_in_and_same_failed_snapshot_is_not_requeued(monkeypatch, tmp_path):
    from pharma import api
    from pharma.jobs import JobStore
    from pharma.narrative import ModelGateway
    from types import SimpleNamespace
    store=JobStore(tmp_path/'jobs.sqlite3')
    monkeypatch.setattr(api,'store',store)
    monkeypatch.setattr(api,'scoped_analysis',lambda req:snapshot(('11',)))
    monkeypatch.setattr('pharma.narrative.ModelGateway',lambda:SimpleNamespace(key='synthetic-only'))
    calls=[]
    def enqueue(req):
        calls.append(1)
        s=store.snapshot(snapshot(('11',)))
        return store.enqueue('report',{'snapshot_id':s['snapshot_id']},'focus-fixture'),s
    monkeypatch.setattr(api,'_enqueue_report',enqueue)
    monkeypatch.setenv('PHARMA_AUTO_EXPLAIN','false')
    req=api.AnalysisRequest(context_id='synthetic:company')
    assert api.analysis(req)['focus']['model_status']=='DISABLED'
    assert not calls
    monkeypatch.setenv('PHARMA_AUTO_EXPLAIN','true')
    first=api.analysis(req)['focus']
    assert first['model_status']=='QUEUED'
    assert api.analysis(req)['focus']['job_id']==first['job_id']
    store.update(first['job_id'],'FAILED',error='synthetic failure')
    assert api.analysis(req)['focus']['model_status']=='FAILED'
    assert len(calls)==1
