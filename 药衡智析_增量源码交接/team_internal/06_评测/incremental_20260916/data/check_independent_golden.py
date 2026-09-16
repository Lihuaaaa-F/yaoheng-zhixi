"""Independent Fraction oracle from original CSVs; exercises public snapshot seams."""
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'05_原型/backend'))
from pharma.metrics import analyze, benchmark

rows = {'cost':[], 'budget':[]}
encoding = []
for path in sorted((ROOT/'01_数据/00_原始').rglob('*.csv')):
    raw = path.read_bytes()
    # Strict decoding only: no conversion, replacement or ignored characters.
    content = raw.decode('utf-8-sig')
    encoding.append({'file':str(path.relative_to(ROOT)), 'sha256':hashlib.sha256(raw).hexdigest(),
                     'strict_utf8':'PASS','replacement_characters':content.count('\ufffd')})
    kind = 'cost' if '成本汇总' in path.name else 'budget' if '预算数据' in path.name else None
    if kind:
        rows[kind].extend(csv.DictReader(content.splitlines()))

def aggregate(factory,product,months,kind='cost'):
    selected = [r for r in rows[kind] if r['工厂']==factory and r['产品名称']==product and r['月份'] in months]
    if {r['月份'] for r in selected} != set(months):
        return None
    prefix = '预算' if kind=='budget' else ''
    quantity = sum(F(r[prefix+'产量(盒)']) for r in selected)
    total = sum(F(r[prefix+'总成本(元)']) for r in selected)
    totals = {key:sum(F(r[prefix+name+'(元/盒)'])*F(r[prefix+'产量(盒)']) for r in selected)
              for key,name in [('materials','直接材料'),('labor','直接人工'),('overhead','制造费用')]}
    return {'quantity':quantity,'total_cost':total,'unit_cost':total/quantity,
            'unit':{key:value/quantity for key,value in totals.items()},'total':totals}

observations=[]
def check(case,field,actual,expected):
    good = actual is None if expected is None else actual is not None and abs(F(actual)-expected) < F(1,10**12)
    observations.append({'case':case,'field':field,'actual':actual,'expected_fraction':str(expected),
                         'status':'PASS' if good else 'FAIL'})

cases = []
for row in rows['cost']:
    factory,product,month = [row[k] for k in ('工厂','产品名称','月份')]
    cases.append((factory,product,month,'monthly',[month]))
    if month.endswith(('-03','-06')):
        number=int(month[-2:])
        cases.append((factory,product,month,'quarterly',[f'{month[:4]}-{m:02}' for m in range(number-2,number+1)]))

for factory,product,month,kind,months in cases:
    case = ':'.join((factory,product,month,kind))
    current=aggregate(factory,product,months)
    output=analyze(factory,product,month,kind)
    for key in ('quantity','total_cost','unit_cost'):
        check(case,key,output['metrics'][key]['value'],current[key])
    periods={'budget':months,'yoy':[f'{int(m[:4])-1}-{m[-2:]}' for m in months]}
    shifted=[]
    for m in months:
        index=int(m[:4])*12+int(m[-2:])-1-(3 if kind=='quarterly' else 1)
        shifted.append(f'{index//12:04}-{index%12+1:02}')
    periods['mom']=shifted
    for label,period in periods.items():
        base=aggregate(factory,product,period,'budget' if label=='budget' else 'cost')
        for element in output['elements']:
            key=element['key']
            for measure,total_key in [('unit','unit_cost'),('total','total_cost')]:
                bound=element['comparisons'][label][measure]
                numerator=current[measure][key]-base[measure][key] if base else None
                denominator=current[total_key]-base[total_key] if base else None
                percentage=100*numerator/denominator if denominator else None
                for field,expected in [('numerator',numerator),('denominator',denominator),('contribution',percentage)]:
                    check(case,f'{key}.{label}.{measure}.{field}',bound[field],expected)
        if label=='budget' and base:
            check(case,'budget.quantity_effect',output['budget_bridge']['quantity_effect'],(current['quantity']-base['quantity'])*base['unit_cost'])
            check(case,'budget.unit_cost_effect',output['budget_bridge']['unit_cost_effect'],current['quantity']*(current['unit_cost']-base['unit_cost']))

for product in ('银黄口服液','板蓝根颗粒','六味地黄胶囊'):
    for number in range(1,7):
        month=f'2026-{number:02}'
        left,right=aggregate('中药二厂',product,[month]),aggregate('中药一厂',product,[month])
        output=benchmark(product,month)
        denominator=left['unit_cost']-right['unit_cost']
        for element in output['elements']:
            numerator=left['unit'][element['key']]-right['unit'][element['key']]
            check(f'benchmark:{product}:{month}',element['key']+'.contribution',element['contribution'],100*numerator/denominator if denominator else None)

result={'created_at':datetime.now(timezone.utc).isoformat(),'method':'Original CSV + Fraction independent oracle; production public analyze/benchmark only',
        'scope':f"{sum(c[3]=='monthly' for c in cases)} monthly and {sum(c[3]=='quarterly' for c in cases)} complete quarterly snapshots; 18 cross-factory comparisons; all products, both factories, unit and total bases",
        'cases':len(cases),'observations':len(observations),'failures':sum(r['status']=='FAIL' for r in observations),
        'encoding':encoding,'checks':observations}
result['status']='PASS' if result['failures']==0 else 'FAIL'
destination=Path(__file__).with_name('independent_golden_result.json')
destination.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','encoding')},ensure_ascii=False,indent=2))
raise SystemExit(bool(result['failures']))
