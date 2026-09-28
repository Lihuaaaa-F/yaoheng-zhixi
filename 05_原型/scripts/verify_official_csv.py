"""One-off independent acceptance of official CSVs; not an official answer key."""
from __future__ import annotations

import csv
import json
import os
import sys
from decimal import Decimal as D
from pathlib import Path
from types import SimpleNamespace

app = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
package = app.parent / '00_赛题原始资料/模拟数据_V1.1_净化解压/创灵境_考题模拟数据'
os.environ.update(PHARMA_RUNTIME_DIR=str(out / 'runtime'),
                  PHARMA_ARTIFACTS_DIR=str(out / 'artifacts'),
                  PHARMA_DATA_PACKAGE=str(package), PHARMA_SYNTHETIC_DETAIL_DIR='')
sys.path.insert(0, str(app / 'backend'))
from pharma import config, data_import, import_pipeline, industry, metrics, narrative
from pharma.jobs import JobStore

# Exercise the real deterministic fallback while preventing any model request.
calls = []
def forbidden_call(*args, **kwargs):
    calls.append('attempted')
    raise AssertionError('External model calls forbidden in this acceptance')
narrative.ModelGateway.complete = forbidden_call
narrative.ModelGateway.for_route = staticmethod(lambda route: SimpleNamespace(available=False, key=''))

sources = sorted(package.glob('01_*/*.csv')) + sorted(package.glob('02_*/*.csv'))
actual, budget, material_rows, uploaded = [], [], [], []
for source in sources:
    name = source.name
    rows = list(csv.DictReader(source.read_text(encoding='utf-8-sig').splitlines()))
    if '成本汇总' in name:
        kind = 'cost_summary'
        actual += rows
    elif '预算' in name:
        kind = 'budget'
        budget += rows
    elif '原材料' in name:
        kind = 'material_detail'
        material_rows += rows
    elif '制造费用' in name:
        kind = 'manufacturing_detail'
    elif '人工工时' in name:
        kind = 'labor_detail'
    else:
        kind = 'industry_reference'
    uploaded.append(data_import.create_upload('business', name, source.read_bytes(), kind))

assert len(uploaded) == 10
store = JobStore(out / 'runtime' / 'jobs.sqlite3')
job = store.enqueue('data_parse', {'import_ids': [r['id'] for r in uploaded]})
import_pipeline.run_data_parse(store, job)
finished = store.get(job['id'])
assert finished['status'] == 'SUCCEEDED', finished.get('error')
state = data_import.workspace_state()
assert state['status'] == 'READY' and state['all_files_included']
assert len(state['imported_files']) == 10
context = finished['result']['published']['context_id']

checks, specification_checks, max_relative, max_absolute = [], 0, D(0), D(0)
def check(label, observed, expected):
    global max_relative, max_absolute
    if expected is None:
        assert observed is None, (label, observed, expected)
        checks.append({'check': label, 'expected': None, 'observed': None})
        return
    assert observed is not None, (label, observed, expected)
    expected, observed = D(str(expected)), D(str(observed))
    absolute = abs(observed - expected)
    relative = absolute / abs(expected) if expected else D(0)
    max_relative, max_absolute = max(max_relative, relative), max(max_absolute, absolute)
    assert absolute <= max(D('1e-20'), abs(expected) * D('1e-20')), (label, observed, expected)
    checks.append({'check': label, 'expected': str(expected), 'observed': str(observed),
                   'absolute_error': str(absolute), 'relative_error': str(relative)})

def period_months(month, kind):
    year, number = map(int, month.split('-'))
    return [f'{year}-{m:02d}' for m in range(number-2, number+1)] if kind == 'quarterly' else [month]

def prior_months(months, offset):
    result = []
    for month in months:
        year, number = map(int, month.split('-'))
        index = year * 12 + number - 1 + offset
        result.append(f'{index // 12}-{index % 12 + 1:02d}')
    return result

elements = ('直接材料', '直接人工', '制造费用')
element_names = {'material': '直接材料', 'materials': '直接材料',
                 'labor': '直接人工', 'overhead': '制造费用'}
def golden(factory, product, months, scenario='actual'):
    rows = [r for r in (budget if scenario == 'budget' else actual)
            if r['工厂'] == factory and r['产品名称'] == product and r['月份'] in months]
    if {r['月份'] for r in rows} != set(months):
        return None
    prefix = '预算' if scenario == 'budget' else ''
    quantity = sum((D(r[prefix + '产量(盒)']) for r in rows), D(0))
    total = sum((D(r[prefix + '总成本(元)']) for r in rows), D(0))
    element_totals = {name: sum((D(r[prefix + name + '(元/盒)']) * D(r[prefix + '产量(盒)'])
                               for r in rows), D(0)) for name in elements}
    assert sum(element_totals.values(), D(0)) == total
    return {'quantity': quantity, 'total_cost': total, 'unit_cost': total / quantity,
            'unit': {key: value / quantity for key, value in element_totals.items()},
            'total': element_totals}

def difference(value, base):
    return value - base if value is not None and base is not None else None

def rate(value, base):
    return (value - base) / base * 100 if value is not None and base else None

scenarios = json.loads((app.parent / 'competition_configuration/scenarios.json').read_text())
executed = []
for scenario in scenarios:
    product, month, kind = scenario['product'], scenario['month'], scenario['analysis_type']
    months = period_months(month, kind)
    previous = prior_months(months, -3 if kind == 'quarterly' else -1)
    for basis in ('unit', 'total'):
        chosen = 'unit_cost' if basis == 'unit' else 'total_cost'
        label = f'{scenario["id"]}:{product}:{kind}:{basis}'
        goldens = {}
        for factory in ('中药一厂', '中药二厂'):
            current = golden(factory, product, months)
            assert current is not None
            goldens[factory] = current
            bases = {'mom': golden(factory, product, previous),
                     'yoy': golden(factory, product, prior_months(months, -12)),
                     'budget': golden(factory, product, months, 'budget')}
            for route, cid in [('original', 'pharmaceutical:competition'), ('uploaded', context)]:
                snapshot = industry.analyze_reference(cid, factory, product, month, kind, basis)
                tag = f'{label}:{factory}:{route}'
                source_specs = {r['产品规格'] for r in actual if r['工厂'] == factory
                                and r['产品名称'] == product and r['月份'] in months}
                assert source_specs == {snapshot['specification']}, (tag, source_specs, snapshot['specification'])
                specification_checks += 1
                for key in ('quantity', 'total_cost', 'unit_cost'):
                    check(tag + ':' + key, snapshot['metrics'][key]['value'], current[key])
                observed_elements = {element_names[r['key']]: r for r in snapshot['elements']}
                for name in elements:
                    row = observed_elements[name]
                    for measure in ('unit', 'total'):
                        check(tag + ':' + name + ':' + measure, row[measure], current[measure][name])
                    base = bases['mom']
                    delta = difference(current[basis][name], base[basis][name] if base else None)
                    total_delta = difference(current[chosen], base[chosen] if base else None)
                    check(tag + ':' + name + ':contribution', row['contribution'],
                          delta / total_delta * 100 if total_delta and delta is not None else None)
                    for comparison, base in bases.items():
                        for measure in ('unit', 'total'):
                            result = row['comparisons'][comparison][measure]
                            base_value = base[measure][name] if base else None
                            check(tag + ':' + name + ':' + comparison + ':' + measure + ':delta',
                                  result['delta'], difference(current[measure][name], base_value))
                            check(tag + ':' + name + ':' + comparison + ':' + measure + ':rate',
                                  result['rate'], rate(current[measure][name], base_value))
                for comparison, base in bases.items():
                    check(tag + ':' + comparison, snapshot['metrics'][comparison]['value'],
                          rate(current[chosen], base[chosen] if base else None))
                if factory == '中药二厂':
                    assert not snapshot['details']['available']
                else:
                    for item in snapshot['materials_summary']:
                        def material_cost(period, aggregate):
                            matched = [r for r in material_rows if r['工厂'] == factory
                                       and r['产品名称'] == product and r['月份'] in period
                                       and r['原材料名称'] == item['name']]
                            if not aggregate or {r['月份'] for r in matched} != set(period):
                                return None
                            return sum((D(r['原材料总成本(元)']) for r in matched), D(0)) / aggregate['quantity']
                        value, old = material_cost(months, current), material_cost(previous, bases['mom'])
                        check(tag + ':material:' + item['name'] + ':current', item['current'], value)
                        check(tag + ':material:' + item['name'] + ':previous', item['previous'], old)
                        check(tag + ':material:' + item['name'] + ':delta', item['delta'], difference(value, old))
        left, right = goldens['中药一厂'], goldens['中药二厂']
        for route in ('original', 'uploaded'):
            if route == 'original':
                _, comparison = metrics.benchmark_analysis(product, month, '中药一厂', '中药二厂', kind, basis)
            else:
                _, comparison = industry.benchmark_reference(context, product, month, '中药一厂', '中药二厂', kind, basis)
            assert comparison['direction'].startswith('中药一厂−中药二厂')
            for row in comparison['summary']:
                key = row['key']
                check(label + ':' + route + ':benchmark:' + key + ':delta', row['delta'], left[key] - right[key])
                check(label + ':' + route + ':benchmark:' + key + ':rate', row['rate'], rate(left[key], right[key]))
            for row in comparison['elements']:
                name = element_names[row['key']]
                delta, denominator = left[basis][name] - right[basis][name], left[chosen] - right[chosen]
                check(label + ':' + route + ':benchmark:' + name + ':delta', row['delta'], delta)
                check(label + ':' + route + ':benchmark:' + name + ':rate', row['rate'], rate(left[basis][name], right[basis][name]))
                check(label + ':' + route + ':benchmark:' + name + ':contribution', row['contribution'],
                      delta / denominator * 100 if denominator else None)
        executed.append({'scenario': scenario, 'basis': basis, 'status': 'PASS'})

assert not calls
receipt = {'status': 'PASS', 'source': 'Independent Decimal arithmetic directly from official CSV source cells',
           'official_answer_key_available': False, 'uploaded_files': len(uploaded),
           'upload_parse_status': finished['status'], 'workspace_status': state['status'],
           'analysis_routes': ['original package', 'cumulative uploaded workspace'],
           'scenario_basis_combinations': executed, 'numeric_checks': len(checks),
           'source_specification_checks': specification_checks,
           'max_absolute_error': str(max_absolute), 'max_relative_error': str(max_relative),
           'difference_requirement_relative': '0.01', 'external_model_calls': len(calls),
           'second_factory_detail': 'Unavailable in original supplied data; no fabricated detail',
           'checks': checks}
(out / 'independent_official_csv_receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2))
print(json.dumps({key: value for key, value in receipt.items() if key != 'checks'}, ensure_ascii=False, indent=2))
