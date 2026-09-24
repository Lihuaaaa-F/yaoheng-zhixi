"""Regression examples: the selected snapshot owns context, period and units."""
from copy import deepcopy
from decimal import Decimal as D

from pharma import attribution as A
from pharma import forecasting


def snapshot(*, basis='unit', analysis_type='quarterly'):
    # Q2 is up against Q1, although June is down against May. Monthly row reloads
    # would report the opposite conclusion. An unrelated enterprise shares names.
    current = {'quantity': '300', 'unit_cost': '8', 'total_cost': '2400',
               'elements_unit': {'materials': '6', 'labor': '2'},
               'elements_total': {'materials': '1800', 'labor': '600'}}
    prior = {'quantity': '200', 'unit_cost': '6', 'total_cost': '1200',
             'elements_unit': {'materials': '4', 'labor': '2'},
             'elements_total': {'materials': '800', 'labor': '400'}}
    periods = ['2026-01', '2026-02', '2026-03']
    elems = []
    for key, name in [('materials', '材料'), ('labor', '人工')]:
        changes = {}
        for b in ('unit', 'total'):
            a, z = current['elements_' + b][key], prior['elements_' + b][key]
            changes[b] = {'current': a, 'base': z, 'delta': str(D(a)-D(z)),
                          'comparison_period': periods}
        elems.append({'key': key, 'name': name, 'unit': current['elements_unit'][key],
                      'total': current['elements_total'][key], 'comparisons': {'mom': changes}})
    metric = 'unit_cost' if basis == 'unit' else 'total_cost'
    return {'snapshot_id': 'independent-fixture', 'context_id': 'generic:uploaded-enterprise',
            'factory': '同名工厂', 'product': '同名产品', 'month': '2026-06',
            'analysis_type': analysis_type, 'period': {'start': '2026-04', 'end': '2026-06'},
            'basis': basis, 'comparison': {'mom': {'current': current[metric], 'base': prior[metric],
                                                'delta': str(D(current[metric])-D(prior[metric]))}},
            'elements': elems, 'period_values': {'current': current, 'mom': prior},
            'metrics': {'unit_cost': {'unit': '元/件'}, 'total_cost': {'unit': '元'},
                        'mom': {'comparison_period': periods}},
            'trend': [{'month': '2026-05', 'unit_cost': '9'}, {'month': '2026-06', 'unit_cost': '8'}]}


def test_quarter_attribution_uses_same_snapshot_not_opposite_monthly_change(monkeypatch):
    monkeypatch.setattr(A, 'load_rows', lambda: (_ for _ in ()).throw(AssertionError('cross-context read')))
    s = snapshot()
    before = deepcopy(s)
    result = A.analyze_attribution_snapshot(s)
    assert result['status'] == 'PASS'
    assert result['direction'] == '上升' and D(result['total_delta']) == D('2')
    assert result['analysis_type'] == 'quarterly'
    assert result['base_period'] == ['2026-01', '2026-02', '2026-03']
    assert result['context_id'] == s['context_id'] and result['snapshot_id'] == s['snapshot_id']
    assert result['did']['status'] == result['price_signal']['status'] == 'UNAVAILABLE'
    assert s == before


def test_total_attribution_reconciles_quantity_and_unit_cost_from_current_enterprise():
    result = A.analyze_attribution_snapshot(snapshot(basis='total'))
    assert D(result['total_delta']) == D('1200')
    factors = next(d for d in result['dims'] if d['dim'].startswith('总量两因子'))
    assert sum(D(a['delta']) for a in factors['attributes']) == D('1200')
    assert result['value_unit'] == '元'


def test_missing_element_not_zero_filled_and_mismatched_components_fail_closed():
    s = snapshot()
    s['elements'][0]['comparisons']['mom']['unit']['base'] = None
    assert A.analyze_attribution_snapshot(s)['status'] == 'UNAVAILABLE'
    s = snapshot()
    s['comparison']['mom']['delta'] = '3'
    result = A.analyze_attribution_snapshot(s)
    assert result['status'] == 'UNAVAILABLE' and result['reason_code'] == 'ELEMENTS_DO_NOT_RECONCILE'


def test_forecast_coverage_is_computed_for_this_series_not_contest_global_rate():
    result = forecasting.forecast_series([(f'2026-0{i}', float(i)) for i in range(1, 7)])
    assert '88.9%' not in result['evaluation_notice'] and '45 检验点' not in result['interval']
    assert result['holdout']['interval_coverage'] == {
        'covered': 3, 'tested': 3, 'rate': 1.0, 'horizon': 1,
        'scope': 'current_series_rolling_origin',
    }
    short = forecasting.forecast_series([('2026-01', 1), ('2026-02', 2), ('2026-03', 3)])
    assert short['holdout']['interval_coverage']['rate'] is None
    assert short['holdout']['interval_coverage']['tested'] == 0


def test_competition_benchmark_total_basis_does_not_report_opposite_unit_direction(monkeypatch):
    from pharma import metrics
    seen = []

    def selected(factory, product, month, analysis_type, basis):
        seen.append(basis)
        s = snapshot(basis=basis)
        amounts = {'甲': ('100', '10', '1000', [('materials', '6', '600'), ('labor', '4', '400')]),
                   '乙': ('200', '8', '1600', [('labor', '4', '800'), ('materials', '4', '800')])}
        qty, unit, total, elements = amounts[factory]
        s['metrics'] = {key: {'value': value, 'unit': u, 'row_keys': [factory + ':' + key],
                             'source_hash': ['fixture-' + factory], 'metric_id': factory + ':' + key}
                        for key, value, u in [('unit_cost', unit, '元/盒'), ('total_cost', total, '元'),
                                              ('quantity', qty, '盒')]}
        s['elements'] = []
        for key, u, t in elements:
            s['elements'].append({'key': key, 'name': key, 'unit': u, 'total': t})
            s['metrics'][key] = {'value': u if basis == 'unit' else t, 'row_keys': [factory + ':' + key],
                                 'source_hash': ['fixture-' + factory], 'metric_id': factory + ':' + key}
        s['details'] = {'available': False}
        return s

    monkeypatch.setattr(metrics, 'analyze', selected)
    bound, result = metrics.benchmark_analysis('独立产品', '2026-06', '甲', '乙', 'quarterly', 'total')
    assert seen == ['total', 'total']
    assert result['basis'] == bound['benchmark_context']['basis'] == 'total'
    assert D(result['summary'][0]['delta']) == D('2')  # unit direction is positive
    assert D(result['summary'][1]['delta']) == D('-600')  # selected total is negative
    assert sum(D(e['delta']) for e in result['elements']) == D('-600')
    assert all(e['unit'] == '元' and D(e['denominator']) == D('-600') for e in result['elements'])
    for element in result['elements']:
        fact = bound['metrics'][element['metric_refs']['contribution']]
        assert D(fact['numerator']) / D(fact['denominator']) * 100 == D(fact['value'])
