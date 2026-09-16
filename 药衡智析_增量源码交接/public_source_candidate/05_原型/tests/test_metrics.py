from decimal import Decimal as D
from pharma.metrics import analyze

def test_comparisons_bind_their_own_period_numerator_and_denominator():
    # Independent May source-row examples, not copied from the engine's output.
    golden = {
        '板蓝根颗粒': [('0.18','0.23','78.26'),('0.33','0.37','89.19'),('0.37','0.47','78.72')],
        '银黄口服液': [('0.22','0.31','70.97'),('0.46','0.50','92.00'),('0.50','0.61','81.97')],
        '六味地黄胶囊': [('0.35','0.45','77.78'),('0.67','0.71','94.37'),('0.79','0.99','79.80')],
    }
    for product, expected in golden.items():
        snapshot = analyze('中药一厂',product,'2026-05')
        material = snapshot['elements'][0]
        for label, period, (numerator, denominator, percent) in zip(
                ('mom','yoy','budget'), ('2026-04','2025-05','2026-05'), expected):
            comparison = material['comparisons'][label]['unit']
            assert D(comparison['numerator']) == D(numerator)
            assert D(comparison['denominator']) == D(denominator)
            assert D(comparison['contribution']).quantize(D('0.01')) == D(percent)
            assert comparison['comparison_period'] == [period]
            metric = snapshot['metrics'][f'materials_{label}_unit_contribution']
            assert metric['numerator'] == comparison['numerator']
            assert metric['denominator'] == comparison['denominator']
            assert metric['comparison_period'] == [period]

def test_quarter_weighting_against_independent_golden():
    result = analyze('中药一厂', '银黄口服液', '2026-06', 'quarterly')
    assert D(result['metrics']['total_cost']['value']) == D('1796180')
    assert D(result['metrics']['quantity']['value']) == D('163000')
    assert abs(D(result['metrics']['unit_cost']['value']) - D('11.01950920245398773006134969')) < D('0.000000001')

def test_benchmark_direction_uses_right_factory_denominator():
    from pharma.metrics import benchmark
    forward = benchmark('板蓝根颗粒','2026-05')
    reverse = benchmark('板蓝根颗粒','2026-05','中药一厂','中药二厂')
    assert D(forward['summary'][0]['delta']) == D('0.50')
    assert abs(D(forward['summary'][0]['rate'])-D('6.693440428380187')) < D('0.0000001')
    assert abs(D(reverse['summary'][0]['rate'])-D('-6.273525721455458')) < D('0.0000001')

def test_benchmark_structure_is_available_without_second_factory_material_details():
    from pharma.metrics import benchmark_analysis
    snapshot, result = benchmark_analysis('板蓝根颗粒','2026-05')
    assert [D(row['delta']) for row in result['elements']] == [D('0.20'),D('0.13'),D('0.17')]
    assert [D(row['contribution']) for row in result['elements']] == [D('40'),D('26'),D('34')]
    assert result['details']['left']['materials'] == []
    for row in result['elements']:
        assert D(row['denominator']) == D('0.50')
        metric = snapshot['metrics'][row['metric_refs']['contribution']]
        assert D(metric['value']) == D(row['contribution'])
        assert metric['unit'] == '%'
    reverse, _ = benchmark_analysis('板蓝根颗粒','2026-05','中药一厂','中药二厂')
    assert [D(row['contribution']) for row in reverse['benchmark_context']['elements']] == [D('40'),D('26'),D('34')]

def test_strict_alert_threshold_boundary():
    from pharma.metrics import threshold_alert
    assert [threshold_alert(value) for value in ('-10.01','-10','-9.99','9.99','10','10.01',None)] == [True,False,False,False,False,True,False]

def test_contribution_allows_negative_over_100_and_zero_denominator():
    from pharma.metrics import contribution
    assert contribution('-2','1') == '-200'
    assert contribution('3','1') == '300'
    assert contribution('2','0') is None

def test_missing_zero_base_and_explicit_month_join():
    from pharma.metrics import change
    assert change('10',None)['rate'] is None
    assert change('10','0')['rate'] is None
    result=analyze('中药一厂','银黄口服液','2026-01')
    assert result['metrics']['mom']['value'] is None
    assert result['metrics']['mom']['comparison_period']==['2025-12']
    quarter=analyze('中药一厂','银黄口服液','2026-03','quarterly')
    assert quarter['metrics']['mom']['value'] is None

def test_s1_budget_bridge_and_industry_conversion():
    result=analyze('中药一厂','银黄口服液','2026-05')
    assert result['metrics']['unit_cost']['value']=='11.21'
    assert abs(D(result['metrics']['mom']['value'])-D('2.8440366972477062'))<D('0.00000001')
    assert [e['unit_delta'] for e in result['elements']]==['0.22','0.03','0.06']
    assert result['industry']['converted_unit_cost']=='1.121'
    bridge=result['budget_bridge']
    assert D(bridge['quantity_effect'])+D(bridge['unit_cost_effect'])==D(bridge['total_delta'])
    assert all(t['month']<='2026-05' for t in result['trend'])
    assert all('6月价格' not in r for r in result['details']['market'])

def test_banlangen_material_driver_budget_bridge_and_available_yoy_are_registered():
    result = analyze('中药一厂','板蓝根颗粒','2026-05')
    assert [D(e['yoy_unit']) for e in result['elements']] == [D('4.42'),D('1.04'),D('1.64')]
    assert [D(e['yoy_rate']).quantize(D('0.01')) for e in result['elements']] == [D('7.47'),D('1.92'),D('1.22')]
    driver = result['materials_summary'][0]
    assert driver['name'] == '板蓝根'
    assert D(driver['previous']) == D('2.90')
    assert D(driver['current']) == D('3.05')
    assert D(driver['contribution']).quantize(D('0.01')) == D('83.33')
    assert D(driver['denominator']) == D('0.18')
    for field in ('current','previous','delta','contribution'):
        assert D(result['metrics'][driver['metric_refs'][field]]['value']) == D(driver[field])
    current_metric = result['metrics'][driver['metric_refs']['current']]
    assert D(current_metric['numerator']) == D('311100')
    assert D(current_metric['denominator']) == D('102000')
    assert D(result['budget_bridge']['quantity_effect']) == D('84000')
    assert D(result['budget_bridge']['unit_cost_effect']) == D('47940')
    assert D(result['budget_bridge']['total_delta']) == D('131940')
    assert D(result['metrics']['budget_quantity_effect']['value']) == D('84000')
    assert '题包折算' in result['labor_metrics']['definitions']['hourly_wage']
    assert [r['month'] for r in result['trend']] == ['2026-01','2026-02','2026-03','2026-04','2026-05']
    assert D(result['trend'][1]['unit_cost']) == D('7.25')

def test_missing_material_details_and_incomplete_quarter_remain_explicit():
    second = analyze('中药二厂','板蓝根颗粒','2026-05')
    assert second['materials_summary'] == []
    assert second['elements'][0]['comparisons']['budget']['unit']['contribution'] is None
    quarter = analyze('中药一厂','银黄口服液','2026-03','quarterly')
    assert all(row['previous'] is None and row['contribution'] is None and row['reason'] for row in quarter['materials_summary'])

def test_s2_and_s3_missing_detail_and_actual_total_alerts():
    second=analyze('中药二厂','板蓝根颗粒','2026-05')
    assert second['metrics']['budget']['value'] is None
    assert second['details']['available'] is False
    assert second['industry']['converted_unit_cost']=='0.3985'
    s3=analyze('中药一厂','六味地黄胶囊','2026-03')
    assert D(s3['metrics']['total_cost']['value'])==D('595700')
    assert s3['industry']['converted_unit_cost']==str(D('17.02')/60)
    assert not any(a['basis']=='unit' for a in s3['alerts'])
    assert any(a['basis']=='total' for a in s3['alerts'])

def test_quarter_requires_end_month():
    import pytest
    with pytest.raises(ValueError,match='QUARTER_END_MONTH_REQUIRED'):
        analyze('中药一厂','银黄口服液','2026-05','quarterly')

def test_all_scenarios_match_independent_fraction_golden():
    import json
    from pathlib import Path
    golden=json.loads((Path(__file__).resolve().parents[2]/'06_评测/golden.json').read_text())
    for name,product,month,kind in [('S1','银黄口服液','2026-05','monthly'),('S3','六味地黄胶囊','2026-03','monthly'),('Q2','银黄口服液','2026-06','quarterly')]:
        result=analyze('中药一厂',product,month,kind)
        for key in ('unit_cost','mom','yoy','budget'):
            if key in golden[name]:
                assert abs(D(result['metrics'][key]['value'])-D(golden[name][key]))<D('0.0000001')


def test_real_total_alerts_count_matches_independent_45_observations():
    unit_count=total_count=0
    for product in ('银黄口服液','板蓝根颗粒','六味地黄胶囊'):
        for month in ('2026-02','2026-03','2026-04','2026-05','2026-06'):
            result=analyze('中药一厂',product,month)
            unit_count+=sum(e['alerts']['unit'] for e in result['elements'])
            total_count+=sum(e['alerts']['total'] for e in result['elements'])
    assert (unit_count,total_count)==(0,31)
