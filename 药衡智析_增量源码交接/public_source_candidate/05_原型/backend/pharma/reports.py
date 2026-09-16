"""原 Word 模板的 XML 定位绑定、保留 run 样式、逐任务 PDF 转换。"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
import hashlib, json, re, shutil, subprocess, tempfile
from datetime import datetime
from decimal import Decimal
from .config import ROOT, PACKAGE, ARTIFACTS
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
PATTERN = re.compile(r'\{\{([^{}]+)\}\}')
TEMPLATE = ROOT / '04_方案与文档/月度成本分析报告工作模板.docx'
MAP_PATH = ROOT / '04_方案与文档/placeholder_map.json'
RENDERER_VERSION='reader-v9-truetype-fonts'
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
    original = next((PACKAGE / '04_报告模板').glob('*.docx'))
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
                # Only the working copy loses the supplied company watermark.
                for parent in xml.iter():
                    for child in list(parent):
                        if child.tag.endswith('}shape') and (any('WaterMark' in str(v) for v in child.attrib.values()) or any(t.attrib.get('string')=='重庆创灵境数字技术有限公司' for t in child.iter())):parent.remove(child)
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

def _all_paragraphs(doc):
    from docx.text.paragraph import Paragraph
    return [Paragraph(p,doc) for p in doc.element.body.iter('{'+W+'}p')]

def build_bindings(snapshot,narrative,benchmark=None):
    m=snapshot['metrics']; els={e['key']:e for e in snapshot['elements']}; quarterly=snapshot['analysis_type']=='quarterly'
    period=snapshot.get('period',{}); label=(period.get('start','')+' 至 '+period.get('end','')) if quarterly else snapshot['month']
    values={'报告标题':f"{snapshot['product']} {'季度成本分析' if quarterly else '专题分析' if snapshot['analysis_type']=='special' else '月度成本分析'}报告",'报告类型':{'monthly':'月度成本分析','quarterly':'季度成本分析','special':'专题分析'}[snapshot['analysis_type']],'分析月份':label,'产品名称':snapshot['product'],'产品规格':snapshot.get('specification',{'银黄口服液':'10ml×10支/盒','板蓝根颗粒':'10g×20袋/盒','六味地黄胶囊':'0.3g×60粒/盒'}.get(snapshot['product'],'')),'编制日期':datetime.now().strftime('%Y-%m-%d'),'本月产量':number(m['quantity'],0),'本月单位成本':number(m['unit_cost'],4 if quarterly else 2),'单位成本':number(m['unit_cost'],4 if quarterly else 2),'本月总成本':number(m['total_cost'])}
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
        return '\n'.join(f.get('rendered_text',f.get('text','')) for f in findings if f.get('section')==section and f.get('claim_type')=='hypothesis')
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
    values['成本异常排查分析']=overview+'\n'+alert_text+'\n'+prose('overhead')
    be=(benchmark or {}).get('elements',[])
    values['差异结构拆解分析']='二厂减一厂，差异率以一厂为基数。'+('；'.join(r['name']+'差额 '+number(r.get('delta'))+' 元/盒，占跨厂单位成本总差额 '+number(r.get('contribution'))+'%' for r in be)+'。' if be else '该期间没有可比跨厂记录。')
    values['差异归因分析文本']=prose('benchmark') or '三要素差额用于定位核查重点。二厂缺原料、工时及费用明细，尚不能分解到二厂单项原料；请两厂成本会计核对同规格的领料、工时与费用分摊记录。'
    values['本月亮点']='本期单位成本 '+number(m['unit_cost'])+' 元/盒，产量 '+number(m['quantity'],0)+' 盒。管理重点是先核查贡献最大的要素，再区分产量变化和单位成本变化对总支出的影响。'
    values['需关注问题']='原料成本上涨不能直接等同采购价上涨。平均小时工资为题包折算口径，不能据此认定基础薪率上调。跨厂原料差异需补二厂明细。'
    delta=changes.get('unit_cost',{}).get('mom',{}).get('delta')
    values['合计贡献度']='100.00' if delta is not None and Decimal(delta)!=0 else 'N/A（总变动为0或无基期）'
    return values

def render_docx(snapshot,narrative,evidence,output,benchmark=None):
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    if not TEMPLATE.exists():normalize_template()
    elif json.loads(MAP_PATH.read_text()).get('reader_template_version') not in ('reader-v2','reader-v3-truetype'):compact_working_template(TEMPLATE,MAP_PATH)
    meta=json.loads(MAP_PATH.read_text());doc=Document(TEMPLATE)
    values=build_bindings(snapshot,narrative,benchmark)
    for entry in meta['placeholders']:values.setdefault(entry['field'], NA)
    dynamic={k for k in values if '表格' in k}
    for k in dynamic:values[k]='' # tables are inserted at their actual block, below
    sections=[]; dynamic_anchors={}
    for p in _all_paragraphs(doc):
        before=p.text
        for field in dynamic:
            if '{{'+field+'}}' in before:dynamic_anchors[field]=p
        replace_text_nodes(list(p._p.iter('{'+W+'}t')),values)
        if 'N/A' in p.text:_text(p,'）%','）')
        if before.startswith(('一、','二、','三、','四、','五、','六、')):sections.append(p.text)
        for a,b in [('整体解决方案','成本分析报告'),('重庆创灵境数字技术有限公司','药衡智析演示团队（模拟数据）'),('龚云','演示编制人'),('ERP系统成本模块','创灵境题包模拟CSV（非实时ERP）'),('财务总监','待人工审核'),('与中药二厂','二厂−一厂，以一厂为基准')]:_text(p,a,b)
        if '关键提示：方案中' in p.text:_text(p,p.text,'本报告使用比赛模拟数据。事实、原因假设与缺失证据分别标注；任务仅为模拟发送。')
        if snapshot['analysis_type']=='quarterly':
            for a,b in [('本月','本季度'),('上月','上季度'),('去年同月','去年同期季度'),('分析月份','分析期间')]:_text(p,a,b)
    for p in _all_paragraphs(doc):
        if '近6个月单位成本趋势' in p.text:_text(p,'近6个月单位成本趋势','可用期间单位成本趋势（截至 '+snapshot['month']+'，共 '+str(len(snapshot['trend']))+' 个月）')
    for section in doc.sections:
        for part in [section.header,section.footer]:
            for p in part.paragraphs:
                replace_text_nodes(list(p._p.iter('{'+W+'}t')),values)
                _text(p,'整体解决方案','药衡智析 · 模拟成本分析')
            pg=section._sectPr.find(qn('w:pgNumType'))
            if pg is not None:pg.attrib.pop(qn('w:start'),None)
    for section in doc.sections:
        for p in section.footer.paragraphs:
            if '页' not in p.text:continue
            for child in list(p._p):
                if child.tag!=qn('w:pPr'):p._p.remove(child)
            p.add_run('第 ')
            for instruction in ('PAGE','NUMPAGES'):
                run=p.add_run();field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),instruction);run._r.addnext(field)
                p.add_run(' 页 / 共 ' if instruction=='PAGE' else ' 页')
    def table(anchor,headers,rows):
        p=dynamic_anchors.get(anchor)
        if p is None:raise ValueError('模板动态块缺失:'+anchor)
        t=doc.add_table(rows=1,cols=len(headers))
        if doc.tables[0].style:t.style=doc.tables[0].style
        for cell,label in zip(t.rows[0].cells,headers):cell.text=str(label)
        for row in rows or [['N/A：无可用明细']+['—']*(len(headers)-1)]:
            for cell,val in zip(t.add_row().cells,row):cell.text=str(val if val is not None else NA)
        p._p.addnext(t._tbl)
        for row in t.rows:
            for cell in row.cells:
                for pp in cell.paragraphs:
                    for r in pp.runs:r.font.size=Pt(9)
        return t
    details=snapshot.get('details',{})
    def generic_rows(items):
        if not items:return []
        return [[str(k),str(v)] for item in items for k,v in item.items() if not k.startswith('_') and k not in ('source_hash','row_key')]
    table('原材料成本明细表格',['月份','原料','单位消耗成本（元/盒）','总成本（元）'],[[r['月份'],r['原材料名称'],r['单位消耗成本(元/盒)'],r['原材料总成本(元)']] for r in details.get('materials',[])])
    table('近6个月成本趋势表格',['月份','单位成本（元/盒）','产量（盒）','总成本（元）'],[[r['month'],number(r['unit_cost']),number(r['quantity'],0),number(r['total_cost'])] for r in snapshot['trend']])
    table('原材料价格跟踪表格',['药材','参考月份','市场价格','单位（非采购价）'],[[r['药材名称'],snapshot['month'],r.get(str(int(snapshot['month'][5:]))+'月价格',NA),r['单位']] for r in details.get('market',[])])
    table('对标差异表格',['要素','二厂（元/盒）','一厂（元/盒）','差异（元/盒）','差异率（%）'],[[r.get('name','单位成本'),number(r.get('left')),number(r.get('right')),number(r.get('delta')),number(r.get('rate'))] for r in (benchmark or {}).get('summary',[])[:1]+(benchmark or {}).get('elements',[])])
    actionable=[f for f in narrative.get('findings',[]) if f.get('suggestion','').strip()]
    table('改进建议表格',['问题与核查行动','预期证据'],[[str(i+1)+'．'+f.get('rendered_text','')+'\n核查对象：'+f.get('verification_target','待补')+'\n行动：'+f.get('suggestion'), '、'.join(f.get('expected_evidence',[]) if isinstance(f.get('expected_evidence'),list) else [f.get('expected_evidence') or '核查对象的原始记录'])] for i,f in enumerate(actionable)])
    table('整改任务表格',['责任部门／角色','优先级','期限依据与状态'],[[str(i+1)+'．'+(f.get('department') or '责任部门待定')+'／'+(f.get('responsible_role') or '待分配')+'（姓名待分配）', {'high':'高','medium':'中','low':'低'}.get(f.get('priority'),'中'), (f.get('deadline_basis') or '下次成本复核前，具体日期由用户确认')+'；待确认发送'] for i,f in enumerate(actionable)])
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    els={e['key']:e for e in snapshot['elements']}
    for prefix,key,text in [('3.3','labor','平均小时工资是题包折算口径。每盒人工费用受工时、人员组成及加班影响；需核对工时台账、工资组成与返工记录，不能认定基础薪率上涨。'),('四、','overhead','按费用台账和分配基数检查变化。维修事件只有在产品、期间及入账范围一致时才用于本期解释；不得将维修金额重复计入总成本。')]:
        anchor=next((p for p in doc.paragraphs if p.text.startswith(prefix)),None)
        if anchor is not None:
            e=els[key];anchor.insert_paragraph_before(e['name']+'每盒 '+number(e['unit'])+' 元，比上期变动 '+number(e.get('unit_delta'))+' 元，占单位成本环比变动 '+number(e.get('unit_contribution'))+'%。'+text)
    add_reader_charts(doc,snapshot,benchmark,dynamic_anchors,output)
    add_reader_summary(doc,snapshot,narrative,output)
    doc.add_paragraph('来源与审核说明')
    doc.add_paragraph('数据来源：成本汇总表、原材料明细表、人工与制造费用表 · '+snapshot['product']+' · '+snapshot['factory']+' · '+snapshot['month']+'。金额以元、单位成本以元/盒计；季度按产量加权。')
    source_map={e['evidence_id']:e for e in evidence.get('evidence',[])}
    used=set()
    for f in narrative.get('findings',[]):
        for ref in f.get('evidence_refs',[]):
            if ref in source_map and ref not in used:
                e=source_map[ref];doc.add_paragraph(readable_source(e));used.add(ref)
    doc.add_paragraph('人工归因评分：待评（0—5分）；内容可读性与逐页版式：待人工审核。引用只说明依据来源，不等于已证实因果。')
    style_reader(doc)
    audit=output.with_name('machine_audit.json')
    audit.write_text(json.dumps({'snapshot':snapshot,'narrative':narrative,'evidence':evidence,'benchmark':benchmark,'bindings':values},ensure_ascii=False,indent=2))
    temp=output.with_suffix('.tmp.docx');doc.save(temp)
    check=verify_docx(temp,snapshot,sections)
    if check['status']!='PASS':raise ValueError('报告验证失败:'+json.dumps(check,ensure_ascii=False))
    temp.replace(output)
    return {'status':'PASS','scope':'file_generation','path':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'verification':check,'bindings':values}

def verify_docx(path,snapshot,sections=None):
    with ZipFile(path) as z:
        strings=[]
        for n in z.namelist():
            if n.startswith('word/') and n.endswith('.xml'):
                xml=ET.fromstring(z.read(n));strings.append(''.join(t.text or '' for t in xml.iter('{'+W+'}t')))
        text='\n'.join(strings)
        numeric_bindings=build_bindings(snapshot,{})
        by_marker={}
        for n in z.namelist():
            if n.startswith('word/') and n.endswith('.xml'):
                xml=ET.fromstring(z.read(n))
                for p in xml.findall('.//w:p',NS):
                    actual=''.join(t.text or '' for t in p.findall('.//w:t',NS))
                    for mark in p.findall('w:bookmarkStart',NS):by_marker[mark.get('{'+W+'}name')]=actual
        failures=[];checked=0
        for entry in json.loads(MAP_PATH.read_text())['placeholders']:
            field=entry['field'];value=numeric_bindings.get(field)
            if value is None or not (re.match(r'^-?\d',str(value)) or str(value).startswith('N/A')) or field=='编制日期':continue
            expected=entry['context'].replace('{{'+entry['original']+'}}',str(value))
            if 'N/A' in expected:expected=expected.replace('）%','）')
            actual=by_marker.get(entry.get('marker'))
            checked+=1
            if actual!=expected:failures.append({'field':field,'expected':expected,'actual':actual})
        duplicated_units=bool(re.search(r'元/盒元/盒|%%|盒盒',text))
        residual=PATTERN.findall(text)
        headings=[s for s in ['一、封面与基本信息','二、总成本概览','三、成本要素明细分析','四、重点产品专项分析','五、对标分析','六、总结与建议'] if s in text]
        numeric=number(snapshot['metrics']['unit_cost'],4 if snapshot['analysis_type']=='quarterly' else 2) in text and number(snapshot['metrics']['total_cost']) in text
        tables=sum(1 for _ in ET.fromstring(z.read('word/document.xml')).iter('{'+W+'}tbl'))
        images=len([n for n in z.namelist() if n.startswith('word/media/')])
    return {'status':'PASS' if not residual and len(headings)==6 and numeric and tables>=11 and images>0 and not failures and checked>=70 and not duplicated_units else 'FAIL','numeric_bindings_checked':checked,'numeric_binding_failures':failures,'duplicated_units':duplicated_units,'residual_placeholders':residual,'headings':headings,'core_numbers':numeric,'tables':tables,'images':images,'semantic_bindings':'XML位置区分金额与比例','human_layout':'待全部页人工审核','scope':'文件结构与指标绑定；不是报告验收'}

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
                    for heading in headings:
                        if any(line.strip().startswith(heading) for line in lines):page_map.setdefault(heading,index)
                if not text.strip() or '{{' in text:return {'status':'FAILED','reason':'PDF_CONTENT_INVALID'}
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
                    if candidate.text.strip() and not re.match(r'^[一二三四五六]、|^[2-6]\.\d+(?:\.\d+)?\s+',candidate.text.strip()):break
                    start=candidate;previous=previous.getprevious()
                if not start.paragraph_format.page_break_before:
                    start.paragraph_format.page_break_before=True;layout_changed=True
        # 竖排目录逐行回填实际页码；目录标题行(带YH_TOC书签)保持不变
        toc_lines={'一、基本信息':'一、封面与基本信息','二、总成本概览':'二、总成本概览','三、要素明细':'三、成本要素明细分析','四、专项分析':'四、重点产品专项分析','五、对标分析':'五、对标分析','六、总结与建议':'六、总结与建议'}
        toc_updated=False
        for paragraph in d.paragraphs:
            text=paragraph.text.strip()
            # 目录行以全角空格开头；真实章节标题不以全角空格开头，避免污染正文
            if not text.startswith(chr(0x3000)):continue
            key=next((k for k in toc_lines if text.lstrip(chr(0x3000)).split('　')[0].startswith(k)),None)
            if key is None or paragraph is toc:continue
            page=page_map.get(toc_lines[key])
            fresh=chr(0x3000)+key+('　·　第'+str(page)+'页' if page else '')
            if paragraph.text!=fresh:_text(paragraph,paragraph.text,fresh);toc_updated=True
        if _toc_pass<5 and (layout_changed or toc_updated):
            d.save(path)
            return convert_pdf(path,timeout,converter,_toc_pass+1)
        return {'status':'PASS','scope':'file_conversion','toc_updated':len(page_map)==6,'orphan_headings':orphan_headings,'toc_pages':page_map,'path':str(pdf),'pages':pages,'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()}
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
    if meta.get('reader_template_version')=='reader-v2':return
    body=d.element.body
    heading=next(p._p for p in d.paragraphs if p.text=='一、封面与基本信息')
    for child in list(body):
        if child is heading:break
        body.remove(child)
    # Existing blank同比 cells are omissions, not missing data.
    overview=next(t for t in d.tables if any('去年同月' in c.text for c in t.rows[0].cells))
    for row,cn in zip(overview.rows[4:7],['材料','人工','制造费用']):
        for index,field,ratio in [(4,'去年'+cn+'成本' if cn!='制造费用' else '去年制造费用',False),(5,cn+'成本同比',True)]:
            p=row.cells[index].paragraphs[0];p.text='{{'+field+'}}'+('%' if ratio else '')
            marker='YH_reader_'+field
            mark=OxmlElement('w:bookmarkStart');mark.set(qn('w:id'),str(22000+len(meta['placeholders'])));mark.set(qn('w:name'),marker);p._p.insert(0,mark)
            end=OxmlElement('w:bookmarkEnd');end.set(qn('w:id'),mark.get(qn('w:id')));p._p.append(end)
            meta['placeholders'].append({'original':field,'field':field,'context':p.text,'marker':marker,'xml_part':'word/document.xml','source':'period_values.yoy.elements_unit / elements.comparisons.yoy.unit.rate','unit':'%' if ratio else '元/盒'})
    for p in _all_paragraphs(d):
        for br in list(p._p.iter(qn('w:br'))):
            if br.get(qn('w:type'))=='page':br.getparent().remove(br)
        pp=p._p.find(qn('w:pPr'))
        if pp is not None:
            for tag in ('sectPr','pageBreakBefore'):
                for x in list(pp.findall(qn('w:'+tag))):pp.remove(x)
    style_reader(d)
    d.save(output)
    meta['reader_template_version']='reader-v2'
    meta['template_hash']=hashlib.sha256(Path(output).read_bytes()).hexdigest()
    meta['working_changes']=['移除重复封面、空文控表和不适用阅读指南','六个赛题固定章节保留','同比三要素单独绑定','中文字体与A4样式统一']
    Path(map_path).write_text(json.dumps(meta,ensure_ascii=False,indent=2))


def style_reader(doc):
    from docx.shared import Pt,Cm,RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    for section in doc.sections:
        section.page_width=Cm(21);section.page_height=Cm(29.7)
        section.top_margin=Cm(1.7);section.bottom_margin=Cm(1.6)
        section.left_margin=Cm(1.7);section.right_margin=Cm(1.7)
    for name in ('Normal','Body Text','Table Normal','Title','Heading 1','Heading 2','Heading 3'):
        if name not in doc.styles:continue
        st=doc.styles[name];st.font.name='Noto Sans SC';st.font.size=Pt(10.5)
        st.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'Noto Sans SC')
        st.paragraph_format.line_spacing=1.18;st.paragraph_format.space_after=Pt(5)
    for p in _all_paragraphs(doc):
        text=p.text.strip();fmt=p.paragraph_format
        fmt.page_break_before=False;fmt.widow_control=True
        fmt.line_spacing=1.15;fmt.space_before=Pt(0);fmt.space_after=Pt(5)
        heading=bool(re.match(r'^[一二三四五六]、|^[2-6]\.\d+(?:\.\d+)?\s+',text)) or text=='来源与审核说明'
        fmt.keep_with_next=heading or '｜' in text or (not text and bool(p._p.xpath('.//w:bookmarkStart')))
        if not text and not p._p.xpath('.//w:drawing'):fmt.space_after=Pt(0);fmt.line_spacing=Pt(1)
        if text.endswith('成本分析报告'):fmt.keep_with_next=True
        fmt.keep_together=True
        if heading:fmt.space_before=Pt(10);fmt.space_after=Pt(5)
        for r in p.runs:
            r.font.name='Noto Sans SC';r.font.size=Pt(20 if text.endswith('成本分析报告') else 14 if re.match('^[一二三四五六]、',text) else 11.5 if heading else 10.5)
            r.font.bold=heading;r.font.color.rgb=RGBColor.from_string('143D50' if heading else '202D33')
            rp=r._element.get_or_add_rPr();rp.get_or_add_rFonts().set(qn('w:eastAsia'),'Noto Sans SC')
            for tag in ('spacing','position','szCs'):
                for child in list(rp.findall(qn('w:'+tag))):rp.remove(child)
    for t in doc.tables:
        t.autofit=False
        widths=[2.4,2.35,2.35,1.8,2.35,1.8,2.35,1.8] if len(t.columns)==8 else [17.3/len(t.columns)]*len(t.columns)
        for col,width in zip(t.columns,widths):col.width=Cm(width)
        for row in t.rows:
            for cell,width in zip(row.cells,widths):cell.width=Cm(width)
        for i,row in enumerate(t.rows):
            trpr=row._tr.get_or_add_trPr()
            for h in list(trpr.findall(qn('w:trHeight'))):trpr.remove(h)
            if trpr.find(qn('w:cantSplit')) is None:trpr.append(OxmlElement('w:cantSplit'))
            if i==0 and trpr.find(qn('w:tblHeader')) is None:trpr.append(OxmlElement('w:tblHeader'))
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.keep_with_next=False;p.paragraph_format.space_after=Pt(3);p.paragraph_format.line_spacing=1.08
                    for r in p.runs:r.font.size=Pt(9);r.font.bold=i==0
                if i==0:
                    pr=cell._tc.get_or_add_tcPr();shd=OxmlElement('w:shd');shd.set(qn('w:fill'),'EAF2F5');pr.append(shd)
    # Remove layout-only empty paragraphs, keeping anchors/bookmarks and drawings.
    for p in list(doc.paragraphs):
        if not p.text.strip() and not p._p.xpath('.//w:drawing | .//w:bookmarkStart | .//w:sectPr'):
            p._p.getparent().remove(p._p)


def add_reader_summary(doc,snapshot,narrative,output):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt
    first=doc.paragraphs[0]
    title=first.insert_paragraph_before(snapshot['product']+'成本分析报告')
    title.paragraph_format.keep_with_next=True
    m=snapshot['metrics'];label=snapshot['period']['start']+' 至 '+snapshot['period']['end']
    first.insert_paragraph_before(snapshot['factory']+' · '+label+' · '+snapshot.get('specification',''))
    first.insert_paragraph_before('报告编号：'+output.parent.name+'；人工审核：待审核。')
    mode='本次采用基础分析，原因解释待复核。' if not narrative.get('model_live') or narrative.get('status')!='PASS' else '本次采用模型辅助解释；因果归因仍待人工复核。'
    first.insert_paragraph_before(mode)
    ranked=sorted(snapshot['elements'],key=lambda e:abs(Decimal(e.get('unit_delta') or '0')),reverse=True)
    lead=ranked[0]
    first.insert_paragraph_before('核心发现：单位成本 '+number(m['unit_cost'])+' 元/盒，总成本 '+number(m['total_cost'])+' 元；较上期变动最大的要素为'+lead['name']+'，每盒变动 '+number(lead.get('unit_delta'))+' 元。建议先核对该要素原始明细，再安排责任部门复核。')
    toc_items=['一、基本信息','二、总成本概览','三、要素明细','四、专项分析','五、对标分析','六、总结与建议']
    toc=first.insert_paragraph_before('目录')
    for item in toc_items:
        line=first.insert_paragraph_before('　'+item)
        line.paragraph_format.space_after=Pt(0);line.paragraph_format.keep_with_next=True
    mark=OxmlElement('w:bookmarkStart');mark.set(qn('w:id'),'30000');mark.set(qn('w:name'),'YH_TOC');toc._p.insert(0,mark)


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
    def insert(fig,name,anchor,title):
        fig.tight_layout();path=output.with_name(name+'.png');fig.savefig(path,dpi=190,bbox_inches='tight');plt.close(fig)
        cap=doc.add_paragraph(title);cap.paragraph_format.keep_with_next=True
        pic=doc.add_paragraph();pic.add_run().add_picture(str(path),width=Cm(17))
        anchor.addnext(cap._p);cap._p.addnext(pic._p)
    trend=snapshot['trend'];fig,ax=plt.subplots(figsize=(8,2.5))
    vals=[float(r['unit_cost']) for r in trend];ax.plot([r['month'] for r in trend],vals,'o-',color='#176C8C');ax.set_ylabel('单位成本（元/盒）')
    span=max(vals)-min(vals);margin=max(span*.6,max(vals)*.07);ax.set_ylim(max(0,min(vals)-margin),max(vals)+margin)
    for i,v in enumerate(vals):ax.annotate(f'{v:.2f}',(i,v),xytext=(0,7),textcoords='offset points',ha='center')
    ax.grid(axis='y',alpha=.2);insert(fig,'trend',anchors['近6个月成本趋势表格']._p,snapshot['product']+' · '+snapshot['factory']+' · '+trend[0]['month']+' 至 '+trend[-1]['month']+'｜单位成本趋势（纵轴范围见刻度）')
    fig,ax=plt.subplots(figsize=(8,2.1));els=snapshot['elements'];vals=[float(e['unit']) for e in els]
    ax.barh([e['name'] for e in els],vals,color=['#176C8C','#46978D','#82939F']);ax.set_xlim(0,max(vals)*1.35);ax.set_xlabel('元/盒（零基线）')
    for i,(v,e) in enumerate(zip(vals,els)):ax.text(v+.02,i,f'{v:.2f} / {number(e["share"])}%',va='center')
    anchor=next(p._p for p in doc.paragraphs if p.text.startswith('2.2'))
    insert(fig,'structure',anchor,subtitle+'｜三要素单位成本与占比')
    base=snapshot.get('comparison',{}).get('mom',{}).get('base');current=snapshot['metrics']['unit_cost']['value']
    if base is not None:
        fig,ax=plt.subplots(figsize=(8,2.6));running=float(base);xs=['上期']+[e['name'] for e in els]+['本期']
        ax.bar(0,running,color='#82939F')
        ax.text(0,running,f'{running:.2f}',ha='center',va='bottom')
        for i,e in enumerate(els,1):
            v=float(e.get('unit_delta') or 0);bottom=min(running,running+v);ax.bar(i,abs(v),bottom=bottom,color='#A56B3D' if v>=0 else '#176C8C');ax.text(i,max(running,running+v)+.04,(('+' if v>=0 else '')+number(e.get('unit_delta') or 0)),ha='center');running+=v
        ax.bar(4,float(current),color='#176C8C');ax.text(4,float(current),number(current),ha='center',va='bottom');ax.set_xticks(range(5),xs);ax.set_ylim(0,max(float(base),float(current))*1.22);ax.set_ylabel('元/盒（零基线）')
        insert(fig,'waterfall',anchor,subtitle+'｜上期至本期单位成本变动')
    be=(benchmark or {}).get('elements',[])
    if be:
        fig,ax=plt.subplots(figsize=(8,2.4));pos=list(range(len(be)))
        ax.bar([x-.18 for x in pos],[float(r['right']) for r in be],width=.35,label='一厂',color='#176C8C');ax.bar([x+.18 for x in pos],[float(r['left']) for r in be],width=.35,label='二厂',color='#82939F')
        for i,r in enumerate(be):peak=max(float(r['right']),float(r['left']));ax.text(i,peak+peak*.05,'差额 '+number(r['delta']),ha='center',bbox={'facecolor':'white','alpha':.8,'edgecolor':'none','pad':1.2})
        ax.set_xticks(pos,[r['name'] for r in be]);ax.set_ylabel('元/盒（零基线）');ax.set_ylim(0,max(float(r[k]) for r in be for k in ('left','right'))*1.3);ax.legend(ncol=2)
        insert(fig,'benchmark',anchors['对标差异表格']._p,snapshot['product']+' · '+period_label+'｜跨厂三要素（差额＝二厂−一厂）')


def assess_report(result,review=None):
    """File checks are necessary but never sufficient for business acceptance.

    Human dimensions come only from a stored review bound to the current
    artifact bytes; without it they stay PENDING, never auto-signed."""
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
    r={
      'file_openable':verdict(dx.get('status')=='PASS' and pdf.get('status')=='PASS','DOCX结构检查与PDF实际打开'),
      'calculation_consistency':verdict(checks.get('core_numbers') and checks.get('numeric_bindings_checked',0)>=70 and not checks.get('numeric_binding_failures'),'固定快照与模板位置逐项核对'),
      'section_completeness':human('section_completeness','六个固定章节的业务实质待真人评审'),
      'evidence_applicability':verdict(evidence_ok and bool(n.get('evidence_applicability_checked')) and not claim_failures,f'逐条核对{claims_checked}项结论的证据引用与适用性；'+('全部通过' if not claim_failures else '；'.join(claim_failures[:5]))),
      'readability':human('readability','真人可读性评审待完成'),
      'visual_quality':human('visual_quality','逐页渲染检查与真人版式审核待完成'),
      'task_actionability':verdict(bool(actions) and all(f.get('verification_target') and f.get('expected_evidence') and f.get('responsible_role') and f.get('deadline_basis') for f in actions),'建议必须包含对象、预期证据、责任角色和期限依据'),
      'model_participation':verdict(n.get('model_live') is True and n.get('status')=='PASS','模型实际参与、身份核验一致且解释覆盖校验通过；基础分析不视为模型通过')}
    r['overall']='PASS' if all(v['status']=='PASS' for v in r.values()) else 'FAIL' if any(v['status']=='FAIL' for v in r.values()) else 'PENDING'
    if review:
        r['human_attribution_score']=review.get('attribution_score')
        r['human_review_comment']=review.get('comment','')
    r['policy']='强制环节逐项通过后才能认定报告合格；人工评审缺失保持待评，产物变化使既有审核失效'
    return r
