"""单一确定性指标快照：API、图表与报告共享同一份计算结果。

制药原题数据专用引擎（行业包走 industry.py）：全部口径用 Decimal 计算，
环比/同比/预算共用 change/contribution 阈值函数；±10% 严格超限才触发告警
（恰好等于阈值不触发），贡献率允许为负或超过 100%，缺月不补零。
"""
from __future__ import annotations
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from .ingestion import ingest, load_rows

D = Decimal
FORMULA_VERSION = 'cost-formulas-1.1'
from .ingestion import _CONTRACT, source_contract, source_contract_hash
ELEMENTS = _CONTRACT['elements']


def contribution(delta, total_delta):
    if delta is None or total_delta is None or D(str(total_delta)) == 0:
        return None
    return _text(D(str(delta))/D(str(total_delta))*100)


def threshold_alert(rate):
    """Strict element threshold in percentage points; null is unavailable."""
    return rate is not None and abs(D(str(rate))) > D('10')


def _decimal(value):
    return None if value is None else D(str(value))


def _text(value):
    return None if value is None else format(value, 'f')


def change(current, base):
    """Public comparison seam; missing and zero bases remain explicit N/A."""
    current = D(str(current)) if current is not None else None
    base = D(str(base)) if base is not None else None
    reason = '本期无可定义数值（产量为0或数据缺失）' if current is None else '缺少完整比较期数据' if base is None else '基期为0，比例无定义' if base == 0 else None
    return {'current': _text(current), 'base': _text(base),
            'delta': _text(current-base) if current is not None and base is not None else None,
            'rate': _text((current-base)/base*100) if current is not None and base not in (None, D(0)) else None,
            'reason': reason}


def _months(month, kind):
    year, number = map(int, month.split('-'))
    if number not in range(1, 13):
        raise ValueError('INVALID_MONTH')
    if kind == 'quarterly':
        if number % 3:
            raise ValueError('QUARTER_END_MONTH_REQUIRED')
        end = ((number-1)//3+1)*3
        return [f'{year:04}-{m:02}' for m in range(end-2,end+1)]
    if kind not in ('monthly','special'):
        raise ValueError('INVALID_ANALYSIS_TYPE')
    return [month]


def _shift(month, amount):
    year, number = map(int, month.split('-'))
    index = year*12+number-1+amount
    return f'{index//12:04}-{index%12+1:02}'


def _aggregate(rows, months, kind='cost'):
    selected = [r for r in rows if r['kind']==kind and r['month'] in months]
    if {r['month'] for r in selected} != set(months):
        return None
    prefix = '预算' if kind == 'budget' else ''
    quantity = sum(D(r['data'][prefix+'产量(盒)']) for r in selected)
    total = sum(D(r['data'][prefix+'总成本(元)']) for r in selected)
    elements = {key: sum(D(r['data'][prefix+name+'(元/盒)'])*D(r['data'][prefix+'产量(盒)']) for r in selected) for key,name in ELEMENTS.items()}
    return {'quantity': quantity, 'total_cost': total, 'unit_cost': total/quantity if quantity else None,
            'elements_total': elements, 'elements_unit': {k:v/quantity if quantity else None for k,v in elements.items()}, 'rows': selected}


def _metric(key, value, unit, formula, rows, numerator=None, denominator=None, comparison_period=None, reason=None):
    return {'metric_id': key, 'value': _text(value), 'display': 'N/A' if value is None else format(value.quantize(D('0.01'), rounding=ROUND_HALF_UP), 'f'),
            'unit': unit, 'formula': formula, 'formula_version': FORMULA_VERSION,
            'numerator': _text(numerator), 'denominator': _text(denominator), 'comparison_period': comparison_period,
            'row_keys': [r['row_key'] for r in rows], 'source_hash': sorted({r['source_hash'] for r in rows}), 'reason': reason or ('数据缺失或分母为0，数值无定义' if value is None else None)}


def catalog():
    manifest = ingest()
    rows = [r for r in load_rows() if r['kind']=='cost']
    return {'factories': sorted({r['factory'] for r in rows}), 'products': sorted({r['product'] for r in rows}),
            'months': sorted({r['month'] for r in rows}), 'snapshot_id': manifest['snapshot_id']}


def analyze(factory, product, month, analysis_type='monthly', basis='unit'):
    if basis not in ('unit', 'total'):
        raise ValueError('INVALID_BASIS')
    manifest = ingest()
    all_rows = load_rows()
    rows = [r for r in all_rows if r['factory']==factory and r['product']==product]
    months = _months(month, analysis_type)
    current = _aggregate(rows, months)
    if current is None:
        raise ValueError('NO_COMPLETE_PERIOD_DATA')
    comparison_months = {'mom': [_shift(m,-3 if analysis_type=='quarterly' else -1) for m in months],
                         'yoy': [_shift(m,-12) for m in months], 'budget': months}
    bases = {k:_aggregate(rows, periods, 'budget' if k=='budget' else 'cost') for k,periods in comparison_months.items()}
    scope = f'{factory}:{product}:{months[0]}:{months[-1]}:{basis}'
    metrics = {}
    for key,unit,formula in [('unit_cost','元/盒','Σ总成本/Σ产量'),('total_cost','元','Σ(产量×单位成本)'),('quantity','盒','Σ产量')]:
        metrics[key] = _metric(scope+':'+key, current[key], unit, formula, current['rows'],
            current['total_cost'] if key=='unit_cost' else current[key], current['quantity'] if key=='unit_cost' else D(1))
    field = 'unit_cost' if basis=='unit' else 'total_cost'
    comparison = {key: change(current[field], base[field] if base else None) for key,base in bases.items()}
    for key,item in comparison.items():
        base = bases[key]
        metrics[key] = _metric(scope+':'+key, D(item['rate']) if item['rate'] is not None else None, '%', '(本期−基期)/基期×100',
            current['rows']+(base['rows'] if base else []), D(item['delta']) if item['delta'] else None, D(item['base']) if item['base'] else None,
            comparison_months[key], item['reason'])
    previous = bases['mom']
    elements, alerts = [], []
    for key,name in ELEMENTS.items():
        unit_change = change(current['elements_unit'][key], previous['elements_unit'][key] if previous else None)
        total_change = change(current['elements_total'][key], previous['elements_total'][key] if previous else None)
        selected = unit_change if basis=='unit' else total_change
        denominator = D(comparison['mom']['delta']) if comparison['mom']['delta'] is not None else None
        delta = D(selected['delta']) if selected['delta'] is not None else None
        contribution_value = contribution(delta, denominator)
        flag = {'unit': False, 'total': False}
        for b,c in [('unit',unit_change),('total',total_change)]:
            rate = D(c['rate']) if c['rate'] is not None else None
            flag[b] = threshold_alert(rate)
            if flag[b]:
                alerts.append({'alert_id':'alert-'+hashlib.sha256(f'{scope}:{key}:{b}'.encode()).hexdigest()[:20], 'element_key':key, 'metric_id':scope+':'+key+'_'+b+'_rate', 'fact_summary':f'{name} {b} 环比 {_text(rate)}%，基期 {c["base"]}，本期 {c["current"]}', 'element':name,'basis':b,'current':c['current'],'base':c['base'],'value_unit':'元/盒' if b=='unit' else '元','rate':_text(rate),'rule':'严格大于+10%或小于−10%', 'note':'总额同时受产量影响' if b=='total' else '单位要素成本'})
        elements.append({'key':key,'name':name,'unit':_text(current['elements_unit'][key]),'total':_text(current['elements_total'][key]),
            'delta':_text(delta),'contribution':contribution_value,'contribution_reason': '总变动为0或基期缺失' if contribution_value is None else None,
            'unit_mom':unit_change['rate'],'total_mom':total_change['rate'],'alerts':flag,
            'share':_text(current['elements_total'][key]/current['total_cost']*100) if current['total_cost'] else None,
            'unit_delta':unit_change['delta'],'total_delta':total_change['delta'],
            'unit_contribution':contribution(unit_change['delta'],change(current['unit_cost'],previous['unit_cost'] if previous else None)['delta']),
            'total_contribution':contribution(total_change['delta'],change(current['total_cost'],previous['total_cost'] if previous else None)['delta']),
            'previous_unit':_text(previous['elements_unit'][key]) if previous else None,
            'budget_unit':_text(bases['budget']['elements_unit'][key]) if bases['budget'] else None,
            'budget_rate':change(current['elements_unit'][key], bases['budget']['elements_unit'][key] if bases['budget'] else None)['rate']})
        metrics[key] = _metric(scope+':'+key,current['elements_unit'][key] if basis=='unit' else current['elements_total'][key], '元/盒' if basis=='unit' else '元',
            'Σ(要素单位成本×产量)/Σ产量' if basis=='unit' else 'Σ(要素单位成本×产量)',current['rows'],current['elements_total'][key],current['quantity'] if basis=='unit' else D(1))
        for measure,unit_name,c in [('unit','元/盒',unit_change),('total','元',total_change)]:
            refs=current['rows']+(previous['rows'] if previous else [])
            for suffix,number,num,den,formula,output_unit in [
                ('delta',c['delta'],D(c['delta']) if c['delta'] is not None else None,D(1),'本期要素−基期要素',unit_name),
                ('rate',c['rate'],D(c['delta']) if c['delta'] is not None else None,D(c['base']) if c['base'] is not None else None,'(本期要素−基期要素)/基期要素×100','%'),
                ('contribution',elements[-1][measure+'_contribution'],D(c['delta']) if c['delta'] is not None else None,
                 _decimal(change(current['unit_cost' if measure=='unit' else 'total_cost'],previous['unit_cost' if measure=='unit' else 'total_cost'] if previous else None)['delta']),
                 '要素变动额/同口径总变动额×100','%')]:
                metric_key=key+'_'+measure+'_'+suffix
                metrics[metric_key]=_metric(scope+':'+metric_key,D(number) if number is not None else None,output_unit,formula,refs,num,den,comparison_months['mom'],c['reason'] if number is None else None)
        # Every comparison owns its period, basis and denominator. Legacy fields above
        # remain month-on-month for existing consumers; other comparisons never reuse them.
        elements[-1]['comparisons'] = {}
        for label, base in bases.items():
            elements[-1]['comparisons'][label] = {}
            refs = current['rows'] + (base['rows'] if base else [])
            for measure, total_field, output_unit in [('unit','unit_cost','元/盒'),('total','total_cost','元')]:
                c = change(current['elements_'+measure][key], base['elements_'+measure][key] if base else None)
                denominator = change(current[total_field],base[total_field] if base else None)['delta']
                percentage = contribution(c['delta'],denominator)
                bound = {**c, 'contribution':percentage, 'numerator':c['delta'], 'denominator':denominator,
                         'comparison_period':comparison_months[label], 'comparison_object':label,
                         'basis':measure, 'unit':output_unit,
                         'contribution_reason': '总变动为0或基期缺失' if percentage is None else None}
                elements[-1]['comparisons'][label][measure] = bound
                for suffix, value, den, unit_name, formula in [
                    ('delta',c['delta'],'1',output_unit,'本期要素−所选基期要素'),
                    ('rate',c['rate'],c['base'],'%','(本期要素−所选基期要素)/所选基期要素×100'),
                    ('contribution',percentage,denominator,'%','要素变动额/同一比较对象同口径总变动额×100')]:
                    metric_key = f'{key}_{label}_{measure}_{suffix}'
                    metrics[metric_key] = _metric(scope+':'+metric_key,_decimal(value),unit_name,formula,
                        refs,_decimal(c['delta']),_decimal(den),comparison_months[label],
                        bound['contribution_reason'] if suffix=='contribution' else c['reason'])
        elements[-1]['yoy_unit'] = _text(bases['yoy']['elements_unit'][key]) if bases['yoy'] else None
        elements[-1]['yoy_rate'] = elements[-1]['comparisons']['yoy']['unit']['rate']
    trend=[]
    for m in sorted({r['month'] for r in rows if r['kind']=='cost' and _shift(month,-5)<=r['month']<=month}):
        a=_aggregate(rows,[m])
        trend.append({'month':m, **{k:_text(a[k]) for k in ('unit_cost','total_cost','quantity')},
                      **{k:_text(v) for k,v in a['elements_unit' if basis=='unit' else 'elements_total'].items()}})
    details = {'available':False,'reason':'该工厂/期间无原料、费用和工时明细；不按比例推算', 'materials':[],'expenses':[],'labor':[],'market':[]}
    for r in rows:
        if r['month'] in months and r['kind'] in ('materials','expenses','labor'):
            details[r['kind']].append({**r['data'],'row_key':r['row_key'],'source_hash':r['source_hash']})
            details['available']=True
            details['reason']=None
    # 二厂明细为合成演示数据（按题包汇总精确校准）：在明细出口统一标注，
    # 报告/看板/对标均携带该声明，不冒充真实二厂经营明细。
    from .config import SYNTHETIC_DETAIL_FACTORIES
    if details['available'] and factory in SYNTHETIC_DETAIL_FACTORIES:
        details['data_label'] = '合成演示数据：数值按题包二厂成本汇总精确校准（结构比例取自一厂），非真实二厂经营明细'
    material_names = {r['原材料名称'] for r in details['materials']}
    details['market'] = [{**{k:v for k,v in r['data'].items() if not k.endswith('月价格') or int(k[:-3]) <= int(month[5:])},'row_key':r['row_key'],'source_hash':r['source_hash']} for r in all_rows if r['kind']=='market' and r['data']['药材名称'] in material_names]
    if manifest.get('masterdata_hash')!=source_contract_hash():raise ValueError('MASTERDATA_CHANGED_DURING_ANALYSIS')
    spec,divisor,unit,category=source_contract()['specifications'][product]
    actual_specs={r['data']['产品规格'] for r in current['rows']}
    if actual_specs != {spec}:
        raise ValueError('UNVERIFIED_PRODUCT_SPECIFICATION: '+str(actual_specs))
    industry={'rows':[{**r['data'],'row_key':r['row_key'],'source_hash':r['source_hash']} for r in all_rows if r['kind']=='industry' and r['data']['产品类别']==category],
              'converted_unit_cost':_text(current['unit_cost']/divisor) if current['unit_cost'] is not None else None,'unit':unit,'divisor':str(divisor),
              'notice':'题包静态模拟行业参考；本厂水平不是所选月实测。缺收入，毛利率和费用收入比不可独立计算。'}
    bridge=None
    budget=bases['budget']
    if budget and current['unit_cost'] is not None and budget['unit_cost'] is not None:
        volume=(current['quantity']-budget['quantity'])*budget['unit_cost']
        unit_effect=current['quantity']*(current['unit_cost']-budget['unit_cost'])
        bridge={'quantity_effect':_text(volume),'unit_cost_effect':_text(unit_effect),'total_delta':_text(current['total_cost']-budget['total_cost']),
                'formula':'(实际量−预算量)×预算单位成本＋实际量×(实际单位成本−预算单位成本)','note':'不是采购单价×实物耗量分解'}
        bridge['metric_refs'] = {}
        for key,value,formula in [('quantity_effect',volume,'(实际产量−预算产量)×预算单位成本'),
                                 ('unit_cost_effect',unit_effect,'实际产量×(实际单位成本−预算单位成本)'),
                                 ('total_delta',current['total_cost']-budget['total_cost'],'实际总成本−预算总成本')]:
            metric_key = 'budget_'+key
            metrics[metric_key] = _metric(scope+':'+metric_key,value,'元',formula,
                current['rows']+budget['rows'],value,D(1),comparison_months['budget'])
            bridge['metric_refs'][key] = metric_key
    period_values = {}
    for label,a in {'current':current,**bases}.items():
        period_values[label] = None if a is None else {**{k:_text(a[k]) for k in ('quantity','unit_cost','total_cost')},
            'elements_unit':{k:_text(v) for k,v in a['elements_unit'].items()},'elements_total':{k:_text(v) for k,v in a['elements_total'].items()}}
    period_changes={key:{label:change(current[key],b[key] if b else None) for label,b in bases.items()} for key in ('quantity','unit_cost','total_cost')}
    labor_metrics={}
    for label,period in [('current',months),('mom',comparison_months['mom'])]:
        rr=[r for r in rows if r['kind']=='labor' and r['month'] in period]
        if {r['month'] for r in rr} != set(period):
            labor_metrics[label]={'hours_per_10000':None,'hourly_wage':None,'efficiency':None,'reason':'缺少完整期间工时数据'}
            continue
        hours=sum(D(r['data']['总工时(小时)']) for r in rr)
        qty=sum(D(r['data']['产量(盒)']) for r in rr)
        wages=sum(D(r['data']['直接人工总额(元)']) for r in rr)
        person_days=sum(D(r['data']['生产人数(人)'])*D(r['data']['工作天数(天)']) for r in rr)
        labor_metrics[label]={'hours':_text(hours),'hours_per_10000':_text(hours/qty*10000) if qty else None,
            'hourly_wage':_text(wages/hours) if hours else None,'efficiency':_text(qty/person_days) if person_days else None,'reason':None,
            'row_keys':[r['row_key'] for r in rr],'source_hashes':sorted({r['source_hash'] for r in rr})}
    labor_metrics['rates']={k:change(labor_metrics['current'][k],labor_metrics['mom'][k])['rate'] for k in ('hours_per_10000','hourly_wage','efficiency')}
    labor_metrics['definitions']={'hours_per_10000':'Σ工时/Σ产量×10000，小时/万盒','hourly_wage':'题包折算口径：Σ直接人工总额/Σ工时，元/小时；不等同基础薪率','efficiency':'Σ产量/Σ(生产人数×工作天数)，盒/人·日'}
    materials_summary=[]
    for name in sorted({r['data']['原材料名称'] for r in rows if r['kind']=='materials' and r['month'] in months}):
        values, refs, material_totals, material_quantities = {}, {}, {}, {}
        for label,period in [('current',months),('previous',comparison_months['mom'])]:
            rr = [r for r in rows if r['kind']=='materials' and r['month'] in period and r['data']['原材料名称']==name]
            quantity = sum(D(r['data']['产量(盒)']) for r in rr)
            complete = {r['month'] for r in rr}==set(period)
            material_totals[label] = sum(D(r['data']['原材料总成本(元)']) for r in rr) if complete else None
            material_quantities[label] = quantity if complete else None
            values[label] = material_totals[label]/quantity if quantity and complete else None
            refs[label] = rr
        c = change(values['current'],values['previous'])
        denominator = elements[0]['comparisons']['mom']['unit']['delta']
        percentage = contribution(c['delta'],denominator)
        item = {'name':name,'current':c['current'],'previous':c['base'],'delta':c['delta'],'rate':c['rate'],
                'contribution':percentage,'numerator':c['delta'],'denominator':denominator,'unit':'元/盒',
                'comparison_period':comparison_months['mom'],'reason':c['reason'],
                'contribution_reason':'原料明细不完整或材料总变动为0' if percentage is None else None,
                'source_labels':[f"{r['row_key'].rsplit(':',1)[0]}·{product}·{r['month']}" for r in refs['current']+refs['previous']],
                'metric_refs':{}}
        for key,value,unit_name,formula,num,den in [
            ('current',values['current'],'元/盒','Σ本期原料总成本/Σ本期产量',material_totals['current'],material_quantities['current']),
            ('previous',values['previous'],'元/盒','Σ上期原料总成本/Σ上期产量',material_totals['previous'],material_quantities['previous']),
            ('delta',_decimal(c['delta']),'元/盒','本期原料单位消耗成本−上期原料单位消耗成本',_decimal(c['delta']),D(1)),
            ('contribution',_decimal(percentage),'%','原料单位消耗成本变动/材料单位成本总变动×100',_decimal(c['delta']),_decimal(denominator))]:
            metric_key = f'material:{name}:{key}'
            used = refs['current'] if key=='current' else refs['previous'] if key=='previous' else refs['current']+refs['previous']
            metrics[metric_key] = _metric(scope+':'+metric_key,value,unit_name,formula,used,num,den,
                comparison_months['mom'] if key!='current' else months,item['contribution_reason'] if key=='contribution' else c['reason'] if value is None else None)
            item['metric_refs'][key] = metric_key
        materials_summary.append(item)
    materials_summary.sort(key=lambda r: (r['delta'] is None, -abs(D(r['delta'])) if r['delta'] is not None else D(0),r['name']))
    expenses_summary=[]
    for category in sorted({r['data']['费用类别'] for r in rows if r['kind']=='expenses'}):
        values={}
        for label,period in [('current',months),('mom',comparison_months['mom'])]:
            rr=[r for r in rows if r['kind']=='expenses' and r['month'] in period and r['data']['费用类别']==category]
            qty=sum(D(r['data']['产量(盒)']) for r in rr)
            values[label]=sum(D(r['data']['费用总额(元)']) for r in rr)/qty if qty and {r['month'] for r in rr}==set(period) else None
        c=change(values['current'],values['mom'])
        expenses_summary.append({'name':category,'current':c['current'],'previous':c['base'],'rate':c['rate'],'delta':c['delta'],'unit':'元/盒','reason':c['reason']})
    result={'period_values':period_values,'period_changes':period_changes,'labor_metrics':labor_metrics,'materials_summary':materials_summary,'expenses_summary':expenses_summary,'data_version':manifest['snapshot_id'],'snapshot_id': '', 'formula_version':FORMULA_VERSION,'factory':factory,'product':product,'month':months[-1],
            'analysis_type':analysis_type,'specification':spec,'basis':basis,'period':{'start':months[0],'end':months[-1]},'metrics':metrics,'comparison':comparison,
            'elements':elements,'trend':trend,'details':details,'industry':industry,'budget_bridge':bridge,'alerts':alerts,
            'source_hashes':sorted({r['source_hash'] for r in rows}), 'limits':['原料单位消耗成本不是采购单价或实物耗用量；市场价格不代表企业采购价','设备事件与成本共变只支持假设；维修费不额外加入汇总']}
    result['snapshot_id']=hashlib.sha256(json.dumps(result,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return result


def benchmark_partner(factory=None, product=None):
    """报告对标基准厂的统一策略（2026-09-22 扩展性）：
    ① 主数据 benchmark_factory 指定优先（赛题口径：与中药二厂对标）；
    ② 指定厂不生产该产品（新药品只部分厂生产）时，回退到生产该产品的
       其他厂——配对必须有可比数据，否则报告对标章节整体失败；
    ③ 无产品约束时回退目录序第一个其他厂。
    UI 跨厂对标页不受此限制（用户任选两厂）。"""
    factories=source_contract()['factories']
    factory=factory or factories[0]
    designated=source_contract().get('benchmark_factory')
    def rows_safe():
        # 未导入数据快照（新部署/CI 无 .runtime/data）时按“无产品数据”处理，
        # 候选为空 → 返回 None；调用方各自已有“缺少第二工厂”降级路径。
        try:
            return load_rows()
        except FileNotFoundError:
            return []
    def produces(f):
        if product is None:
            return True
        rows = [r for r in rows_safe() if r['kind']=='cost' and r['factory']==f and r['product']==product]
        return bool(rows)
    if designated and designated!=factory and designated in factories and produces(designated):
        return designated
    candidates=[x for x in factories if x!=factory and produces(x)]
    if not candidates:
        rows=[r for r in rows_safe() if r['kind']=='cost' and r['product']==product] if product else []
        by_data=sorted({r['factory'] for r in rows}-{factory})
        candidates=by_data
    return candidates[0] if candidates else None

def _benchmark_factories(left, right, factory=None, product=None):
    """缺省方向与报告路径一致：以 benchmark_partner 选出的对标厂为基准（右厂/分母）。

    2026-09-23 修复（审计 AUD-BENCH-02）：此前缺省 left/right 取 factories[1]/[0]，
    与报告/worker 路径显式传入的"本单位−对标厂，以对标厂为分母"方向相反，
    直接调用 benchmark() 时差异额符号易被误读。现在缺省时：
    - 两厂都未给：base=factory（或目录首厂），partner=benchmark_partner(base)；
    - 只给 left：right=benchmark_partner(left)；
    - 只给 right：left=benchmark_partner(right)。
    partner 为 None（无第二工厂）时显式拒绝。
    """
    factories = source_contract()['factories']
    if len(factories) < 2 and (left is None or right is None):
        raise ValueError('TWO_FACTORIES_REQUIRED')
    if left is not None and right is not None:
        return left, right
    if right is None:
        partner = benchmark_partner(left or factory or factories[0], product)
        if partner is None:
            raise ValueError('TWO_FACTORIES_REQUIRED')
        return left or (factory or factories[0]), partner
    partner = benchmark_partner(right, product)
    if partner is None:
        raise ValueError('TWO_FACTORIES_REQUIRED')
    return partner, right


def benchmark(product, month, left=None, right=None, analysis_type='monthly', factory=None):
    """跨厂对标：方向为 left−right，以 right 为分母。

    缺省（left/right 未传）时按"factory（本单位）− benchmark_partner（对标厂）"
    配对，与报告/worker 路径同向；见 _benchmark_factories。
    """
    left,right=_benchmark_factories(left,right,factory,product)
    a,b=analyze(left,product,month,analysis_type),analyze(right,product,month,analysis_type)
    summary=[]
    for key,name,unit in [('unit_cost','单位成本','元/盒'),('total_cost','总成本','元'),('quantity','产量','盒')]:
        x,y=a['metrics'][key]['value'],b['metrics'][key]['value']
        summary.append({'name':name,'key':key,'unit':unit,'left':x,'right':y,**{k:v for k,v in change(x,y).items() if k in ('delta','rate','reason')}})
    elements=[]
    for x,y in zip(a['elements'],b['elements']):
        c = change(x['unit'],y['unit'])
        denominator = summary[0]['delta']
        elements.append({'key':x['key'],'name':x['name'],'unit':'元/盒','left':x['unit'],'right':y['unit'],
            **{k:v for k,v in c.items() if k in ('delta','rate','reason')},
            'contribution':contribution(c['delta'],denominator),'numerator':c['delta'],'denominator':denominator,
            'comparison_period':a['period'], 'comparison_object':f'{left}−{right}',
            'contribution_reason':'跨厂单位成本总差额为0' if denominator is not None and D(denominator)==0 else None})
    from .config import SYNTHETIC_DETAIL_FACTORIES as _synth_factories
    if _synth_factories:
        benchmark_hypothesis='跨厂成本差异已由同规格月度成本确认；规模、设备及工艺差异需核查。当前二厂明细为按汇总校准的合成演示数据，结构结论仅用于演示。'
        benchmark_missing=['二厂真实经营明细（现有为合成演示明细）','相同口径设备利用率与批次工艺记录']
    else:
        # 2026-09-22 起默认停用合成明细：二厂只有题包成本汇总口径，拆结构到
        # 要素层为止，原材料下钻缺失按"证据支持假设/证据不足"合同输出归因推测。
        benchmark_hypothesis='跨厂成本差异已由同规格月度成本与三要素汇总口径确认；规模、设备及工艺差异需核查。二厂缺少原材料/费用等经营明细，结构归因仅到要素层，更深层原因以证据支持假设表述、不认定因果。'
        benchmark_missing=['二厂原材料消耗与制造费用明细（当前仅有成本汇总口径）','相同口径设备利用率与批次工艺记录']
    return {'analysis_type':analysis_type,'period':a['period'],'direction':f'{left}−{right}，以{right}为分母','product':product,'month':month,'left':left,'right':right,
            'snapshot_ids':[a['snapshot_id'],b['snapshot_id']], 'summary':summary,'elements':elements,
            'details':{'left':a['details'],'right':b['details']},
            'hypotheses':[{'claim_type':'hypothesis','hypothesis':benchmark_hypothesis,
              'metric_refs':[a['metrics']['unit_cost']['metric_id'],b['metrics']['unit_cost']['metric_id']],
              'evidence_refs':[],'missing_evidence':benchmark_missing,
              'suggestion':'先核对两厂归集口径与真实明细；生产/GMP变更需人工批准。'}],
            'limits':['总成本对比受产量影响，不能作为单位效率结论','文档原因证据由报告检索流程补充；仅表内数值不能证明因果']}


def benchmark_analysis(product,month,left=None,right=None,analysis_type='monthly'):
    """Package already-calculated cross-factory metrics for constrained generation."""
    left,right=_benchmark_factories(left,right)
    comparison=benchmark(product,month,left,right,analysis_type)
    snapshot=analyze(left,product,month,analysis_type)
    right_snapshot=analyze(right,product,month,analysis_type)
    for row in comparison['summary']+comparison['elements']:
        key=row['key'];base=snapshot['metrics'][key]
        row['metric_refs'] = {}
        for field,unit in [('delta',row.get('unit','元/盒')),('rate','%')] + ([('contribution','%')] if 'contribution' in row else []):
            metric_id=f"benchmark:{left}:{right}:{product}:{month}:{key}:{field}"
            value=row[field]
            row['metric_refs'][field] = metric_id
            snapshot['metrics'][metric_id]={**base,'metric_id':metric_id,'label':comparison['direction']+' '+row['name']+{'rate':'差异率','delta':'差异金额','contribution':'占跨厂单位成本差额'}[field],'value':value,'display':'N/A' if value is None else format(D(value).quantize(D('0.01')),'f'),'unit':unit,'formula':{'rate':'(左厂−右厂)/右厂×100','delta':'左厂−右厂','contribution':'要素跨厂差额/单位成本跨厂总差额×100'}[field],'numerator':row['delta'],'denominator':row['right'] if field=='rate' else row['denominator'] if field=='contribution' else '1','comparison_period':comparison['period'],'row_keys':base['row_keys']+right_snapshot['metrics'][key]['row_keys'],'source_hash':sorted(set(base['source_hash']+right_snapshot['metrics'][key]['source_hash']))}
    snapshot['benchmark_context']={k:comparison[k] for k in ('left','right','direction','summary','elements','limits','period')}
    snapshot['snapshot_id']=hashlib.sha256(json.dumps(snapshot,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return snapshot,comparison
