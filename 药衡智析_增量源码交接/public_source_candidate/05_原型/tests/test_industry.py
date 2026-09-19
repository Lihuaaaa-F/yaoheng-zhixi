"""Public synthetic acceptance cases; golden arithmetic is written independently."""
from decimal import Decimal
import json
import pytest
from pharma.industry import (AnalysisContext, CostFact, QuantityFact, NormalizedDataset,
    aggregate, compare, convert_quantity, load_pack, resolve_context, analyze_reference,
    publish_snapshot, load_snapshot, generation_key, retrieve_reference)


def test_reference_golden_and_specialist_metrics():
    mechanical = analyze_reference('mechanical_demo:synthetic-mechanical', month='2026-06')
    assert Decimal(mechanical['metrics']['total_cost']['value']) == 3600
    assert Decimal(mechanical['metrics']['quantity']['value']) == 120
    assert Decimal(mechanical['metrics']['unit_cost']['value']) == 30
    assert Decimal(mechanical['metrics']['machine_hours_per_piece']['value']) == Decimal('0.5')
    chemical = analyze_reference('chemical_demo:synthetic-chemical', month='2026-06')
    assert Decimal(chemical['metrics']['total_cost']['value']) == 2400
    assert Decimal(chemical['metrics']['unit_cost']['value']) == 12
    assert Decimal(chemical['metrics']['energy_per_kg']['value']) == 3
    assert len(chemical['elements']) == 4
    quarter = analyze_reference('mechanical_demo:synthetic-mechanical', month='2026-06', analysis_type='quarterly')
    assert Decimal(quarter['metrics']['total_cost']['value']) == 9400
    assert Decimal(quarter['metrics']['quantity']['value']) == 320
    assert Decimal(quarter['metrics']['unit_cost']['value']) == Decimal('29.375')


def test_context_frozen_isolated_and_cache_inputs():
    a = resolve_context('mechanical_demo:synthetic-mechanical')
    b = resolve_context('chemical_demo:synthetic-chemical')
    with pytest.raises(Exception): a.enterprise_id = 'changed'
    keys = [generation_key(a, {}, **kw) for kw in ({}, {'prompt_version':'new'}, {'model':'new'}, {'retriever_version':'new'}, {'embedding_model':'new'})]
    assert len(set(keys)) == 5
    assert generation_key(a,{}) != generation_key(b,{})
    assert retrieve_reference(a, '成本', product='DEMO-01')
    assert all(x['enterprise_id'] == a.enterprise_id for x in retrieve_reference(a,'成本',product='DEMO-01'))
    assert retrieve_reference(a,'成本',product='NOT-APPLICABLE') == []
    assert resolve_context('mechanical_demo:synthetic-mechanical') == a


def test_finite_numbers_units_and_currency():
    for token in ('NaN','Infinity','-Infinity'):
        with pytest.raises(ValueError): fact(amount=token)
    assert convert_quantity(Decimal('1'), 't', 'kg') == 1000
    for source,target in [('件','kg'),('L','kg'),('盒','粒')]:
        with pytest.raises(ValueError,match='CONVERSION_EVIDENCE_REQUIRED'): convert_quantity(Decimal(1),source,target)
    with pytest.raises(ValueError,match='CURRENCY'): aggregate(dataset(costs=[fact(),fact(fact_id='2',currency='USD')]), ['2026-06'])


def fact(**kw):
    return CostFact(**dict(dict(fact_id='1', enterprise_id='e',factory_id='f',product_id='p',product_version='1',period='2026-06',cost_object='order-1',element_id='materials',amount='10',currency='CNY',quantity_unit='件',policy_version='1',scope='completed',source_row='synthetic:1',source_snapshot='s'),**kw))


def qty(**kw):
    return QuantityFact(**dict(dict(fact_id='q',enterprise_id='e',factory_id='f',product_id='p',product_version='1',period='2026-06',cost_object='order-1',quantity='2',unit='件',policy_version='1',scope='completed',source_row='synthetic:2',source_snapshot='s'),**kw))


def dataset(costs=None, quantities=None):
    return NormalizedDataset(costs=costs or [fact()], quantities=quantities or [qty()])


def test_quantity_not_duplicated_by_cost_join_or_repeated_export():
    result = aggregate(dataset([fact(), fact(fact_id='2',element_id='energy',amount='6')], [qty(),qty()]),['2026-06'])
    assert result['quantity'] == 2 and result['total_cost'] == 16 and result['unit_cost'] == 8
    with pytest.raises(ValueError,match='CONFLICTING_QUANTITY'): aggregate(dataset(quantities=[qty(),qty(fact_id='other',quantity='9')]),['2026-06'])
    with pytest.raises(ValueError,match='DETAIL_SUMMARY'): aggregate(dataset([fact(),fact(fact_id='sum',level='summary')]),['2026-06'])


def test_scope_policy_missing_month_wip_and_legal_comparisons():
    a=aggregate(dataset(),['2026-06'])
    b=aggregate(dataset([fact(period='2026-05')],[qty(period='2026-05')]),['2026-05'])
    assert compare(a,b,'mom')['rate'] == '0'
    budget=aggregate(dataset([fact(scenario='budget')],[qty(scenario='budget')]),['2026-06'],scenario='budget')
    assert compare(a,budget,'budget')['delta'] == '0'
    with pytest.raises(ValueError,match='INCOMPLETE_PERIOD'): aggregate(dataset(),['2026-04','2026-05','2026-06'])
    for changed,error in [({'scope':'wip'},'WIP'),({'policy_version':'other'},'POLICY'),({'product_version':'other'},'PRODUCT'),({'quantity_unit':'kg'},'UNIT')]:
        with pytest.raises(ValueError,match=error): aggregate(dataset([fact(),fact(fact_id='2',**changed)]),['2026-06'])


def test_pack_version_and_snapshot_publication(tmp_path):
    manifest=load_pack('mechanical_demo').model_dump()
    manifest['core_compatibility']='>=9,<10'
    with pytest.raises(ValueError,match='INCOMPATIBLE'): load_pack(manifest)
    first=publish_snapshot(dataset(),tmp_path)
    with pytest.raises(ValueError): publish_snapshot(dataset([fact(),fact(fact_id='2',currency='USD')]),tmp_path)
    assert load_snapshot(tmp_path)['snapshot_id'] == first['snapshot_id']


def test_empty_import_cannot_replace_active_snapshot(tmp_path):
    first=publish_snapshot(dataset(),tmp_path)
    with pytest.raises(ValueError,match='EMPTY_DATASET'):
        publish_snapshot(NormalizedDataset(costs=[],quantities=[]),tmp_path)
    assert load_snapshot(tmp_path)['snapshot_id']==first['snapshot_id']


def test_quarter_benchmark_uses_requested_factories_and_weighting():
    from pharma.industry import benchmark_reference
    snapshot, result=benchmark_reference('mechanical_demo:synthetic-mechanical','DEMO-01','2026-06','示范工厂B','示范工厂A','quarterly')
    assert result['analysis_type']=='quarterly'
    assert Decimal(result['summary'][0]['left'])==Decimal('58.75')
    assert Decimal(result['summary'][0]['right'])==Decimal('29.375')
    assert Decimal(result['summary'][0]['rate'])==100
    assert result['period']=={'start':'2026-04','end':'2026-06'}
    assert snapshot['benchmark_context']['direction'].startswith('示范工厂B−示范工厂A')


def test_concurrent_same_product_and_document_ids_are_isolated():
    from concurrent.futures import ThreadPoolExecutor
    def run(cid):
        result=analyze_reference(cid,month='2026-06')
        return result['context_hash'],result['metrics']['unit_cost']['value'],retrieve_reference(resolve_context(cid),'成本',product='DEMO-01')
    ids=['mechanical_demo:synthetic-mechanical','chemical_demo:synthetic-chemical']
    with ThreadPoolExecutor(max_workers=2) as pool:
        a,b=list(pool.map(run,ids))
    assert a[0]!=b[0] and a[1]=='30' and b[1]=='12'
    assert a[2] and b[2]
    assert {e['analysis_context']['industry_id'] for e in a[2]}=={'mechanical_demo'}
    assert {e['analysis_context']['industry_id'] for e in b[2]}=={'chemical_demo'}
    assert run(ids[0])[:2]==a[:2]


def test_csv_import_round_trip_and_failed_update(tmp_path):
    import csv
    from pharma.industry import import_csv
    cost=tmp_path/'cost.csv'; quantity=tmp_path/'quantity.csv'; out=tmp_path/'out'
    def write(path,item):
        data=item.model_dump(mode='json')
        with path.open('w',newline='') as h:
            writer=csv.DictWriter(h,fieldnames=data);writer.writeheader();writer.writerow(data)
    write(cost,fact());write(quantity,qty())
    first=import_csv(cost,quantity,out)
    assert load_snapshot(out)['dataset']['quantities'][0]['quantity']=='2'
    quantity.write_text(quantity.read_text().replace(',2,',',Infinity,'))
    with pytest.raises(ValueError):import_csv(cost,quantity,out)
    assert load_snapshot(out)['snapshot_id']==first['snapshot_id']


def test_zero_quantity_is_undefined_not_zero_cost_and_missing_budget_is_explicit():
    result=aggregate(dataset(quantities=[qty(quantity='0')]),['2026-06'])
    assert result['unit_cost'] is None and result['total_cost']==10
    a=analyze_reference('chemical_demo:synthetic-chemical',month='2026-01')
    assert a['metrics']['mom']['value'] is None and a['metrics']['mom']['reason']


def test_packaging_conversion_requires_product_bound_evidence():
    from pharma.industry import UnitConversion
    bridge=UnitConversion(source_unit='盒',target_unit='粒',factor='60',product_id='p',product_version='1',evidence_ref='synthetic-specification-v1')
    assert convert_quantity(Decimal(2),'盒','粒',conversion=bridge,product_id='p',product_version='1')==120
    with pytest.raises(ValueError,match='CONVERSION_SCOPE'):
        convert_quantity(Decimal(2),'盒','粒',conversion=bridge,product_id='other',product_version='1')
    with pytest.raises(ValueError):UnitConversion(source_unit='盒',target_unit='粒',factor='60',product_id='p',product_version='1',evidence_ref='')


def test_explicit_alignment_allows_unit_and_policy_bridges():
    from pharma.industry import ComparisonAlignment, PolicyBridge, UnitConversion
    a=aggregate(dataset([fact(amount='100',quantity_unit='kg')],[qty(quantity='100',unit='kg')]),['2026-06'])
    b=aggregate(dataset([fact(amount='80',quantity_unit='t',period='2026-05',policy_version='old')],[qty(quantity='0.1',unit='t',period='2026-05',policy_version='old')]),['2026-05'])
    bridge=PolicyBridge(enterprise_id='e',factory_id='f',product_id='p',product_version='1',periods=['2026-05'],scenario='actual',source_policy_version='old',target_policy_version='1',amount_adjustment='20',evidence_ref='approved-allocation-reconciliation')
    align=ComparisonAlignment(unit_conversion=UnitConversion(source_unit='t',target_unit='kg',factor='1000',product_id='p',product_version='1',evidence_ref='SI-mass'),policy_bridge=bridge)
    assert compare(a,b,'mom',alignments=align)['rate']=='0'
    with pytest.raises(ValueError,match='CONVERSION_FACTOR'):
        compare(a,b,'mom',alignments=align.model_copy(update={'unit_conversion':align.unit_conversion.model_copy(update={'factor':Decimal(1)})}))
    with pytest.raises(ValueError,match='BRIDGE_SCOPE'):
        compare(a,b,'mom',alignments=align.model_copy(update={'policy_bridge':bridge.model_copy(update={'periods':('2026-04',)})}))
    with pytest.raises(ValueError):PolicyBridge(**{**bridge.model_dump(),'evidence_ref':''})
    budget=aggregate(dataset([fact(amount='100',quantity_unit='t',scenario='budget')],[qty(quantity='0.1',unit='t',scenario='budget')]),['2026-06'],scenario='budget')
    assert compare(a,budget,'budget',alignments=ComparisonAlignment(unit_conversion=align.unit_conversion))['delta']=='0'


def test_blank_policy_and_mislabeled_parent_children_are_rejected():
    with pytest.raises(ValueError):fact(policy_version=' ')
    with pytest.raises(ValueError):fact(quantity_unit=' ')
    parent=fact(element_id='materials',level='summary')
    child=fact(fact_id='2',element_id='steel',parent_element_id='materials',level='summary')
    with pytest.raises(ValueError,match='HIERARCHY_DOUBLE_COUNT'):aggregate(dataset([parent,child]),['2026-06'])


def test_multiple_enterprises_same_pack_same_product_and_evidence_id(tmp_path,monkeypatch):
    import pharma.industry as module
    monkeypatch.setattr(module,'ENTERPRISE_REGISTRY',tmp_path/'registry.json')
    pack=load_pack('mechanical_demo'); original=module.PACKS/pack.id
    profile=json.loads((original/'enterprise.json').read_text())
    profile.update(id='another-mechanical',name='另一个合成企业',dataset_id='another-dataset')
    local=tmp_path/'enterprise';local.mkdir()
    (local/'enterprise.json').write_text(json.dumps(profile))
    facts=json.loads((original/'facts.json').read_text())
    for items in facts.values():
        for row in items:row['enterprise_id']=profile['id']
    (local/'facts.json').write_text(json.dumps(facts))
    knowledge=json.loads((original/'knowledge.json').read_text())
    for row in knowledge:row['enterprise_id']=profile['id']
    (local/'knowledge.json').write_text(json.dumps(knowledge))
    context_id=module.register_enterprise(pack.id,local/'enterprise.json')
    assert context_id=='mechanical_demo:another-mechanical'
    entries=module.context_catalog()['contexts']
    assert len([x for x in entries if x['industry_id']=='mechanical_demo'])==2
    a=resolve_context('mechanical_demo:synthetic-mechanical');b=resolve_context(context_id)
    assert a.context_hash!=b.context_hash
    assert module.knowledge_entry_for_context(b)==local/'knowledge.json'
    assert module.catalog(context_id)['products']==['DEMO-01']
    result=analyze_reference(context_id,month='2026-06')
    assert result['analysis_context']['enterprise_id']==profile['id']
    from pharma.knowledge import Knowledge
    evidence=Knowledge(source_dir=module.knowledge_entry_for_context(b).parent,context=b,vector_enabled=False).search('成本',product='DEMO-01',mode='bm25')['evidence']
    assert evidence and all(x['analysis_context']['enterprise_id']==profile['id'] for x in evidence)
    assert all(x['analysis_context']['enterprise_id']==a.enterprise_id for x in retrieve_reference(a,'成本',product='DEMO-01'))


def test_duplicate_summary_ids_cannot_double_count_and_unrelated_levels_can_mix():
    with pytest.raises(ValueError,match='DUPLICATE_SUMMARY'):
        aggregate(dataset([fact(level='summary'),fact(fact_id='copy',level='summary')]),['2026-06'])
    result=aggregate(dataset([fact(level='summary'),fact(fact_id='labor',element_id='labor',amount='4')]),['2026-06'])
    assert result['total_cost']==14


def test_enterprise_display_unit_cannot_override_fact_semantics():
    import pharma.industry as module
    pack=load_pack('mechanical_demo');profile=module._enterprise(pack)
    with pytest.raises(ValueError,match='ENTERPRISE_UNIT'):
        module._read_dataset(pack,{**profile,'quantity_unit':'kg'})
    with pytest.raises(ValueError,match='ENTERPRISE_CURRENCY'):
        module._read_dataset(pack,{**profile,'currency':'USD'})


def test_mixed_product_summary_and_work_order_grains_cannot_double_count():
    costs=[fact(amount='100'),fact(fact_id='order',amount='100',grain='work_order',cost_object='wo')]
    quantities=[qty(quantity='10'),qty(fact_id='qo',quantity='10',grain='work_order',cost_object='wo')]
    with pytest.raises(ValueError,match='GRAIN_CONFLICT'):aggregate(dataset(costs,quantities),['2026-06'])


def _mutated_reference(monkeypatch, pack_id, mutate):
    import pharma.industry as module
    pack=load_pack(pack_id);base=module._read_dataset(pack)
    raw=base.model_dump(mode='json');mutate(raw)
    changed=NormalizedDataset.model_validate(raw)
    original=module._read_dataset
    monkeypatch.setattr(module,'_read_dataset',lambda p,enterprise=None:changed if p.id==pack_id else original(p,enterprise))
    return lambda:analyze_reference(pack_id+':synthetic-'+('mechanical' if pack_id=='mechanical_demo' else 'chemical'),factory='示范工厂A',month='2026-06')


def _current_drivers(raw):
    return [x for x in raw['optional'] if x['factory_id']=='示范工厂A' and x['scenario']=='actual' and x['period']=='2026-06']


def test_driver_units_convert_minutes_and_mwh_without_changing_meaning(monkeypatch):
    def minutes(raw):
        row=_current_drivers(raw)[0];row.update(value='60',unit='分钟')
    run=_mutated_reference(monkeypatch,'mechanical_demo',minutes)
    assert Decimal(run()['metrics']['machine_hours_per_piece']['value'])==Decimal(1)/120
    monkeypatch.undo()
    def mwh(raw):
        row=_current_drivers(raw)[0];row.update(value='0.6',unit='MWh')
    run=_mutated_reference(monkeypatch,'chemical_demo',mwh)
    assert Decimal(run()['metrics']['energy_per_kg']['value'])==3


@pytest.mark.parametrize('change,error',[
    ({'unit':'元'},'OPTIONAL_UNIT'),({'scope':'wip'},'WIP'),
    ({'cost_object':'no-such-order'},'OPTIONAL_OBJECT'),({'grain':'batch'},'GRAIN')])
def test_invalid_optional_facts_reject_in_actual_analysis(monkeypatch,change,error):
    def mutate(raw):_current_drivers(raw)[0].update(change)
    run=_mutated_reference(monkeypatch,'mechanical_demo',mutate)
    with pytest.raises(ValueError,match=error):run()


def test_duplicate_driver_export_does_not_double_specialized_metric(monkeypatch):
    def duplicate(raw):raw['optional'].append(dict(_current_drivers(raw)[0]))
    run=_mutated_reference(monkeypatch,'mechanical_demo',duplicate)
    assert Decimal(run()['metrics']['machine_hours_per_piece']['value'])==Decimal('0.5')
    monkeypatch.undo()
    def conflict(raw):
        row=dict(_current_drivers(raw)[0]);row['value']='90';raw['optional'].append(row)
    run=_mutated_reference(monkeypatch,'mechanical_demo',conflict)
    with pytest.raises(ValueError,match='CONFLICTING_OPTIONAL'):run()


def test_optional_coverage_checks_every_production_object_not_just_month(monkeypatch):
    def add_uncovered_order(raw):
        for relation in ('costs','quantities'):
            selected=[x for x in raw[relation] if x['factory_id']=='示范工厂A' and x['scenario']=='actual' and x['period']=='2026-06']
            for item in selected:
                copy=dict(item);copy['fact_id']+=':other';copy['cost_object']='uncovered-order';raw[relation].append(copy)
    run=_mutated_reference(monkeypatch,'mechanical_demo',add_uncovered_order)
    result=run()['metrics']['machine_hours_per_piece']
    assert result['value'] is None and 'OBJECT_COVERAGE' in result['reason']


def test_strategy_requires_correct_output_dimension(monkeypatch):
    import pharma.industry as module
    run=_mutated_reference(monkeypatch,'mechanical_demo',lambda raw:None)
    original=module.aggregate
    def wrong_unit(*args,**kwargs):return {**original(*args,**kwargs),'quantity_unit':'kg'}
    monkeypatch.setattr(module,'aggregate',wrong_unit)
    with pytest.raises(ValueError,match='STRATEGY_OUTPUT_UNIT'):run()


def test_actual_analysis_does_not_bypass_comparison_contract(monkeypatch):
    def change_budget(raw):
        for relation in ('costs','quantities'):
            for x in raw[relation]:
                if x['scenario']=='budget':x['source_mode']='driver_rebuilt'
    run=_mutated_reference(monkeypatch,'mechanical_demo',change_budget)
    with pytest.raises(ValueError,match='SOURCE_MODE'):run()


def test_non_benchmark_comparisons_require_same_factory():
    current=aggregate(dataset(),['2026-06'])
    other=aggregate(dataset([fact(factory_id='another',period='2026-05')],[qty(factory_id='another',period='2026-05')]),['2026-05'])
    with pytest.raises(ValueError,match='FACTORY'):compare(current,other,'mom')


def test_cross_factory_reference_only_relaxes_factory_not_source_mode(monkeypatch):
    import pharma.industry as module
    def change_factory(raw):
        for rows in raw.values():
            for row in rows:
                if row['factory_id']=='示范工厂B':row['source_mode']='driver_rebuilt'
    _mutated_reference(monkeypatch,'mechanical_demo',change_factory)
    with pytest.raises(ValueError,match='SOURCE_MODE'):
        module.benchmark_reference('mechanical_demo:synthetic-mechanical','DEMO-01','2026-06','示范工厂A','示范工厂B')


def test_different_ids_cannot_repeat_same_driver_object_operation(monkeypatch):
    def repeat(raw):
        copy=dict(_current_drivers(raw)[0]);copy['fact_id']='another-export-id';raw['optional'].append(copy)
    run=_mutated_reference(monkeypatch,'mechanical_demo',repeat)
    with pytest.raises(ValueError,match='OPTIONAL_DUPLICATE_OBJECT_OPERATION'):run()


def test_report_template_is_frozen_when_analysis_snapshot_is_created(tmp_path,monkeypatch):
    import shutil
    import pharma.industry as module
    original=module.PACKS/'mechanical_demo'
    target=tmp_path/'packs'/'mechanical_demo'
    shutil.copytree(original,target)
    monkeypatch.setattr(module,'PACKS',target.parent)
    monkeypatch.setattr(module,'ENTERPRISE_REGISTRY',tmp_path/'registry.json')
    template_path=target/'template.json'
    before=json.loads(template_path.read_text())
    snapshot=analyze_reference('mechanical_demo:synthetic-mechanical',month='2026-06')
    assert snapshot['report_template']==before
    frozen_snapshot_id=snapshot['snapshot_id']
    after={**before,'sections':['改版标题']+before['sections'][1:]}
    template_path.write_text(json.dumps(after,ensure_ascii=False))
    assert snapshot['report_template']==before
    assert snapshot['snapshot_id']==frozen_snapshot_id
    newer=analyze_reference('mechanical_demo:synthetic-mechanical',month='2026-06')
    assert newer['report_template']==after
    assert newer['analysis_context']['template_version']!=snapshot['analysis_context']['template_version']
    assert newer['snapshot_id']!=snapshot['snapshot_id']


def test_template_drift_between_context_binding_and_snapshot_copy_is_rejected(tmp_path,monkeypatch):
    import shutil
    import pharma.industry as module
    target=tmp_path/'packs'/'mechanical_demo'
    shutil.copytree(module.PACKS/'mechanical_demo',target)
    monkeypatch.setattr(module,'PACKS',target.parent)
    monkeypatch.setattr(module,'ENTERPRISE_REGISTRY',tmp_path/'registry.json')
    original=module.resolve_context
    def drift(context_id):
        context=original(context_id)
        path=target/'template.json';value=json.loads(path.read_text())
        value['required_notice']='后来改版的合成声明'
        path.write_text(json.dumps(value,ensure_ascii=False))
        return context
    monkeypatch.setattr(module,'resolve_context',drift)
    with pytest.raises(ValueError,match='TEMPLATE_SNAPSHOT_CHANGED'):
        analyze_reference('mechanical_demo:synthetic-mechanical',month='2026-06')


@pytest.mark.parametrize('analysis_type', ['monthly','quarterly'])
@pytest.mark.parametrize('basis', ['unit','total'])
def test_benchmark_metric_evidence_recomputes_display_and_both_sources(analysis_type,basis):
    from pharma.industry import benchmark_reference
    snapshot, result=benchmark_reference('mechanical_demo:synthetic-mechanical','DEMO-01','2026-06','示范工厂A','示范工厂B',analysis_type,basis)
    for row in result['summary']+result['elements']:
        for field,ref in row['metric_refs'].items():
            metric=snapshot['metrics'][ref]
            value=Decimal(metric['numerator'])/Decimal(metric['denominator'])
            if field!='delta':value*=100
            assert value==Decimal(row[field])
            assert metric['basis']==('unit' if row['key']=='unit_cost' else 'total' if row['key']=='total_cost' else 'quantity' if row['key']=='quantity' else basis)
            assert metric['sources']['left']['cost_rows'] and metric['sources']['right']['cost_rows']
            assert metric['sources']['left']['quantity_rows'] and metric['sources']['right']['quantity_rows']
            assert metric['comparison_period']==result['period']
    if basis=='unit' and analysis_type=='monthly':
        material=next(x for x in result['elements'] if x['key']=='materials')
        rate=snapshot['metrics'][material['metric_refs']['rate']]
        assert (rate['numerator'],rate['denominator'],rate['value'])==('-15','30','-50.0')


@pytest.mark.parametrize('analysis_type', ['monthly','quarterly'])
def test_period_evidence_distinguishes_rate_and_contribution(analysis_type):
    snapshot=analyze_reference('mechanical_demo:synthetic-mechanical',month='2026-06',analysis_type=analysis_type)
    for comparison in ('mom','yoy','budget'):
        metric=snapshot['metrics'][comparison]
        assert metric['sources']['current']['quantity_rows']
        for element in snapshot['elements']:
            for basis,c in element['comparisons'][comparison].items():
                if c['rate'] is not None:
                    assert Decimal(c['numerator'])/Decimal(c['denominator'])*100==Decimal(c['rate'])
                if c['contribution'] is not None:
                    assert Decimal(c['contribution_numerator'])/Decimal(c['contribution_denominator'])*100==Decimal(c['contribution'])
        if metric['value'] is not None:
            assert metric['sources']['base']['cost_rows'] and metric['sources']['base']['quantity_rows']
            assert Decimal(metric['numerator'])/Decimal(metric['denominator'])*100==Decimal(metric['value'])


@pytest.mark.parametrize('missing', [False,True])
def test_comparison_zero_or_missing_element_preserves_undefined_evidence(monkeypatch,missing):
    import pharma.industry as module
    def mutate(raw):
        raw['costs']=[row for row in raw['costs'] if not (missing and row['factory_id']=='示范工厂B' and row['period']=='2026-06' and row['element_id']=='materials')]
        if not missing:
            for row in raw['costs']:
                if row['factory_id']=='示范工厂B' and row['period']=='2026-06' and row['element_id']=='materials':row['amount']='0'
    _mutated_reference(monkeypatch,'mechanical_demo',mutate)
    snapshot,result=module.benchmark_reference('mechanical_demo:synthetic-mechanical','DEMO-01','2026-06','示范工厂A','示范工厂B')
    material=next(row for row in result['elements'] if row['key']=='materials')
    metric=snapshot['metrics'][material['metric_refs']['rate']]
    assert metric['value'] is None and metric['reason']
    assert metric['denominator'] is None if missing else Decimal(metric['denominator'])==0
    assert metric['numerator'] is None if missing else Decimal(metric['numerator'])==15


@pytest.mark.parametrize('pack_id,company', [('mechanical_demo','synthetic-mechanical'),('chemical_demo','synthetic-chemical'),('pharmaceutical','synthetic-pharma')])
def test_multiple_products_preserve_isolated_costs_units_and_sources(monkeypatch,pack_id,company):
    import pharma.industry as module
    pack=load_pack(pack_id);ds=module._read_dataset(pack);profile=module._enterprise(pack,company)
    original_product=next(iter(profile['products']))
    raw=ds.model_dump(mode='json')
    for rows in raw.values():
        copies=[]
        for row in rows:
            if row['product_id']!=original_product:continue
            copy=dict(row);copy['product_id']='SECOND-SYNTHETIC';copy['fact_id']+='-second';copy['source_row']+='-second'
            if 'amount' in copy:copy['amount']=str(Decimal(copy['amount'])*2)
            copies.append(copy)
        rows.extend(copies)
    modified=NormalizedDataset.model_validate(raw)
    original_reader=module._read_dataset;original_enterprise=module._enterprise
    monkeypatch.setattr(module,'_read_dataset',lambda p,enterprise=None:modified if p.id==pack_id else original_reader(p,enterprise))
    monkeypatch.setattr(module,'_enterprise',lambda p,company=None:{**profile,'products':{**profile['products'],'SECOND-SYNTHETIC':profile['products'][original_product]}} if p.id==pack_id else original_enterprise(p,company))
    first=analyze_reference(pack_id+':'+company,product=original_product,month='2026-06')
    second=analyze_reference(pack_id+':'+company,product='SECOND-SYNTHETIC',month='2026-06')
    assert Decimal(second['metrics']['unit_cost']['value'])==2*Decimal(first['metrics']['unit_cost']['value'])
    assert first['metrics']['unit_cost']['unit']==second['metrics']['unit_cost']['unit']
    assert all(row.endswith('-second') for row in second['metrics']['unit_cost']['row_keys'])
    assert not any(row.endswith('-second') for row in first['metrics']['unit_cost']['row_keys'])
