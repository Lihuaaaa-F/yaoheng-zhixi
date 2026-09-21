"""原 Word 模板的 XML 定位绑定、保留 run 样式、逐任务 PDF 转换。"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
import hashlib, json, os, re, shutil, subprocess, tempfile
from datetime import datetime
from decimal import Decimal
from .config import ROOT, PACKAGE, ARTIFACTS
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
PATTERN = re.compile(r'\{\{([^{}]+)\}\}')
RESIDUAL = re.compile(r'\{\{[^{}]*\}\}|\[\[[^\[\]]*\]\]')
# 工作模板（由赛题原件规范化生成）默认落在仓库 04_方案与文档/；
# 容器与只读部署用 PHARMA_TEMPLATE_DIR 指向可写持久目录。
_TEMPLATE_DIR = Path(os.environ.get('PHARMA_TEMPLATE_DIR', str(ROOT / '04_方案与文档')))
TEMPLATE = _TEMPLATE_DIR / '月度成本分析报告工作模板.docx'
MAP_PATH = _TEMPLATE_DIR / 'placeholder_map.json'
RENDERER_VERSION='reader-20260921-template-v7'
NA = 'N/A（无可用基期或明细）'

def replace_text_nodes(nodes, mapping):
    """Replace split-run tokens without assigning paragraph.text or removing runs."""
    text = ''.join(n.text or '' for n in nodes)
    spans = []; pos = 0
    for n in nodes:
        size = len(n.text or ''); spans.append((pos, pos + size, n)); pos += size
    for match in reversed(list(PATTERN.finditer(text))):
        if match.group(1) not in mapping:
            continue
        start, end = match.span(); replacement = str(mapping[match.group(1)])
        touched = [(a,b,n) for a,b,n in spans if b > start and a < end]
        for index, (a,b,n) in enumerate(touched):
            old = n.text or ''; n.text = old[:max(0,start-a)] + (replacement if index == 0 else '') + old[min(len(old),end-a):]
            n.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')

def binding_semantics(field,ratio=False):
    metadata={'报告标题':'report.title','报告类型':'analysis_type','分析月份':'period','产品名称':'product','产品规格':'specification','编制日期':'report.created_at'}
    if field in metadata:return metadata[field],'文本/日期'
    dynamic={'原材料成本明细表格':'details.materials','近6个月成本趋势表格':'trend','原材料价格跟踪表格':'details.market','对标差异表格':'benchmark.summary/elements','改进建议表格':'narrative.findings.suggestion','整改任务表格':'narrative.findings.suggestion + actions.confirmation'}
    if field in dynamic:return dynamic[field],'表格列各自定义'
    if field=='合计贡献度':return 'period_changes.unit_cost.mom.delta -> defined contribution','%'
    if any(x in field for x in ['分析文本','归因','排查','拆解','亮点','问题','变动说明']):return 'narrative.findings + evidence.location','文本'
    period='budget' if '预算' in field else 'yoy' if '去年' in field else 'mom' if '上月' in field else 'current'
    metric='quantity' if '产量' in field else 'total_cost' if '总成本' in field else 'unit_cost'
    if any(x in field for x in ['工时','时薪','效率']):
        key=next(k for cn,k in [('工时','hours_per_10000'),('时薪','hourly_wage'),('效率','efficiency')] if cn in field)
        return 'labor_metrics.'+('rates' if ratio else period)+'.'+key, '%' if ratio else {'hours_per_10000':'h/万盒','hourly_wage':'元/h','efficiency':'盒/人·日'}[key]
    for cn,key in [('折旧','折旧费'),('动力','动力费'),('间接人工','间接人工费'),('检验','检验费'),('其他','其他制造费用')]:
        if cn in field:return 'expenses_summary['+key+'].'+('rate' if ratio else 'previous' if period=='mom' else 'current'),'%' if ratio else '元/盒'
    for cn,key in [('材料','materials'),('人工','labor'),('制造费用','overhead')]:
        if cn in field:
            value='unit_contribution' if '贡献度' in field else 'share' if '占比' in field else 'budget_rate' if '预算偏差' in field else 'unit_mom' if ratio else 'unit_delta' if '环比' in field else 'previous_unit' if period=='mom' else 'budget_unit' if period=='budget' else 'unit'
            return 'elements['+key+'].'+value,'%' if ratio else '元/盒'
    if ratio:
        comparison='budget' if '预算' in field else 'yoy' if '同比' in field else 'mom'
        return 'period_changes.'+metric+'.'+comparison+'.rate','%'
    if field=='总环比':return 'period_changes.unit_cost.mom.delta','元/盒'
    return 'period_values.'+period+'.'+metric,'盒' if metric=='quantity' else '元' if metric=='total_cost' else '元/盒'

def normalize_template(output=TEMPLATE, map_path=MAP_PATH):
    # 跳过 Word 锁文件（~$ 前缀）并按名排序保证选择稳定（2026-09-21：容器内锁文件曾致 BadZipFile）
    original = next(p for p in sorted((PACKAGE / '04_报告模板').glob('*.docx')) if not p.name.startswith('~$'))
    entries=[]; original_names=[]
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    with ZipFile(original) as zin, ZipFile(output,'w',ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            raw=zin.read(info.filename)
            if info.filename.startswith('word/') and info.filename.endswith('.xml'):
                xml=ET.fromstring(raw)
                for i,p in enumerate(xml.findall('.//w:p',NS)):
                    nodes=p.findall('.//w:t',NS);text=''.join(t.text or '' for t in nodes)
                    rename={}
                    if info.filename=='word/document.xml' and i==235 and text=='100%':
                        nodes[0].text='{{合计贡献度}}%'
                        for n in nodes[1:]:n.text=''
                        text='{{合计贡献度}}%'
                    marker='YH_'+hashlib.sha256(info.filename.encode()).hexdigest()[:8]+'_'+str(i)
                    if PATTERN.search(text):
                        mark=ET.Element('{'+W+'}bookmarkStart',{'{'+W+'}id':str(10000+i),'{'+W+'}name':marker});p.insert(0,mark)
                        p.append(ET.Element('{'+W+'}bookmarkEnd',{'{'+W+'}id':str(10000+i)}))
                    for match in PATTERN.finditer(text):
                        name=match.group(1)
                        if name!='合计贡献度':original_names.append(name)
                        ratio=text[match.end():].lstrip().startswith('%')
                        field=name+'_'+('比例' if ratio else '金额') if name in ('人工环比','制造费用环比') else name
                        rename[name]='{{'+field+'}}'
                        entries.append({'original':name,'field':field,'xml_part':info.filename,'paragraph_index':i,'marker':marker,'context':text,'unit':binding_semantics(field,ratio)[1],'source':binding_semantics(field,ratio)[0],'missing_policy':'N/A并说明缺值原因','semantic':name+('变动率' if ratio else '')})
                    replace_text_nodes(nodes,rename)
                # 2026-09-21 真人评审四轮（用户裁定）：模板水印与页眉装饰完整保留，不再剥离。
                raw=ET.tostring(xml,encoding='utf-8',xml_declaration=True)
            zout.writestr(info,raw)
    result={'original_hash':hashlib.sha256(original.read_bytes()).hexdigest(),'template_hash':hashlib.sha256(output.read_bytes()).hexdigest(),'original_unique':len(set(original_names)),'original_occurrences':len(original_names),'placeholders':entries}
    Path(map_path).write_text(json.dumps(result,ensure_ascii=False,indent=2))
    compact_working_template(output, map_path)
    return json.loads(Path(map_path).read_text())

def number(value, digits=2):
    if isinstance(value,dict):value=value.get('value')
    if value is None:return NA
    try:
        exact=Decimal(str(value))
        if digits==2 and exact!=0 and abs(exact)<Decimal('0.005'):digits=4
        return f'{exact:.{digits}f}'
    except Exception:return str(value)

def _text(paragraph, old, new):
    nodes=list(paragraph._p.iter('{'+W+'}t'))
    # Fixed template prose is replaced with the same run-preserving algorithm.
    combined=''.join(n.text or '' for n in nodes)
    if old not in combined:return
    if nodes:
        nodes[0].text=combined.replace(old,new)
        for n in nodes[1:]:n.text=''

def rewrite_template_prose(paragraph, replacements):
    """Rewrite only static template text before inserting bound user/model values.

    Placeholder ranges remain untouched even when their names contain the same
    words as a label; existing runs and bookmarks retain their positions.
    """
    nodes=list(paragraph._p.iter('{'+W+'}t'))
    for old,new in replacements:
        text=''.join(n.text or '' for n in nodes)
        protected=[m.span() for m in RESIDUAL.finditer(text)]
        spans=[];pos=0
        for node in nodes:
            size=len(node.text or '');spans.append((pos,pos+size,node));pos+=size
        for match in reversed(list(re.finditer(re.escape(old),text))):
            start,end=match.span()
            if any(start<b and end>a for a,b in protected):continue
            touched=[(a,b,n) for a,b,n in spans if b>start and a<end]
            for index,(a,b,node) in enumerate(touched):
                value=node.text or ''
                node.text=value[:max(0,start-a)]+(new if index==0 else '')+value[min(len(value),end-a):]
                node.set('{http://www.w3.org/XML/1998/namespace}space','preserve')


def _all_paragraphs(doc):
    from docx.text.paragraph import Paragraph
    return [Paragraph(p,doc) for p in doc.element.body.iter('{'+W+'}p')]

def layout_text(text):
    """Remove only the word-joiner inserted for layout, never normalize values."""
    return text.replace('\u2060', '').replace('\ufeff', '').replace('\u00a0', ' ')


def protect_number_units(paragraph):
    """Keep a number and its unit together without destroying runs/bookmarks.

    LibreOffice ignores U+2060 at some CJK template boundaries; U+FEFF is
    its supported zero-width no-break space. This is layout, not recoding."""
    nodes = list(paragraph._p.iter('{'+W+'}t'))
    for node in nodes:
        node.text = layout_text(node.text or '')
    text = ''.join(node.text or '' for node in nodes)
    if RESIDUAL.search(text):
        return
    unit = r'(?:万元|元|kWh|kg|吨|盒|粒|袋|支|件|小时|分钟|万盒|%|％)(?:/(?:kg|吨|盒|粒|袋|支|件|小时|分钟|万盒))?'
    pattern = r'(?<![A-Za-z0-9_.])[-+−]?\d+(?:,\d{3})*(?:\.\d+)?[ \u00a0]*' + unit
    boundaries = set()
    unbreakable_spaces = set()
    for match in re.finditer(pattern, text):
        boundaries.update(range(match.start()+1, match.end()))
        unbreakable_spaces.update(i for i in range(match.start(),match.end()) if text[i]==' ')
    offset = 0
    for node in nodes:
        original = node.text or ''
        node.text = ''.join(('\ufeff' if offset+i in boundaries else '')+('\u00a0' if offset+i in unbreakable_spaces else char) for i,char in enumerate(original))
        offset += len(original)


def report_period_label(snapshot):
    period = snapshot.get('period') or {}
    start, end = period.get('start'), period.get('end')
    return (start if start == end else start+' 至 '+end) if start and end else snapshot.get('month', '期间未提供')


def benchmark_precision(snapshot):
    return 4 if snapshot.get('analysis_type') == 'quarterly' else 2


def benchmark_labels(comparison):
    """Factory identities come from the comparison, including stored snapshots."""
    comparison = comparison or {}
    left, right = comparison.get('left'), comparison.get('right')
    if not left or not right:
        pair = comparison.get('direction', '').partition('，以')[0]
        if '−' in pair:
            left, right = pair.split('−', 1)
    if not left or not right:
        return '比较厂', '基准厂', '未提供比较对象，不能确定差额方向'
    direction = f'{left}−{right}，以{right}为分母'
    if comparison.get('direction') and comparison['direction'] != direction:
        raise ValueError('BENCHMARK_DIRECTION_CONFLICT')
    return left, right, direction


def build_bindings(snapshot,narrative,benchmark=None):
    m=snapshot['metrics']; els={e['key']:e for e in snapshot['elements']}; quarterly=snapshot['analysis_type']=='quarterly'
    period=snapshot.get('period',{}); label=(period.get('start','')+' 至 '+period.get('end','')) if quarterly else snapshot['month']
    values={'报告标题':f"{snapshot['product']} {'季度成本分析' if quarterly else '专题分析' if snapshot['analysis_type']=='special' else '月度成本分析'}报告",'报告类型':{'monthly':'月度成本分析','quarterly':'季度成本分析','special':'专题分析'}[snapshot['analysis_type']],'分析月份':label,'产品名称':snapshot['product'],'产品规格':snapshot.get('specification') or '未提供规格','编制日期':datetime.now().strftime('%Y-%m-%d'),'本月产量':number(m['quantity'],0),'本月单位成本':number(m['unit_cost'],4 if quarterly else 2),'单位成本':number(m['unit_cost'],4 if quarterly else 2),'本月总成本':number(m['total_cost'])}
    # Comparison metric snapshots are the sole source of calculated fields.
    for key,cn in [('mom','单位成本环比'),('yoy','单位成本同比'),('budget','单位成本预算偏差')]:values[cn]=number(m.get(key))
    for key,prefix in [('mom','上月'),('yoy','去年'),('budget','预算')]:
        c=snapshot.get('comparison',{}).get(key,{})
        base=c.get('base')
        values[prefix+'单位成本']=number(base)
    for ekey,cn in [('materials','材料'),('labor','人工'),('overhead','制造费用')]:
        e=els[ekey]
        values.update({f'本月{cn}成本' if cn!='制造费用' else '本月制造费用':number(e['unit']),f'{cn}金额':number(e['unit']),f'{cn}占比':number(e.get('share')),f'{cn}贡献度':number(e.get('contribution')),f'{cn}环比':number(e.get('delta')),f'{cn}环比_金额':number(e.get('unit_delta', e.get('delta'))),f'{cn}环比_比例':number(e.get('unit_mom')),f'{cn}成本环比':number(e.get('unit_mom'))})
        values[f'上月{cn}成本' if cn!='制造费用' else '上月制造费用']=number(e.get('previous_unit'))
    values.update({'人工单位成本':number(els['labor']['unit']),'上月人工单位成本':number(els['labor'].get('previous_unit')),'制造费用合计':number(els['overhead']['unit']),'上月制造费用合计':number(els['overhead'].get('previous_unit')),'制造费用合计环比':number(els['overhead'].get('unit_mom')),'总环比':number(snapshot.get('comparison',{}).get('mom',{}).get('delta'))})
    periods=snapshot.get('period_values',{})
    changes=snapshot.get('period_changes',{})
    for period,prefix in [('mom','上月'),('yoy','去年'),('budget','预算')]:
        base=periods.get(period) or {}
        for key,cn in [('quantity','产量'),('unit_cost','单位成本'),('total_cost','总成本')]:
            values[prefix+cn]=number(base.get(key),0 if key=='quantity' else 2)
        if period=='yoy':values['去年同月产量']=values['去年产量']
    for key,cn in [('quantity','产量'),('unit_cost','单位成本'),('total_cost','总成本')]:
        for period,label in [('mom','环比'),('yoy','同比'),('budget','预算偏差')]:
            values[cn+label]=number(changes.get(key,{}).get(period,{}).get('rate'))
    values['总环比']=number(changes.get('unit_cost',{}).get('mom',{}).get('delta'))
    for ekey,cn in [('materials','材料'),('labor','人工'),('overhead','制造费用')]:
        e=els[ekey]
        values[cn+'贡献度']=number(e.get('unit_contribution',e.get('contribution')))
        values[cn+'环比']=number(e.get('unit_delta'))
        values['预算'+cn+'成本' if cn!='制造费用' else '预算制造费用']=number(e.get('budget_unit'))
        values[cn+'预算偏差']=number(e.get('budget_rate'))
    lm=snapshot.get('labor_metrics',{})
    for k,cn in [('hours_per_10000','工时'),('hourly_wage','时薪'),('efficiency','效率')]:
        values['本月'+cn]=number(lm.get('current',{}).get(k));values['上月'+cn]=number(lm.get('mom',{}).get(k));values[cn+'环比']=number(lm.get('rates',{}).get(k))
    expense_names={'折旧费':'折旧','动力费(水电气)':'动力','动力费':'动力','间接人工':'间接人工','间接人工费':'间接人工','人工(间接)':'间接人工','检验费':'检验','其他制造费用':'其他','其他':'其他'}
    for e in snapshot.get('expenses_summary',[]):
        cn=expense_names.get(e['name'])
        if cn:
            values['本月'+cn]=number(e['current']);values['上月'+cn]=number(e['previous']);values[cn+'环比']=number(e['rate']);values[cn+'变动说明']=e['name']+'变动需核对费用台账及分摊依据' if e['current'] is not None else NA
    for ekey,cn in [('materials','材料'),('labor','人工'),('overhead','制造费用')]:
        values['去年'+cn+'成本' if cn!='制造费用' else '去年制造费用']=number((periods.get('yoy') or {}).get('elements_unit',{}).get(ekey))
        values[cn+'成本同比']=number(els[ekey].get('comparisons',{}).get('yoy',{}).get('unit',{}).get('rate'))
    findings=narrative.get('findings',[])
    def prose(section):
        return '\n'.join(f.get('rendered_text',f.get('text','')) for f in findings if f.get('section')==section and f.get('claim_type') in ('hypothesis','insufficient_evidence'))
    material=els['materials']
    material_text='直接材料每盒 '+number(material['unit'])+' 元，比上期变动 '+number(material.get('unit_delta'))+' 元，占单位成本变动的 '+number(material.get('unit_contribution'))+'%。'
    rows=snapshot.get('materials_summary',[])
    if rows:
        material_text+='\n'+'；'.join(r.get('name','')+'：'+number(r.get('previous'))+' → '+number(r.get('current'))+' 元/盒，变动 '+number(r.get('delta'))+' 元/盒，占材料增量 '+number(r.get('contribution'))+'%' for r in rows[:4])+'。'
    material_text+=' 单位消耗成本同时受价格和实耗影响；需采购入库单、批次领退料及合格产出记录，才能分别核验价格与耗量。'
    values['材料成本归因分析文本']=material_text+'\n'+prose('materials')
    changes=snapshot.get('period_changes',{})
    overview='本期产量 '+number(m['quantity'],0)+' 盒，总成本 '+number(m['total_cost'])+' 元。'
    alerts=snapshot.get('alerts',[])
    alert_text='\n'.join(a['element']+'的'+('单位成本' if a['basis']=='unit' else '总额')+'环比变动 '+number(a['rate'])+'%；'+a['note']+'。' for a in alerts) or '本期三要素没有超过既定阈值的告警；仍应核对主要变动项。'
    bridges=snapshot.get('budget_bridge') or {}
    if bridges.get('quantity_effect') is not None:
        overview+=' 相对预算总成本差额 '+number(bridges.get('total_delta'))+' 元，其中产量影响 '+number(bridges.get('quantity_effect'))+' 元，单位成本影响 '+number(bridges.get('unit_cost_effect'))+' 元；不能全部归为效率恶化。'
    directions=[]
    materials_summary=snapshot.get('materials_summary') or []
    details_market=(snapshot.get('details') or {}).get('market') or []
    month_no=int(snapshot['month'][5:]);prev_key=f'{month_no-1}月价格';cur_key=f'{month_no}月价格'
    if materials_summary:
        top=materials_summary[0];material_delta=Decimal(str(top.get('delta') or '0'))
        mrow=next((r for r in details_market if r.get('药材名称')==top.get('name')),None)
        if mrow and mrow.get(cur_key) not in (None,'','N/A') and mrow.get(prev_key) not in (None,'','N/A'):
            try:
                price_now=Decimal(str(mrow[cur_key]));price_prev=Decimal(str(mrow[prev_key]));price_move=price_now-price_prev
                same_side=(price_move>0)==(material_delta>0)
                verdict=('与材料单位成本变动方向一致，价格传导可能性较高' if same_side else '与材料单位成本变动方向相反，价格传导可能性低，差异更可能来自单耗或批次结构')
                directions.append('材料价格传导：'+str(top.get('name'))+'市场价由上期 '+str(price_prev)+' 变为 '+str(price_now)+' '+str(mrow.get('单位','元/kg'))+'（'+str(mrow.get('价格来源','市场行情'))+'），'+verdict+'。证实或证伪：核对采购合同单价与市场价的偏离、以及批次库存结构。')
            except Exception:pass
        directions.append('单位耗用变化：投料单耗或提取收率变化会直接改变每盒材料成本，与价格因素叠加。证实或证伪：同批次投料记录与合格产出对照上期，计算单耗变动。')
    qdelta=snapshot.get('period_changes',{}).get('quantity',{}).get('mom',{}).get('delta')
    if qdelta is not None and Decimal(str(qdelta))!=0:
        directions.append('产量分摊：产量环比'+('下降' if Decimal(str(qdelta))<0 else '上升')+' '+number(str(qdelta).lstrip('-'))+' 盒，折旧、间接人工等偏固定费用按产量分摊时，单位成本会随产量'+('上升' if Decimal(str(qdelta))<0 else '下降')+'。证实或证伪：核对制造费用分配表使用的产量基数是否与实际产量一致。')
    if directions:
        values['成本异常排查分析']=overview+'\n'+alert_text+'\n'+('归因方向评估（按可能性排序；以下均为待证实假设，供业务判断）：\n'+'\n'.join(str(i)+'. '+d for i,d in enumerate(directions,1)) if directions else overview+'\n'+alert_text)
    values['人工成本归因分析文本']=prose('labor')
    values['制造费用归因分析文本']=prose('overhead')
    be=(benchmark or {}).get('elements',[])
    left,right,direction=benchmark_labels(benchmark)
    values['差异结构拆解分析']=direction+'。'+('；'.join(r['name']+'差额 '+number(r.get('delta'))+' 元/盒，占跨厂单位成本总差额 '+number(r.get('contribution'))+'%' for r in be)+'。' if be else '该期间没有可比跨厂记录。')
    benchmark_details=(benchmark or {}).get('details') or {}
    synthetic_notes=[]
    for side,factory in (('left',left),('right',right)):
        label=(benchmark_details.get(side) or {}).get('data_label')
        if label:synthetic_notes.append(factory+'明细：'+label)
    values['差异归因分析文本']=(prose('benchmark') or '三要素差额用于定位核查重点。请两厂成本会计核对同规格的领料、工时与费用分摊记录。')+('数据边界：'+'；'.join(synthetic_notes)+'。' if synthetic_notes else '')
    # 本月亮点（2026-09-21 修复 #11）：从注册指标与行业分位确定性生成，
    # 不再输出通用管理提示。每条都绑定可核对数字；无显著改善时如实说明。
    highlights=[]
    mom_value=m['mom'].get('value')
    if mom_value is not None and Decimal(str(mom_value))<0:
        highlights.append('单位成本环比下降 '+number(m['mom'])+'%（本期 '+number(m['unit_cost'])+' 元/盒）')
    improving=[e for e in snapshot.get('elements',[]) if e.get('unit_mom') is not None and Decimal(str(e['unit_mom']))<0]
    if improving:
        best=min(improving,key=lambda e:Decimal(str(e['unit_mom'])))
        highlights.append('改善最大的成本要素：'+best['name']+'（单位环比 '+number(str(best['unit_mom']))+'%）')
    for row in ((snapshot.get('industry') or {}).get('rows') or []) if snapshot.get('factory')=='中药一厂' else []:
        if str(row.get('指标',''))=='人工成本占比' and row.get('本厂水平(中药一厂)') and row.get('行业P50'):
            try:
                if Decimal(str(row['本厂水平(中药一厂)']).rstrip('%'))<Decimal(str(row['行业P50']).rstrip('%')):
                    highlights.append('人工成本占比 '+str(row['本厂水平(中药一厂)'])+' 低于行业中位 '+str(row['行业P50'])+'（题包静态参考）')
            except Exception:pass
        if str(row.get('指标',''))=='单位成本(元/粒)' and row.get('本厂水平(中药一厂)') and row.get('行业P50'):
            try:
                if Decimal(str(row['本厂水平(中药一厂)']))<=Decimal(str(row['行业P50'])):
                    highlights.append('单位成本 '+str(row['本厂水平(中药一厂)'])+' 元/粒 不高于行业中位 '+str(row['行业P50'])+'（题包静态参考）')
            except Exception:pass
    values['本月亮点']=('；'.join(highlights)+'。') if highlights else ('本期单位成本 '+number(m['unit_cost'])+' 元/盒，产量 '+number(m['quantity'],0)+' 盒；本期无显著优于基期或行业中位的确定性亮点。')
    values['需关注问题']='原料成本上涨不能直接等同采购价上涨。平均小时工资为题包折算口径，不能据此认定基础薪率上调。跨厂原料差异需核对二厂明细（当前为按汇总校准的合成明细）。'
    delta=changes.get('unit_cost',{}).get('mom',{}).get('delta')
    values['合计贡献度']='100.00' if delta is not None and Decimal(delta)!=0 else 'N/A（总变动为0或无基期）'
    return values

def sanitize_template_identity(doc):
    """Replace author/reviewer metadata and decorative textbox branding by role.

    The original template stays read-only. No original personal name or company
    string is needed in source code to sanitize a working report.
    """
    # 模板 md 规定的固定值（2026-09-21 真人评审三轮：模板已显示的以模板为准）
    labels = {'编制人': '财务部成本会计', '审核人': '财务总监',
              '编制单位': '中药一厂 财务部', '企业名称': '中药一厂', '数据来源': 'ERP系统成本模块'}
    for table in doc.tables:
        for row in table.rows:
            for index, cell in enumerate(row.cells[:-1]):
                if cell.text.strip().rstrip('：:') in labels:
                    target = row.cells[index+1]
                    value = labels[cell.text.strip().rstrip('：:')]
                    if target.paragraphs:
                        _text(target.paragraphs[0], target.paragraphs[0].text, value)
                        for paragraph in target.paragraphs[1:]:
                            _text(paragraph, paragraph.text, '')
    parts = [doc.part] + [section.header.part for section in doc.sections] + [section.footer.part for section in doc.sections]
    for part in parts:
        # 2026-09-21 四轮（用户裁定）：模板水印文字原样保留，不再改写。
        pass
    doc.core_properties.author = '药衡智析演示团队'
    doc.core_properties.last_modified_by = '药衡智析'


def insert_element_analysis(doc, snapshot, bindings):
    elements = {e['key']: e for e in snapshot['elements']}
    descriptions = [
        ('3.3', 'labor', '人工成本归因分析文本', '平均小时工资是题包折算口径。每盒人工费用受工时、人员组成及加班影响；需核对工时台账、工资组成与返工记录，不能认定基础薪率上涨。'),
        ('四、', 'overhead', '制造费用归因分析文本', '按费用台账和分配基数检查变化。维修事件只有在产品、期间及入账范围一致时才用于本期解释；不得将维修金额重复计入总成本。')]
    for prefix, key, binding, caution in descriptions:
        anchor = next((p for p in doc.paragraphs if p.text.startswith(prefix)), None)
        if anchor is None:
            raise ValueError('MISSING_COST_SECTION:'+key)
        element = elements[key]
        anchor.insert_paragraph_before(element['name']+'每盒 '+number(element['unit'])+' 元，比上期变动 '+number(element.get('unit_delta'))+' 元，占单位成本环比变动 '+number(element.get('unit_contribution'))+'%。'+caution)
        if bindings.get(binding):
            anchor.insert_paragraph_before(bindings[binding])


def explanation_presence(path, narrative, scoped=True):
    """Only body prose in its required section can satisfy a model explanation."""
    from docx import Document
    paragraphs = Document(path).paragraphs
    by_section = {};section = None
    for paragraph in paragraphs:
        text = layout_text(paragraph.text)
        for prefix, target in [('3.1', 'materials'), ('3.2', 'labor'), ('3.3', 'overhead'), ('5.3', 'benchmark')]:
            if text.startswith(prefix):section=target;break
        else:
            if re.match(r'^[一二三四五六]、|^[2456]\.',text):section=None
        if section:
            by_section.setdefault(section,[]).append(text)
    all_body = [layout_text(p.text) for p in paragraphs]
    failures=[];checked=0
    for index,finding in enumerate((narrative or {}).get('findings',[])):
        if finding.get('origin') not in ('model','llm') or finding.get('claim_type') not in ('hypothesis','insufficient_evidence'):
            continue
        checked+=1
        expected=layout_text(finding.get('rendered_text') or finding.get('text',''))
        candidates=by_section.get(finding.get('section'),[]) if scoped else all_body
        if not expected or not any(expected in text for text in candidates):
            failures.append({'finding':index,'section':finding.get('section'),'reason':'MODEL_EXPLANATION_MISSING_FROM_BODY'})
    return {'explanation_bindings_checked':checked,'explanation_binding_failures':failures}


def render_docx(snapshot,narrative,evidence,output,benchmark=None):
    if snapshot.get('context_id') and snapshot['context_id']!='pharmaceutical:competition':
        from .reference_report import render
        result=render(snapshot,narrative,evidence,output,benchmark)
        check=verify_docx(output,snapshot,narrative=narrative)
        if check['status']!='PASS':raise ValueError('REPORT_EXPLANATION_BINDING_FAILED')
        result['verification']=check
        return result
    from docx import Document
    from .narrative import render_visible_text
    narrative=json.loads(json.dumps(narrative))
    for finding in narrative.get('findings',[]):
        for field in ('rendered_text','suggestion','verification_target','responsible_role','deadline_basis','department'):
            if finding.get(field):finding[field]=render_visible_text(finding[field],snapshot,evidence.get('evidence',[]),finding.get('metric_refs',[]),finding.get('evidence_quotes'))
        finding['expected_evidence']=[render_visible_text(x,snapshot,evidence.get('evidence',[]),finding.get('metric_refs',[])) for x in finding.get('expected_evidence',[])]
    from docx.shared import Inches, Pt
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    if not TEMPLATE.exists():normalize_template()
    elif json.loads(MAP_PATH.read_text()).get('reader_template_version') not in ('reader-v2','reader-v3-truetype'):compact_working_template(TEMPLATE,MAP_PATH)
    meta=json.loads(MAP_PATH.read_text());doc=Document(TEMPLATE)
    sanitize_template_identity(doc)
    values=build_bindings(snapshot,narrative,benchmark)
    for entry in meta['placeholders']:values.setdefault(entry['field'], NA)
    dynamic={k for k in values if '表格' in k}
    for k in dynamic:values[k]='' # tables are inserted at their actual block, below
    sections=[]; dynamic_anchors={}
    for p in _all_paragraphs(doc):
        before=p.text
        for field in dynamic:
            if '{{'+field+'}}' in before:dynamic_anchors[field]=p
        # 2026-09-21 真人评审三轮：模板已显示的文字一律原样保留（整体解决方案/
        # ERP系统成本模块/财务总监等不再改写）；仅保留跨厂厂名的动态替换与
        # 季度口径词替换（模板未覆盖的场合）。
        replacements=[]  # 模板文字一律原样；跨厂方向已在 5.2/5.3 与图表说明中呈现
        if snapshot['analysis_type']=='quarterly':
            replacements += [('本月','本季度'),('上月','上季度'),('去年同月','去年同期季度'),('分析月份','分析期间')]
        rewrite_template_prose(p,replacements)
        replace_text_nodes(list(p._p.iter('{'+W+'}t')),values)
        if 'N/A' in p.text:_text(p,'）%','）')
        if before.startswith(('一、','二、','三、','四、','五、','六、')):sections.append(p.text)
    for section in doc.sections:
        for part in [section.header,section.footer]:
            for p in part.paragraphs:
                replace_text_nodes(list(p._p.iter('{'+W+'}t')),values)
            pg=section._sectPr.find(qn('w:pgNumType'))
            if pg is not None:pg.attrib.pop(qn('w:start'),None)
    def table(anchor,headers,rows):
        from docx.oxml import OxmlElement as _OE
        from docx.oxml.ns import qn as _qn
        from docx.enum.text import WD_ALIGN_PARAGRAPH as _TA
        p=dynamic_anchors.get(anchor)
        if p is None:raise ValueError('模板动态块缺失:'+anchor)
        t=doc.add_table(rows=1,cols=len(headers))
        if doc.tables[0].style:t.style=doc.tables[0].style
        for cell,label in zip(t.rows[0].cells,headers):cell.text=str(label)
        for row in rows or [['N/A：无可用明细']+['—']*(len(headers)-1)]:
            for cell,val in zip(t.add_row().cells,row):cell.text=str(val if val is not None else NA)
        p._p.addnext(t._tbl)
        # 模板表格外观（2026-09-21 四轮 E 项）：黑色细边框 + 灰底(D9D9D9)表头 +
        # 表头加粗居中；数据行首列左对齐、数值列居中；长表允许跨页（表头重复）。
        borders=_OE('w:tblBorders')
        for edge in ('top','left','bottom','right','insideH','insideV'):
            e=_OE('w:'+edge);e.set(_qn('w:val'),'single');e.set(_qn('w:sz'),'4');e.set(_qn('w:color'),'000000');borders.append(e)
        t._tbl.tblPr.append(borders)
        allow_split=len(t.rows)>12
        for i,row in enumerate(t.rows):
            trpr=row._tr.get_or_add_trPr()
            if i==0 and trpr.find(_qn('w:tblHeader')) is None:trpr.append(_OE('w:tblHeader'))
            if not allow_split and trpr.find(_qn('w:cantSplit')) is None:trpr.append(_OE('w:cantSplit'))
            for cell in row.cells:
                cell.vertical_alignment=1
                if i==0:
                    pr=cell._tc.get_or_add_tcPr();shd=_OE('w:shd');shd.set(_qn('w:fill'),'D9D9D9');pr.append(shd)
                for j,pp in enumerate(cell.paragraphs):
                    pp.alignment=_TA.CENTER if i==0 else (_TA.LEFT if j==0 and len(headers)>=4 else _TA.CENTER)
                    for r in pp.runs:r.font.size=Pt(9);r.font.bold=(i==0)
        return t
    details=snapshot.get('details',{})
    def generic_rows(items):
        if not items:return []
        return [[str(k),str(v)] for item in items for k,v in item.items() if not k.startswith('_') and k not in ('source_hash','row_key')]
    # 3.1.1 列结构按模板 md：序号/原材料名称/本月单价/上月单价/环比变动/变动原因初步判断
    _ms=snapshot.get('materials_summary') or []
    _ms_map={str(r.get('name')):r for r in _ms}
    def _prev(name):
        v=_ms_map.get(name,{}).get('previous')
        return str(v) if v not in (None,'') else '—'
    def _delta_pct(name):
        v=_ms_map.get(name,{}).get('delta')
        try:return ('+' if float(v)>0 else '')+f'{float(v):.2f}%'
        except Exception:return '—'
    def _reason(name):
        c=_ms_map.get(name,{}).get('contribution')
        return ('贡献材料变动 '+str(c)+'%，优先核查' if c is not None else '待核查（见4.2方向评估）')
    table('原材料成本明细表格',['序号','原材料名称','本月单价(元/盒)','上月单价(元/盒)','环比变动','变动原因初步判断'],[[
        str(i+1),r['原材料名称'],r['单位消耗成本(元/盒)'],_prev(r['原材料名称']),_delta_pct(r['原材料名称']),_reason(r['原材料名称'])]
        for i,r in enumerate(details.get('materials',[]))])
    # 4.1 列结构按模板 md：月份/产量/三要素单位/单位成本/环比变动
    from decimal import Decimal as _Dec
    _trend=snapshot['trend'];_rows_t=[]
    for i,r in enumerate(_trend):
        rate='—'
        try:
            if i>0:
                prev=_Dec(str(_trend[i-1]['unit_cost']));cur=_Dec(str(r['unit_cost']))
                rate=('+' if cur>=prev else '')+f'{float((cur-prev)/prev*100):.2f}%'
        except Exception:rate='—'
        _rows_t.append([r['month'],number(r.get('quantity'),0),number(r.get('materials')),number(r.get('labor')),number(r.get('overhead')),number(r.get('unit_cost')),rate])
    table('近6个月成本趋势表格',['月份','产量(盒)','单位材料(元/盒)','单位人工(元/盒)','单位制造费用(元/盒)','单位成本(元/盒)','环比变动'],_rows_t)
    # 4.3 列结构按模板 md：原材料/年初价/本月价/涨幅/市场趋势/对材料成本影响
    from decimal import Decimal as _Dc
    _mo=int(snapshot['month'][5:]);_ms_names={str(x.get('name')) for x in _ms}
    _rows_m=[]
    for r in details.get('market',[]):
        first=r.get('1月价格','—');cur=r.get(str(_mo)+'月价格','—')
        try:chg=f'{float((_Dc(str(cur))-_Dc(str(first)))/_Dc(str(first))*100):+.1f}%'
        except Exception:chg='—'
        impact=('主要材料，价格变动直接影响单位材料成本' if r['药材名称'] in _ms_names else '行情波动间接影响材料成本')
        _rows_m.append([r['药材名称'],first,cur,chg,str(r.get('趋势分析','—')),impact])
    table('原材料价格跟踪表格',['原材料','年初价','本月价','涨幅','市场趋势','对材料成本影响'],_rows_m)
    # 5.1 列结构按模板 md：对比维度/两厂/差异金额/差异率/方向
    _bl,_br,_bd=benchmark_labels(benchmark)
    _rows_b=[[r.get('name','单位成本'),number(r.get('left'),benchmark_precision(snapshot)),number(r.get('right'),benchmark_precision(snapshot)),number(r.get('delta'),benchmark_precision(snapshot)),number(r.get('rate')),
              ((_bl+'较高') if (r.get('delta') is not None and float(r['delta'])>0) else (_br+'较高') if r.get('delta') is not None else '—')]
             for r in (benchmark or {}).get('summary',[])[:1]+(benchmark or {}).get('elements',[])]
    table('对标差异表格',['对比维度',_bl,_br,'差异金额','差异率','方向'],_rows_b)
    # 建议去重（2026-09-21 修复 #11）：模型建议与确定性回退建议可能同主题
    # 重复（实测 8 条中 4 条主题重复）。按核查对象 + 建议文本二元组相似度
    # （字符二元组 Jaccard ≥0.6）去重；模型来源优先保留，纯规则来源仅补缺。
    def _shingles(text):
        cleaned=re.sub(r'[^\u4e00-\u9fff0-9a-zA-Z]','',str(text))
        return {cleaned[i:i+2] for i in range(max(len(cleaned)-1,0))}
    actionable=[];seen_targets=set();seen_sigs=[]
    candidates=[f for f in narrative.get('findings',[]) if f.get('suggestion','').strip()]
    candidates.sort(key=lambda f:f.get('origin')=='rules')  # 模型来源在前，同主题保留模型版
    for f in candidates:
        sig=_shingles(f.get('suggestion',''))
        target=f.get('verification_target','') or None  # 空核查对象不作为合并键，避免误删不同建议
        duplicate=(target is not None and target in seen_targets
                   or any(sig and s and len(sig&s)/len(sig|s)>=0.6 for s in seen_sigs))
        if duplicate:continue
        if target is not None:seen_targets.add(target)
        seen_sigs.append(sig);actionable.append(f)
    # 6.3 列结构按模板 md：序号/建议事项/责任部门/优先级/预期效果/建议完成时间
    table('改进建议表格',['序号','建议事项','责任部门','优先级','预期效果','建议完成时间'],[[
        str(i+1),f.get('suggestion','待补'),(f.get('department') or '责任部门待定'),
        {'high':'高','medium':'中','low':'低'}.get(f.get('priority'),'中'),
        '、'.join((f.get('expected_evidence') or ['核查对象的原始记录'])[:2]),
        (f.get('deadline_basis') or '下次成本复核前，具体日期由责任部门确认')]
        for i,f in enumerate(actionable)])
    # 6.4 列结构按模板 md：任务编号/任务标题/责任人/优先级/来源/截止时间
    table('整改任务表格',['任务编号','任务标题','责任人','优先级','来源','截止时间'],[[
        'YH-'+hashlib.sha256((f.get('suggestion','')+str(i)).encode()).hexdigest()[:8],
        f.get('verification_target','核查任务'),
        (f.get('responsible_role') or '待分配'),
        {'high':'高','medium':'中','low':'低'}.get(f.get('priority'),'中'),
        '本报告'+str(i+1)+'号建议',
        (f.get('deadline_basis') or '下次成本复核前，由责任部门确认日期')+'（确认后经模拟RPA发送）']
        for i,f in enumerate(actionable)])
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    insert_element_analysis(doc,snapshot,values)
    add_reader_charts(doc,snapshot,benchmark,dynamic_anchors,output)
    add_reader_summary(doc,snapshot,narrative,output)
    # 编制说明与知识库引用（模板 md 尾部要求；引用位置取自本期检索证据）
    doc.add_paragraph('编制说明')
    doc.add_paragraph('本报告由成本智能分析系统自动生成，数据来源于ERP系统，分析文本由AI大模型结合行业知识库自动撰写。如有疑问请联系财务部。')
    doc.add_paragraph('数据说明：本报告使用比赛模拟数据。事实、原因假设与缺失证据分别标注；整改任务确认后仅模拟发送。')
    doc.add_paragraph('知识库引用')
    def _kb_ref(keyword,default_doc):
        for e in evidence.get('evidence',[]):
            src=str(e.get('source') or e.get('source_file') or '')
            if keyword in src:
                loc=('第'+str(e.get('page'))+'页') if e.get('page') else str(e.get('location') or '见文档')
                return src+'（'+loc+'）'
        return default_doc+'（本期未检索到适用段落，待核）'
    doc.add_paragraph('产品配方：'+_kb_ref('配方','产品配方文档（题包03_制药知识文档）'))
    doc.add_paragraph('工艺路线：'+_kb_ref('工艺','生产工艺文档_中药一厂.pdf'))
    doc.add_paragraph('GMP要求：'+_kb_ref('GMP','药品生产质量管理规范GMP.pdf / GMP法规核心摘要'))
    doc.add_paragraph('行业基准：'+_kb_ref('基准','行业成本基准数据_2026（题包02_行业参考数据）'))
    doc.add_paragraph('来源与审核说明')
    doc.add_paragraph('数据来源：成本汇总表、原材料明细表、人工与制造费用表 · '+snapshot['product']+' · '+snapshot['factory']+' · '+report_period_label(snapshot)+'。金额以元、单位成本以元/盒计；季度按产量加权。')
    source_map={e['evidence_id']:e for e in evidence.get('evidence',[])}
    used=set()
    doc.add_paragraph('正文引用的证据来源（位置可回溯）：')
    for f in narrative.get('findings',[]):
        for ref in f.get('evidence_refs',[]):
            if ref in source_map and ref not in used:
                e=source_map[ref];doc.add_paragraph('· '+readable_source(e));used.add(ref)
    # 检索证据全量清单（2026-09-21 修复 #11）：附录不再只列被引用的 3 条，
    # 未被正文引用的候选证据也按文档列出（引用与否不代表因果证实）。
    uncovered=[e for e in evidence.get('evidence',[]) if e['evidence_id'] not in used]
    if uncovered:
        doc.add_paragraph('本期检索到但未被正文直接引用的证据（候选依据 '+str(len(uncovered))+' 条）：')
        for e in uncovered[:12]:
            doc.add_paragraph('· '+readable_source(e))
        if len(uncovered)>12:
            doc.add_paragraph('· ……其余 '+str(len(uncovered)-12)+' 条见机器审计附件。')
    doc.add_paragraph('人工归因评分：待评（0—5分）；内容可读性与逐页版式：待人工审核。引用只说明依据来源，不等于已证实因果。')
    style_reader(doc)
    audit=output.with_name('machine_audit.json')
    audit.write_text(json.dumps({'snapshot':snapshot,'narrative':narrative,'evidence':evidence,'benchmark':benchmark,'bindings':values},ensure_ascii=False,indent=2))
    temp=output.with_suffix('.tmp.docx');doc.save(temp)
    check=verify_docx(temp,snapshot,sections,narrative=narrative)
    if check['status']!='PASS':raise ValueError('报告验证失败:'+json.dumps(check,ensure_ascii=False))
    temp.replace(output)
    return {'status':'PASS','scope':'file_generation','path':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'verification':check,'bindings':values}

def verify_docx(path,snapshot,sections=None,narrative=None):
    if snapshot.get('context_id') and snapshot['context_id']!='pharmaceutical:competition':
        from .reference_report import verify
        result=verify(path,snapshot)
        result.update(explanation_presence(path,narrative,scoped=False))
        if result['explanation_binding_failures']:result['status']='FAIL'
        return result
    explanation_check=explanation_presence(path,narrative)
    with ZipFile(path) as z:
        strings=[]
        for n in z.namelist():
            if n.startswith('word/') and n.endswith('.xml'):
                xml=ET.fromstring(z.read(n));strings.append(''.join(t.text or '' for t in xml.iter('{'+W+'}t')))
        text=layout_text('\n'.join(strings))
        numeric_bindings=build_bindings(snapshot,{})
        by_marker={}
        for n in z.namelist():
            if n.startswith('word/') and n.endswith('.xml'):
                xml=ET.fromstring(z.read(n))
                for p in xml.findall('.//w:p',NS):
                    actual=layout_text(''.join(t.text or '' for t in p.findall('.//w:t',NS)))
                    for mark in p.findall('w:bookmarkStart',NS):by_marker[mark.get('{'+W+'}name')]=actual
        failures=[];checked=0
        for entry in json.loads(MAP_PATH.read_text())['placeholders']:
            field=entry['field'];value=numeric_bindings.get(field)
            if value is None or not (re.match(r'^-?\d',str(value)) or str(value).startswith('N/A')) or field=='编制日期':continue
            expected=entry['context'].replace('{{'+entry['original']+'}}',str(value))
            if 'N/A' in expected:expected=expected.replace('）%','）')
            actual=by_marker.get(entry.get('marker'))
            checked+=1
            if actual!=layout_text(expected):failures.append({'field':field,'expected':expected,'actual':actual})
        duplicated_units=bool(re.search(r'元/盒元/盒|%%|盒盒',text))
        residual=RESIDUAL.findall(text)
        headings=[s for s in ['一、封面与基本信息','二、总成本概览','三、成本要素明细分析','四、重点产品专项分析','五、对标分析','六、总结与建议'] if s in text]
        numeric=number(snapshot['metrics']['unit_cost'],4 if snapshot['analysis_type']=='quarterly' else 2) in text and number(snapshot['metrics']['total_cost']) in text
        tables=sum(1 for _ in ET.fromstring(z.read('word/document.xml')).iter('{'+W+'}tbl'))
        images=len([n for n in z.namelist() if n.startswith('word/media/')])
    return {'status':'PASS' if not explanation_check['explanation_binding_failures'] and not residual and len(headings)==6 and numeric and tables>=11 and images>0 and not failures and checked>=70 and not duplicated_units else 'FAIL',**explanation_check,'numeric_bindings_checked':checked,'numeric_binding_failures':failures,'duplicated_units':duplicated_units,'residual_placeholders':residual,'headings':headings,'core_numbers':numeric,'tables':tables,'images':images,'semantic_bindings':'XML位置区分金额与比例','human_layout':'待全部页人工审核','scope':'文件结构与指标绑定；不是报告验收'}

def convert_pdf(docx_path,timeout=90,converter='libreoffice',_toc_pass=0):
    import os
    path=Path(docx_path)
    try:
        exe = shutil.which(converter)
        if exe is None and converter == 'libreoffice' and os.name == 'nt':
            for candidate in ('soffice', r'C:\Program Files\LibreOffice\program\soffice.exe', r'C:\Program Files (x86)\LibreOffice\program\soffice.exe'):
                found = shutil.which(candidate) if not candidate.startswith('C:') else (candidate if Path(candidate).exists() else None)
                if found: exe = found; break
        if exe is None: return {'status': 'FAILED', 'reason': 'CONVERTER_NOT_FOUND: ' + converter}
        temp_root = '/tmp' if os.name != 'nt' else tempfile.gettempdir()
        with tempfile.TemporaryDirectory(prefix='pharma-lo-',dir=temp_root) as work:
            folder=Path(work);profile=folder/'profile';target=folder/path.with_suffix('.pdf').name
            from xml.sax.saxutils import escape
            font_config=folder/'fonts.conf'
            font_config.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><include ignore_missing="yes">/etc/fonts/fonts.conf</include><dir>'+escape(str(ROOT/'05_原型/assets/fonts'))+'</dir><cachedir>'+escape(str(folder/'font-cache'))+'</cachedir></fontconfig>')
            env={**os.environ,'TMPDIR':'/tmp','XDG_RUNTIME_DIR':work,'FONTCONFIG_FILE':str(font_config)}
            result=subprocess.run([exe,f'-env:UserInstallation={profile.as_uri()}','--headless','--convert-to','pdf','--outdir',work,str(path)],capture_output=True,text=True,timeout=timeout,env=env)
            if result.returncode or not target.exists():return {'status':'FAILED','reason':'CONVERSION_FAILED','log':result.stderr[-1000:]}
            import fitz
            with fitz.open(target) as doc:
                text=''.join(p.get_text() for p in doc);pages=len(doc)
                page_map={};orphan_headings=[]
                headings=['一、封面与基本信息','二、总成本概览','三、成本要素明细分析','四、重点产品专项分析','五、对标分析','六、总结与建议']
                for index,page in enumerate(doc,1):
                    lines=page.get_text().splitlines()
                    meaningful=[line.strip() for line in lines if line.strip() and not re.match(r'^第\s*\d+\s*页',line.strip())]
                    if meaningful and (re.match(r'^[一二三四五六]、|^[2-6]\.\d+(?:\.\d+)?\s+',meaningful[-1]) or '｜' in meaningful[-1]):orphan_headings.append(meaningful[-1])
                    # 章节标题按“≥13pt 大字号行”识别（2026-09-21 四轮 F 项）：目录行
                    # (10.5pt) 与表格单元格(9pt，含阅读指南引用)中的同名文本不再误判。
                    big=set()
                    for b in page.get_text('dict')['blocks']:
                        for l in b.get('lines',[]):
                            ltext=''.join(sp['text'] for sp in l['spans']).strip()
                            sizes=[sp['size'] for sp in l['spans'] if sp['text'].strip()]
                            if ltext and sizes and max(sizes)>=13:big.add(ltext)
                    for heading in headings:
                        if any(t==heading or t.startswith(heading+'（') or t.startswith(heading+' —') for t in big):page_map.setdefault(heading,index)
                if not text.strip() or RESIDUAL.search(text):return {'status':'FAILED','reason':'PDF_CONTENT_INVALID'}
            pdf=path.with_suffix('.pdf');staged=pdf.with_suffix('.tmp.pdf');staged.write_bytes(target.read_bytes());staged.replace(pdf)
        from docx import Document
        d=Document(path)
        toc=next((p for p in d.paragraphs if p._p.xpath('.//w:bookmarkStart[@w:name="YH_TOC"]')),None)
        layout_changed=False
        paragraphs=d.paragraphs
        for index,paragraph in enumerate(paragraphs):
            if paragraph.text.strip() in orphan_headings:
                # Walk actual XML siblings: Document.paragraphs skips tables and
                # could otherwise move a distant chapter across an entire table.
                from docx.text.paragraph import Paragraph
                from docx.oxml.ns import qn
                start=paragraph
                previous=start._p.getprevious()
                while previous is not None and previous.tag==qn('w:p'):
                    candidate=Paragraph(previous,start._parent)
                    if candidate._p.xpath('.//w:drawing'):break
                    if candidate.text.strip() and not re.match(r'^[一二三四五六七八九十]+、|^[1-9]\.\d+(?:\.\d+)?\s+',candidate.text.strip()):break
                    start=candidate;previous=previous.getprevious()
                if not start.paragraph_format.page_break_before:
                    start.paragraph_format.page_break_before=True;layout_changed=True
        # 竖排目录逐行回填实际页码；目录标题行(带YH_TOC书签)保持不变
        toc_lines={'一、基本信息':'一、封面与基本信息','二、总成本概览':'二、总成本概览','三、要素明细':'三、成本要素明细分析','四、专项分析':'四、重点产品专项分析','五、对标分析':'五、对标分析','六、总结与建议':'六、总结与建议'}
        toc_updated=False;toc_verified={}
        for paragraph in d.paragraphs:
            text=paragraph.text
            # 目录行以全角空格开头；真实章节标题不以全角空格开头，避免污染正文
            if not text.startswith(chr(0x3000)):continue
            key=next((k for k in toc_lines if text.lstrip(chr(0x3000)).split('　')[0].startswith(k)),None)
            if key is None or paragraph is toc:continue
            page=page_map.get(toc_lines[key])
            fresh=chr(0x3000)+key+('　·　第'+str(page)+'页' if page else '')
            if paragraph.text!=fresh:_text(paragraph,paragraph.text,fresh);toc_updated=True
            if page and paragraph.text==fresh:toc_verified[toc_lines[key]]=page
        if _toc_pass<5 and (layout_changed or toc_updated):
            d.save(path)
            return convert_pdf(path,timeout,converter,_toc_pass+1)
        return {'status':'PASS','scope':'file_conversion','toc_updated':len(toc_verified)==6 and toc_verified==page_map and not toc_updated,'orphan_headings':orphan_headings,'toc_pages':page_map,'path':str(pdf),'pages':pages,'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()}
    except (OSError,subprocess.TimeoutExpired) as exc:return {'status':'FAILED','reason':type(exc).__name__}


def readable_source(e):
    name=Path(e.get('source','来源待补')).name
    section=e.get('section') or e.get('heading') or '相关章节'
    location=e.get('location') or ('第'+str(e['page'])+'页' if e.get('page') else '位置待补')
    return name+' · '+str(section)+' · '+str(location)


def compact_working_template(output=TEMPLATE,map_path=MAP_PATH):
    """Edit only the working copy; retain required sections and original numeric bookmarks."""
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    d=Document(output);meta=json.loads(Path(map_path).read_text())
    if meta.get('reader_template_version')=='reader-v4':return
    body=d.element.body
    # 2026-09-21 真人评审三轮反馈：模板前置章节（解决方案封面、文档控制三表、
    # 阅读指南、目录域）是题包模板的组成部分，予以完整保留，不再裁剪；
    # 报告生成只做占位符回填与"模板未说明"处的增补。
    _=body
    # Existing blank同比 cells are omissions, not missing data.
    overview=next(t for t in d.tables if any('去年同月' in c.text for c in t.rows[0].cells))
    for row,cn in zip(overview.rows[4:7],['材料','人工','制造费用']):
        for index,field,ratio in [(4,'去年'+cn+'成本' if cn!='制造费用' else '去年制造费用',False),(5,cn+'成本同比',True)]:
            p=row.cells[index].paragraphs[0];p.text='{{'+field+'}}'+('%' if ratio else '')
            marker='YH_reader_'+field
            mark=OxmlElement('w:bookmarkStart');mark.set(qn('w:id'),str(22000+len(meta['placeholders'])));mark.set(qn('w:name'),marker);p._p.insert(0,mark)
            end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),mark.get(qn('w:id')));p._p.append(end)
            meta['placeholders'].append({'original':field,'field':field,'context':p.text,'marker':marker,'xml_part':'word/document.xml','source':'period_values.yoy.elements_unit / elements.comparisons.yoy.unit.rate','unit':'%' if ratio else '元/盒'})
    # 2026-09-21 真人评审四轮（B 项）：模板原生分页（封面/文档控制/阅读指南/目录
    # 各归各页）完整保留，不再剥离 w:br page 与 pageBreakBefore。
    style_reader(d)
    d.save(output)
    meta['reader_template_version']='reader-v4'
    meta['template_hash']=hashlib.sha256(Path(output).read_bytes()).hexdigest()
    meta['working_changes']=['前置章节与原生分页完整保留（模板为准）','六个赛题固定章节保留','同比三要素单独绑定','动态表格按模板md列结构']
    Path(map_path).write_text(json.dumps(meta,ensure_ascii=False,indent=2))


def rebuild_report_footer(doc):
    """Own the footer as a whole so inherited textboxes cannot corrupt page labels."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    visited = set()
    for section in doc.sections:
        footer = section.footer
        if id(footer.part) in visited:
            continue
        visited.add(id(footer.part))
        for node in list(footer._element):
            footer._element.remove(node)
        paragraph = footer.add_paragraph()
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragraph.add_run('第')
        for instruction, suffix in [('PAGE', '页共'), ('NUMPAGES', '页')]:
            field = OxmlElement('w:fldSimple');field.set(qn('w:instr'), instruction)
            run = OxmlElement('w:r');text = OxmlElement('w:t');text.text = '1'
            run.append(text);field.append(run);paragraph._p.append(field)
            paragraph.add_run(suffix)
        for run in paragraph.runs:
            run.font.name = 'Noto Sans SC';run.font.size = Pt(9)


def keep_source_block(doc):
    paragraphs = doc.paragraphs
    starts = [i for i,p in enumerate(paragraphs) if layout_text(p.text).strip() in ('来源与审核说明', '证据来源')]
    if not starts:
        return
    block = paragraphs[starts[-1]:]
    # Only short terminal reference blocks are kept together, not unbounded lists.
    if len(block) <= 12 and sum(len(p.text) for p in block) <= 1600:
        for i, paragraph in enumerate(block):
            paragraph.paragraph_format.keep_with_next = i < len(block)-1
            paragraph.paragraph_format.keep_together = True


def expand_soft_breaks(doc):
    """AA 占位符绑定值中的换行符展开为真实换行 w:br（2026-09-21 真人评审二轮反馈：多行文本被压成一段）。"""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    NEWLINE=chr(10)
    for node in list(doc.element.body.iter(qn('w:t'))):
        text=node.text or ''
        if NEWLINE not in text:continue
        parts=text.split(NEWLINE)
        node.text=parts[0]
        parent=node.getparent()
        position=list(parent).index(node)
        for part in parts[1:]:
            br=OxmlElement('w:br');position+=1;parent.insert(position,br)
            new_t=OxmlElement('w:t');new_t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');new_t.text=part
            position+=1;parent.insert(position,new_t)


def style_reader(doc):
    """模板样式保留（2026-09-21 真人评审四轮 E 项）：不再覆盖模板的字体/字号/
    颜色/边距/分页/行距；只处理本系统新增的内容——图题居中灰字、目录行距、
    数字-单位防断行、换行展开；动态表格外观在 table() 内按模板样式生成。"""
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    for p in _all_paragraphs(doc):
        protect_number_units(p)
        text=layout_text(p.text).strip()
        if text.startswith('图｜'):
            fmt=p.paragraph_format
            p.alignment=WD_ALIGN_PARAGRAPH.CENTER;fmt.first_line_indent=None
            fmt.space_before=Pt(4);fmt.space_after=Pt(10)
            for r in p.runs:r.font.size=Pt(8.5)
        elif p.text.startswith(chr(0x3000)):
            fmt=p.paragraph_format
            fmt.space_before=Pt(1);fmt.space_after=Pt(1);fmt.line_spacing=1.3;fmt.first_line_indent=None
            for r in p.runs:r.font.size=Pt(10.5)
    expand_soft_breaks(doc)
    keep_source_block(doc)
    rebuild_report_footer(doc)


def add_reader_summary(doc,snapshot,narrative,output):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt
    # 2026-09-21 真人评审三轮：模板前置章节（封面/文档控制/阅读指南/目录域）完整保留，
    # 自创大标题取消（模板封面已有）。文档头按模板 md 增补；核心发现与审核状态
    # 作为"模板未说明"的增补插在"一、封面与基本信息"之前。
    anchor=next((p for p in doc.paragraphs if p.text.strip()=='一、封面与基本信息'),None)
    if anchor is None:return
    m=snapshot['metrics'];label=snapshot['period']['start'] if snapshot['period']['start']==snapshot['period']['end'] else snapshot['period']['start']+' 至 '+snapshot['period']['end']
    report_no='YH-'+hashlib.sha256((snapshot['snapshot_id']) .encode()).hexdigest()[:8].upper()
    anchor.insert_paragraph_before('报告编号：'+report_no+'（分析周期 '+label+'）')
    mode='本次采用基础分析，原因解释待复核。' if not narrative.get('model_live') or narrative.get('status')!='PASS' else '本次采用模型辅助解释；因果归因仍待人工复核。'
    anchor.insert_paragraph_before('人工审核：待审核。'+mode)
    ranked=sorted(snapshot['elements'],key=lambda e:abs(Decimal(e.get('unit_delta') or '0')),reverse=True)
    lead=ranked[0]
    from decimal import Decimal as _D
    _lead_delta=_D(str(lead.get('unit_delta') or '0'))
    anchor.insert_paragraph_before('核心发现：本月单位成本 '+number(m['unit_cost'])+' 元/盒，总成本 '+number(m['total_cost'])+' 元。对成本影响最大的是'+lead['name']+'，每盒比上月'+('增加' if _lead_delta>=0 else '减少')+' '+number(str(lead.get('unit_delta') or '0').lstrip('-'))+' 元。正文第三节按要素拆解变动并给出方向评估，第五节是与中药二厂的对比，第六节给出可直接执行的核查建议。')
    # 目录（真人评审二轮）：完整子目录；条目插在模板目录域提示行之后（保留域可更新），
    # 一级行保持全角空格前缀以兼容 convert_pdf 的页码回写。
    title=next((p for p in doc.paragraphs if p.text.strip().replace(chr(0x3000),'').replace(' ','')=='目录'),None)
    if title is None:return
    insert_at=title
    heads=[(para,layout_text(para.text).strip()) for para in doc.paragraphs]
    heads=[(para,t) for para,t in heads if re.match(r'^[一二三四五六七八九十]+、',t) or re.match(r'^[1-9][.][1-9](?:[.][1-9])?[ ]',t)]
    for index,(para,t) in enumerate(heads):
        name='YH_SEC_'+str(index)
        bmk=OxmlElement('w:bookmarkStart');bmk.set(qn('w:id'),str(31000+index));bmk.set(qn('w:name'),name)
        bmk_end=OxmlElement('w:bookmarkEnd');bmk_end.set(qn('w:id'),str(31000+index))
        para._p.insert(0,bmk);para._p.append(bmk_end)
        is_top=bool(re.match(r'^[一二三四五六七八九十]+、',t))
        new_p=OxmlElement('w:p')
        insert_at._p.addnext(new_p)
        from docx.text.paragraph import Paragraph
        line=Paragraph(new_p,insert_at._parent)
        line.text=(chr(0x3000) if is_top else chr(0x3000)*2)+t
        line.paragraph_format.space_after=Pt(1)
        line.style='Normal'
        insert_at=line
    mark=OxmlElement('w:bookmarkStart');mark.set(qn('w:id'),'30000');mark.set(qn('w:name'),'YH_TOC');hint._p.insert(0,mark)


def add_reader_charts(doc,snapshot,benchmark,anchors,output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from docx.shared import Cm
    cjk=str(ROOT/'05_原型/assets/fonts/NotoSansSC-Regular.ttf')
    if Path(cjk).is_file():font_manager.fontManager.addfont(cjk);family=font_manager.FontProperties(fname=cjk).get_name()
    else:family='sans-serif'
    plt.rcParams.update({'font.family':family,'font.size':9,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
    period_label=snapshot['period']['start']+' 至 '+snapshot['period']['end'] if snapshot['analysis_type']=='quarterly' else snapshot['month']
    subtitle=snapshot['product']+' · '+snapshot['factory']+' · '+period_label
    def insert(fig,name,anchor,title,width_cm=17):
        fig.tight_layout();path=output.with_name(name+'.png');fig.savefig(path,dpi=190,bbox_inches='tight');plt.close(fig)
        cap=doc.add_paragraph('图｜'+title);cap.paragraph_format.keep_with_next=True
        pic=doc.add_paragraph();pic.add_run().add_picture(str(path),width=Cm(width_cm))
        anchor.addnext(cap._p);cap._p.addnext(pic._p)
    trend=snapshot['trend'];fig,ax=plt.subplots(figsize=(8,2.5))
    vals=[float(r['unit_cost']) for r in trend];ax.plot([r['month'] for r in trend],vals,'o-',color='#176C8C');ax.set_ylabel('单位成本（元/盒）')
    span=max(vals)-min(vals);margin=max(span*.6,max(vals)*.07);ax.set_ylim(max(0,min(vals)-margin),max(vals)+margin)
    for i,v in enumerate(vals):ax.annotate(f'{v:.2f}',(i,v),xytext=(0,7),textcoords='offset points',ha='center')
    ax.grid(axis='y',alpha=.2);insert(fig,'trend',anchors['近6个月成本趋势表格']._p,snapshot['product']+' · '+snapshot['factory']+' · '+trend[0]['month']+' 至 '+trend[-1]['month']+'｜单位成本趋势（纵轴范围见刻度）')
    els=snapshot['elements']
    # 占比数据用饼图（2026-09-21 真人评审反馈：占比不应画横向柱状图）
    fig,ax=plt.subplots(figsize=(6.8,2.9))
    sizes=[float(e['unit']) for e in els]
    labels=[e['name']+' '+number(e['unit'])+' 元' for e in els]
    wedges,texts,autotexts=ax.pie(sizes,labels=labels,autopct=lambda pct:f'{pct:.1f}%',startangle=90,counterclock=False,
        colors=['#176C8C','#46978D','#82939F','#B08968'][:len(els)],wedgeprops={'linewidth':1.2,'edgecolor':'white'},textprops={'fontsize':9})
    for t in autotexts:t.set_color('white');t.set_fontsize(8.5)
    ax.set_aspect('equal')
    anchor=next(p._p for p in doc.paragraphs if p.text.startswith('2.2'))
    insert(fig,'structure',anchor,subtitle+'｜三要素单位成本构成占比',width_cm=13)
    base=snapshot.get('comparison',{}).get('mom',{}).get('base');current=snapshot['metrics']['unit_cost']['value']
    if base is not None:
        # 瀑布图（2026-09-21 真人评审反馈修复）：纵轴缩放至变动区间而非从零起——
        # 此前负变动柱挤在本期值附近不可辨，被误读为"负值画在第一象限"。
        # 瀑布图（2026-09-21 真人评审二轮反馈）：零线双区画法——左/右总量柱自 0
        # 向上；各要素变动柱按自身数值绘制，负向落在零线下方（第四象限），
        # 量级在负区独立可辨；零线加粗，全图加高容纳正负两方向。
        deltas=[float(e.get('unit_delta') or 0) for e in els]
        total_top=max(float(base),float(current),0)
        neg_bottom=min(deltas+[0]);pos_top=max(deltas+[0])
        neg_span=max(abs(neg_bottom),total_top*0.05,0.05);pos_span=max(pos_top,total_top*0.05,0.05)
        fig,ax=plt.subplots(figsize=(8,3.3));xs=['上期单位成本']+[e['name']+' 变动' for e in els]+['本期单位成本']
        ax.bar(0,float(base),width=.58,color='#82939F',zorder=3);ax.text(0,float(base)+total_top*0.015,f'{float(base):.2f}',ha='center',va='bottom',fontsize=9)
        run_note=float(base)
        for i,e in enumerate(els,1):
            v=deltas[i-1]
            ax.bar(i,v,width=.58,color='#A56B3D' if v>=0 else '#1F6E5E',zorder=3)
            ax.text(i,v+(pos_span*0.08 if v>=0 else -pos_span*0.08),(('+' if v>=0 else '−')+number(e.get('unit_delta') or 0).lstrip('-')),ha='center',va='bottom' if v>=0 else 'top',fontsize=9,color='#5A3B28' if v>=0 else '#1F6E5E')
            run_note+=v
        ax.bar(len(els)+1,float(current),width=.58,color='#176C8C',zorder=3);ax.text(len(els)+1,float(current)+total_top*0.015,f'{float(current):.2f}',ha='center',va='bottom',fontsize=9)
        ax.axhline(0,color='#3A3A3A',lw=1.2,zorder=1)
        ax.set_ylim(neg_bottom-neg_span*0.55,total_top*1.14)
        ax.set_xticks(range(len(els)+2),xs,fontsize=8.5);ax.set_ylabel('元/盒（零线以上=单位成本，零线以下=各要素变动额）');ax.grid(axis='y',alpha=.22)
        insert(fig,'waterfall',anchor,subtitle+'｜上期至本期单位成本变动（零线双区：负向柱在零线下）')

    be=(benchmark or {}).get('elements',[])
    if be:
        fig,ax=plt.subplots(figsize=(8,2.4));pos=list(range(len(be)))
        ax.bar([x-.18 for x in pos],[float(r['right']) for r in be],width=.35,label=benchmark_labels(benchmark)[1],color='#176C8C');ax.bar([x+.18 for x in pos],[float(r['left']) for r in be],width=.35,label=benchmark_labels(benchmark)[0],color='#82939F')
        peak=max(float(r[k]) for r in be for k in ('left','right'));top_limit=peak*1.30
        for i,r in enumerate(be):
            pair_top=max(float(r['right']),float(r['left']))
            ax.text(i,pair_top+peak*0.03,'差额 '+number(r['delta']),ha='center',va='bottom',fontsize=8.5,color='#444444')
        ax.set_xticks(pos,[r['name'] for r in be]);ax.set_ylabel('元/盒（零基线）');ax.set_ylim(0,top_limit);ax.legend(ncol=2,loc='upper center',frameon=False)
        insert(fig,'benchmark',anchors['对标差异表格']._p,snapshot['product']+' · '+period_label+'｜跨厂三要素（'+benchmark_labels(benchmark)[2]+'）')


def assess_report(result,review=None):
    """File checks are necessary but never sufficient for business acceptance.

    Human dimensions come only from a stored review bound to the current
    artifact bytes; without it they stay PENDING, never auto-signed."""
    # 数值绑定下限按“版本明确的合同”解析：生成方验收器自带 expected_bindings
    # 的合同按其声明下限执行；制药模板占位符数量由模板合同固定；未注册
    # 合同一律 fail-closed，不再硬编码旧绑定数量（generic-v1 已废弃）。
    PHARMA_TEMPLATE_BINDING_FLOOR=70
    def _binding_floor(checks):
        contract=checks.get('contract')
        if contract=='generic-v2-role-bound' and checks.get('contract_floor')=='expected_bindings':
            return int(checks.get('expected_bindings') or 10**9)
        if contract is None:  # 赛题制药模板：无 contract 字段即制药路径
            return PHARMA_TEMPLATE_BINDING_FLOOR
        return 10**9
    def verdict(ok,reason):return {'status':'PASS' if ok else 'FAIL','reason':reason}
    n=result.get('narrative',{});ev=result.get('evidence',{});dx=result.get('docx',{});pdf=result.get('pdf',{})
    checks=dx.get('verification',{})
    snapshot=result.get('snapshot',{})
    findings=n.get('findings',[])
    actions=[f for f in findings if f.get('suggestion','').strip()]
    # Per-claim evidence verification, not one aggregate boolean.
    from .knowledge import Knowledge
    sources={e['evidence_id']:e for e in (ev.get('evidence',[]) if isinstance(ev,dict) else ev)}
    claim_failures=[];claims_checked=0
    for f in findings:
        claim=f.get('claim_type');claims_checked+=1
        if claim=='numeric_fact' and not f.get('metric_refs'):claim_failures.append('numeric_fact缺metric_refs')
        if claim=='insufficient_evidence' and not f.get('missing_evidence'):claim_failures.append('insufficient_evidence缺missing_evidence标注')
        if claim in ('hypothesis','document_fact'):
            if not f.get('evidence_refs'):claim_failures.append(claim+'缺证据引用')
            for ref in f.get('evidence_refs',[]):
                item=sources.get(ref)
                if item is None:claim_failures.append('引用了不存在或被排除的证据:'+str(ref));continue
                outcome=Knowledge.evidence_applicability(item,product=snapshot.get('product'),factory=snapshot.get('factory'),period=snapshot.get('period'),specification=snapshot.get('specification'))
                if not outcome['applicable']:claim_failures.append('证据不适用于本场景:'+str(ref))
    evidence_ok=ev.get('status') in ('PASS','FULL','HYBRID_REAL','READY') if isinstance(ev,dict) else False
    def human(dimension,default_reason):
        dim=(review or {}).get('dimensions',{}).get(dimension) if review else None
        if not dim:return {'status':'PENDING','reason':default_reason}
        return {'status':dim['status'],'reason':dim.get('comment') or '','reviewer':review.get('reviewer'),'reviewed_at':review.get('reviewed_at'),'review_id':review.get('id')}
    evidence_reasons=[]
    if not evidence_ok:evidence_reasons.append(f'证据检索状态异常（{ev.get("status") if isinstance(ev,dict) else "不可用"}），不满足适用性核对前提')
    if not n.get('evidence_applicability_checked'):evidence_reasons.append('模型解释未全部通过数字合同校验，未进入证据适用性逐条核对')
    evidence_reasons.extend(f'{i+1}. {msg}' for i,msg in enumerate(claim_failures[:5]))
    r={
      'file_openable':verdict(dx.get('status')=='PASS' and pdf.get('status')=='PASS','DOCX结构检查与PDF实际打开'),
      'calculation_consistency':verdict(checks.get('core_numbers') and _binding_floor(checks)<=checks.get('numeric_bindings_checked',0) and not checks.get('numeric_binding_failures'),'固定快照与模板位置逐项核对'),
      'section_completeness':human('section_completeness','六个固定章节的业务实质待真人评审'),
      'evidence_applicability':verdict(evidence_ok and bool(n.get('evidence_applicability_checked')) and not claim_failures, f'逐条核对{claims_checked}项结论的证据引用与适用性；全部通过' if not evidence_reasons else '证据适用未通过：'+'；'.join(evidence_reasons)),
      'readability':human('readability','真人可读性评审待完成'),
      'visual_quality':human('visual_quality','逐页渲染检查与真人版式审核待完成'),
      'task_actionability':verdict(bool(actions) and all(all(isinstance(f.get(k),str) and f[k].strip() and not RESIDUAL.search(f[k]) for k in ('suggestion','verification_target','responsible_role','deadline_basis')) and isinstance(f.get('expected_evidence'),list) and bool(f['expected_evidence']) and all(isinstance(x,str) and x.strip() and not RESIDUAL.search(x) for x in f['expected_evidence']) for f in actions),'建议必须包含对象、预期证据、责任角色和期限依据'),
      'model_participation':verdict(n.get('model_live') is True and n.get('status')=='PASS','模型实际参与、身份核验一致且解释覆盖校验通过；基础分析不视为模型通过')}
    r['overall']='PASS' if all(v['status']=='PASS' for v in r.values()) else 'FAIL' if any(v['status']=='FAIL' for v in r.values()) else 'PENDING'
    if review:
        r['human_attribution_score']=review.get('attribution_score')
        r['human_review_comment']=review.get('comment','')
    r['policy']='强制环节逐项通过后才能认定报告合格；人工评审缺失保持待评，产物变化使既有审核失效'
    return r
