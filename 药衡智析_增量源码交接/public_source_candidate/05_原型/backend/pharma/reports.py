"""原 Word 模板的 XML 定位绑定、保留 run 样式、逐任务 PDF 转换。"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
# 改写 docx 部件必须用 lxml：标准库 ElementTree 重序列化会把命名空间前缀
# 统一改成 ns0:/ns1:…，根元素 mc:Ignorable="w14 w15 wp14" 随即引用未声明
# 前缀，MS Word 判定文件损坏拒开（LibreOffice 宽容，2026-09-22 事故）。
# ET 仅保留给 verify_docx 等只读解析。
from lxml import etree as LET
from .docx_compat import validate_word_compat
import hashlib, json, os, re, shutil, subprocess, tempfile
from datetime import datetime
from decimal import Decimal
from .config import ROOT, PACKAGE, ARTIFACTS, RUNTIME
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W}
PATTERN = re.compile(r'\{\{([^{}]+)\}\}')
RESIDUAL = re.compile(r'\{\{[^{}]*\}\}|\[\[[^\[\]]*\]\]')
# 工作模板（由赛题原件规范化生成）默认落在仓库 04_方案与文档/；
# 容器与只读部署用 PHARMA_TEMPLATE_DIR 指向可写持久目录。
_TEMPLATE_DIR = Path(os.environ.get('PHARMA_TEMPLATE_DIR', str(ROOT / '04_方案与文档')))
TEMPLATE = _TEMPLATE_DIR / '月度成本分析报告工作模板.docx'
MAP_PATH = _TEMPLATE_DIR / 'placeholder_map.json'
# 用户安装模板（数据中心“报告模板”解析后安装）：按报告类型存放；
# 季度/专题未安装时回退月度模板（绑定合同一致，仅期间口径不同）。
RUNTIME_TEMPLATES = RUNTIME / 'templates'
RENDERER_VERSION='reader-20260923-caption-v9'
NA = 'N/A（无可用基期或明细）'


def working_template(analysis_type='monthly'):
    """按报告类型解析当前模板：已安装模板优先，否则回退题包月度工作模板。

    返回 (模板路径, 占位符清单路径)；安装目录无对应文件或清单缺失均回退。
    """
    analysis_type = analysis_type if analysis_type in ('monthly', 'quarterly', 'special') else 'monthly'
    installed = RUNTIME_TEMPLATES / f'{analysis_type}.docx'
    installed_map = RUNTIME_TEMPLATES / f'{analysis_type}.placeholder_map.json'
    if installed.is_file() and installed_map.is_file():
        return installed, installed_map
    return TEMPLATE, MAP_PATH


def installed_templates() -> list[dict]:
    """已安装模板清单（数据中心报告模板页展示）。"""
    result = []
    for analysis_type, label in (('monthly', '月度成本分析'), ('quarterly', '季度成本分析'), ('special', '专题分析')):
        path, map_path = working_template(analysis_type)
        installed = path.parent == RUNTIME_TEMPLATES
        meta = {}
        if installed and map_path.is_file():
            try: meta = json.loads(map_path.read_text(encoding='utf-8'))
            except (OSError, ValueError): meta = {}
        result.append({'analysis_type': analysis_type, 'label': label, 'installed': installed,
                       'path': str(path), 'placeholder_count': len(meta.get('placeholders', [])),
                       'template_hash': meta.get('template_hash'),
                       'installed_at': meta.get('installed_at')})
    return result


def install_template(source: Path, analysis_type: str) -> dict:
    """安装用户上传的报告模板：通用 {{占位符}}→书签规范化后写入运行时模板目录。

    与题包专属的 normalize_template 区分：不做题包段落级修正与 compact 手术，
    占位符按题包绑定合同改名（“人工环比%”等比例位 → _比例 后缀，与
    build_bindings 的键一致）；书签供 verify_docx 逐项核对。安装后执行与
    compact_working_template 相同的通用前置区手术（解除前置区强制分页、清理
    目录域字符——LibreOffice 对域后内容强制分页的教训，2026-09-21 d5e343a），
    跳过题包专属的同比表格补绑定。渲染绑定按占位符名称合同执行。
    """
    if analysis_type not in ('monthly', 'quarterly', 'special'):
        raise ValueError('UNKNOWN_TEMPLATE_TYPE')
    RUNTIME_TEMPLATES.mkdir(parents=True, exist_ok=True)
    source = Path(source)
    output = RUNTIME_TEMPLATES / f'{analysis_type}.docx'
    map_path = RUNTIME_TEMPLATES / f'{analysis_type}.placeholder_map.json'
    entries = []
    with ZipFile(source) as zin, ZipFile(output, 'w', ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            raw = zin.read(info.filename)
            if info.filename.startswith('word/') and info.filename.endswith('.xml'):
                xml = LET.fromstring(raw)
                for i, p in enumerate(xml.findall('.//w:p', NS)):
                    nodes = p.findall('.//w:t', NS)
                    text = ''.join(t.text or '' for t in nodes)
                    marker = 'YHU_' + hashlib.sha256((analysis_type + info.filename).encode()).hexdigest()[:8] + '_' + str(i)
                    if PATTERN.search(text):
                        mark = LET.Element('{' + W + '}bookmarkStart', {'{' + W + '}id': str(20000 + i), '{' + W + '}name': marker})
                        p.insert(0, mark)
                        p.append(LET.Element('{' + W + '}bookmarkEnd', {'{' + W + '}id': str(20000 + i)}))
                    for match in PATTERN.finditer(text):
                        name = match.group(1)
                        ratio = text[match.end():].lstrip().startswith('%')
                        # 题包绑定合同的改名规则（normalize_template 同款）：比例/
                        # 金额后缀区分同名占位符，保证 build_bindings 键命中；
                        # 改写走 replace_text_nodes 保留 run 样式。
                        field = name + '_' + ('比例' if ratio else '金额') \
                            if name in ('人工环比', '制造费用环比') else name
                        if field != name:
                            replace_text_nodes(nodes, {name: '{{' + field + '}}'})
                        semantic, unit = binding_semantics(field, ratio)
                        entries.append({'original': name, 'field': field, 'xml_part': info.filename,
                                        'paragraph_index': i, 'marker': marker, 'context': text,
                                        'unit': unit, 'source': semantic,
                                        'missing_policy': 'N/A并说明缺值原因',
                                        'semantic': name + ('变动率' if ratio else '')})
                raw = LET.tostring(xml, encoding='utf-8', xml_declaration=True)
            zout.writestr(info, raw)
    # 通用前置区手术：与 compact_working_template 同源逻辑（安全子集）。
    yoy_note = _relayout_front_section(output, entries)
    validate_word_compat(output)
    result = {'analysis_type': analysis_type, 'source': str(source), 'source_filename': source.name,
              'template_hash': hashlib.sha256(output.read_bytes()).hexdigest(),
              'placeholders': entries, 'placeholder_count': len(entries),
              'yoy_binding_note': yoy_note,
              'installed_at': datetime.now().isoformat(), 'reader_template_version': 'installed-v1'}
    map_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


# 同比补绑定的行/列语义锚点（2026-09-23 审计 AUD-TPL-01：此前按 rows[4:7]/列4-5
# 硬编码，用户模板行序不同会写错单元格）。按表头与首列文字定位，找不到即跳过。
_YOY_ELEMENT_ROW_KEYS = (('材料', ('直接材料', '材料')), ('人工', ('直接人工',)), ('制造费用', ('制造费用',)))


def _locate_overview_yoy_cells(overview):
    """在"总成本概览"表中按文字定位 去年同月列/同比列/三要素行。

    返回 (yoy_col, rate_col, {要素名: 行}, 跳过原因列表)；列或某行未命中时
    对应项为 None 并记录原因，调用方只补绑成功命中的单元格。
    """
    header = [c.text.strip() for c in overview.rows[0].cells]
    yoy_col = next((i for i, h in enumerate(header) if '去年同月' in h), None)
    rate_col = next((i for i, h in enumerate(header) if '同比' in h and ('变动' in h or '率' in h)), None)
    skipped = []
    if yoy_col is None:
        skipped.append('表头未找到“去年同月”列')
    if rate_col is None:
        skipped.append('表头未找到“同比”列')
    rows = {}
    for row in overview.rows[1:]:
        first = row.cells[0].text.strip() if row.cells else ''
        if not first:
            continue
        for cn, keys in _YOY_ELEMENT_ROW_KEYS:
            if any(k in first for k in keys) and cn not in rows:
                rows[cn] = row
                break
    for cn, _keys in _YOY_ELEMENT_ROW_KEYS:
        if cn not in rows:
            skipped.append(f'未找到“{cn}”数据行')
    return yoy_col, rate_col, rows, skipped


def _bind_overview_yoy_cell(row, col, field, ratio, entries, book_id_base):
    """在指定行/列写同比占位符并加书签；返回占位符条目。"""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    p = row.cells[col].paragraphs[0]
    p.text = '{{' + field + '}}' + ('%' if ratio else '')
    marker = 'YH_reader_' + field
    mark = OxmlElement('w:bookmarkStart')
    mark.set(qn('w:id'), str(book_id_base + len(entries)))
    mark.set(qn('w:name'), marker)
    p._p.insert(0, mark)
    end = OxmlElement('w:bookmarkEnd')
    end.set(qn('w:id'), mark.get(qn('w:id')))
    p._p.append(end)
    entry = {'original': field, 'field': field, 'context': p.text,
             'marker': marker, 'xml_part': 'word/document.xml',
             'source': 'period_values.yoy.elements_unit / elements.comparisons.yoy.unit.rate',
             'unit': '%' if ratio else '元/盒'}
    entries.append(entry)
    return entry


def _relayout_front_section(path, entries):
    """安装模板的通用手术（compact_working_template 安全子集）：

    ① 前置区（正文首章“一、封面与基本信息”之前）解除强制分页/分节、移除
    目录域字符与“更新域”提示行；正文首章强制新起一页。章节缺失（不会发生：
    安装前 check_template 已要求六章节）时跳过分页调整。
    ② 总成本概览表“去年同月/同比”空白单元格补占位符绑定（题包原件的这些
    单元格是遗漏而非缺数）；按表头文字定位（2026-09-23 修复：不再按行/列
    索引硬编码），模板无该表或行/列未命中时安全跳过并在返回值标注。

    返回补绑定说明（str）：全部命中返回绑定数量；有跳过返回跳过原因。
    """
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    d = Document(path)
    paras = _all_paragraphs(d)
    body_start = next((pp for pp in paras if pp.text.strip() == '一、封面与基本信息'), None)
    in_front = True
    for pp in paras:
        if body_start is not None and pp._p is body_start._p:
            in_front = False
        if not in_front:
            continue
        for br in list(pp._p.iter(qn('w:br'))):
            if br.get(qn('w:type')) == 'page':
                br.getparent().remove(br)
        ppr = pp._p.find(qn('w:pPr'))
        if ppr is not None:
            for tag in ('pageBreakBefore', 'sectPr'):
                for x in list(ppr.findall(qn('w:' + tag))):
                    ppr.remove(x)
        for r_el in list(pp._p.iter(qn('w:r'))):
            if r_el.find(qn('w:fldChar')) is not None or r_el.find(qn('w:instrText')) is not None:
                pp_ = r_el.getparent()
                if pp_ is not None:
                    pp_.remove(r_el)
        if pp.text.strip().startswith('（右键点击此处'):
            pp._p.getparent().remove(pp._p)
    if body_start is not None:
        body_start.paragraph_format.page_break_before = True
    overview = next((t for t in d.tables if any('去年同月' in c.text for c in t.rows[0].cells)), None)
    if overview is None:
        d.save(path)
        return '未找到“总成本概览”表，跳过同比补绑定（渲染时对应占位符按缺值 N/A 处理）'
    yoy_col, rate_col, element_rows, skipped = _locate_overview_yoy_cells(overview)
    bound = 0
    for cn in ('材料', '人工', '制造费用'):
        row = element_rows.get(cn)
        if row is None or yoy_col is None or rate_col is None:
            continue
        field_amount = '去年' + cn + '成本' if cn != '制造费用' else '去年制造费用'
        _bind_overview_yoy_cell(row, yoy_col, field_amount, False, entries, 23000)
        _bind_overview_yoy_cell(row, rate_col, cn + '成本同比', True, entries, 23000)
        bound += 2
    d.save(path)
    if bound:
        return f'同比补绑定 {bound} 个单元格' if not skipped else f'同比补绑定 {bound} 个单元格；跳过：{"；".join(skipped)}'
    return '同比补绑定全部跳过：' + '；'.join(skipped)

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
                xml=LET.fromstring(raw)
                for i,p in enumerate(xml.findall('.//w:p',NS)):
                    nodes=p.findall('.//w:t',NS);text=''.join(t.text or '' for t in nodes)
                    rename={}
                    if info.filename=='word/document.xml' and i==235 and text=='100%':
                        nodes[0].text='{{合计贡献度}}%'
                        for n in nodes[1:]:n.text=''
                        text='{{合计贡献度}}%'
                    marker='YH_'+hashlib.sha256(info.filename.encode()).hexdigest()[:8]+'_'+str(i)
                    if PATTERN.search(text):
                        mark=LET.Element('{'+W+'}bookmarkStart',{'{'+W+'}id':str(10000+i),'{'+W+'}name':marker});p.insert(0,mark)
                        p.append(LET.Element('{'+W+'}bookmarkEnd',{'{'+W+'}id':str(10000+i)}))
                    for match in PATTERN.finditer(text):
                        name=match.group(1)
                        if name!='合计贡献度':original_names.append(name)
                        ratio=text[match.end():].lstrip().startswith('%')
                        field=name+'_'+('比例' if ratio else '金额') if name in ('人工环比','制造费用环比') else name
                        rename[name]='{{'+field+'}}'
                        entries.append({'original':name,'field':field,'xml_part':info.filename,'paragraph_index':i,'marker':marker,'context':text,'unit':binding_semantics(field,ratio)[1],'source':binding_semantics(field,ratio)[0],'missing_policy':'N/A并说明缺值原因','semantic':name+('变动率' if ratio else '')})
                    replace_text_nodes(nodes,rename)
                # 2026-09-21 五轮修正（用户最终裁定）：水印保留原文字
                # （"重庆创灵境数字技术有限公司"textpath 原样），不剥离不改写。
                # 此前"显示错误"的两处根因均已修复：①文字被 sanitize 改写为
                # "药衡智析 · 成本分析"——该改写已删除；②水印仅在 1 页显示——
                # 旧版 compact 全局删分节把带水印的正文页眉压缩到 1 页，现仅
                # 前置区解除分节、正文分节原样保留，水印随正文页眉每页正确显示。
                raw=LET.tostring(xml,encoding='utf-8',xml_declaration=True)
            zout.writestr(info,raw)
    result={'original_hash':hashlib.sha256(original.read_bytes()).hexdigest(),'template_hash':hashlib.sha256(output.read_bytes()).hexdigest(),'original_unique':len(set(original_names)),'original_occurrences':len(original_names),'placeholders':entries}
    Path(map_path).write_text(json.dumps(result,ensure_ascii=False,indent=2))
    compact_working_template(output, map_path)
    validate_word_compat(output)
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

    仅用 U+00A0 绑定数字与单位（Word 正常显示为空格）。2026-09-22 之前还
    在数字边界注入 U+FEFF：Word 部分版本将其渲染为可见异常符号（用户在
    目录数字与"7.26 元"处看到），故彻底停注；layout_text 在每次进入时
    清除历史残留。"""
    nodes = list(paragraph._p.iter('{'+W+'}t'))
    for node in nodes:
        node.text = layout_text(node.text or '')
    text = ''.join(node.text or '' for node in nodes)
    if RESIDUAL.search(text):
        return
    unit = r'(?:万元|元|kWh|kg|吨|盒|粒|袋|支|件|小时|分钟|万盒|%|％)(?:/(?:kg|吨|盒|粒|袋|支|件|小时|分钟|万盒))?'
    pattern = r'(?<![A-Za-z0-9_.])[-+−]?\d+(?:,\d{3})*(?:\.\d+)?[ \u00a0]*' + unit
    unbreakable_spaces = set()
    for match in re.finditer(pattern, text):
        unbreakable_spaces.update(i for i in range(match.start(),match.end()) if text[i]==' ')
    offset = 0
    for node in nodes:
        original = node.text or ''
        node.text = ''.join(('\u00a0' if offset+i in unbreakable_spaces else char) for i,char in enumerate(original))
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
        # P2-10（2026-09-23 视觉审查）：亮点数字此前直引题包静态行（11.9%/0.29），
        # 与报告自身表格（按本月数据计算 11.78%/0.2963→0.30）矛盾；统一改用
        # 本报告同源计算值，方向判断仍对照行业 P50。
        if str(row.get('指标',''))=='人工成本占比' and row.get('行业P50'):
            try:
                _share=Decimal(str(els['labor']['unit']))/Decimal(str(m['unit_cost']))*100
                if _share<Decimal(str(row['行业P50']).rstrip('%')):
                    highlights.append('人工成本占比 '+f'{_share:.2f}%'+' 低于行业中位 '+str(row['行业P50'])+'（题包静态参考）')
            except Exception:pass
        if str(row.get('指标',''))=='单位成本(元/粒)' and row.get('行业P50'):
            try:
                _dv=(snapshot.get('industry') or {}).get('divisor')
                _per=_per=None
                if _dv: _per=Decimal(str(m['unit_cost']))/Decimal(str(_dv))
                _shown=(f'{_per:.2f}' if _per is not None else str(row.get('本厂水平(中药一厂)')))
                if _per is None or _per<=Decimal(str(row['行业P50'])):
                    highlights.append('单位成本 '+_shown+' 元/粒 不高于行业中位 '+str(row['行业P50'])+'（题包静态参考）')
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
        validate_word_compat(output)
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
    template_path, template_map = working_template(snapshot.get('analysis_type', 'monthly'))
    if template_path == TEMPLATE:
        if not TEMPLATE.exists():normalize_template()
        elif json.loads(MAP_PATH.read_text()).get('reader_template_version') not in ('reader-v2','reader-v3-truetype'):compact_working_template(TEMPLATE,MAP_PATH)
    meta=json.loads(template_map.read_text());doc=Document(template_path)
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
        replacements=[
            # P2-6（2026-09-23 视觉审查）：题包提案模板残留清理——封面副标题
            # "整体解决方案"与《季度成本分析报告》语义冲突；阅读指南"可选
            # 组件/并非一次性全部实施"是解决方案提案语言。
            ('整体解决方案','产品成本智能分析报告'),
            ('均为可选组件，并非一次性全部实施','按报告使用方的权限与场景按需提供'),
            ('明确技术架构、实施计划、系统配置','维护系统配置与账号权限'),
        ]
        if snapshot['analysis_type']=='quarterly':
            replacements += [('本月','本季度'),('上月','上季度'),('去年同月','去年同季'),('分析月份','分析期间')]
        rewrite_template_prose(p,replacements)
        replace_text_nodes(list(p._p.iter('{'+W+'}t')),values)
        # P2-5（2026-09-23 视觉审查）：封面副标题原段落自带深色底纹/边框，
        # 在白底封面上呈"悬浮黑条"。副标题语义已替换，装饰性底纹一并清除。
        if '产品成本智能分析报告' in p.text and ('整体解决方案' in before):
            ppr=p._p.find(qn('w:pPr'))
            if ppr is not None:
                for tag in ('w:shd','w:pBdr'):
                    for x in list(ppr.findall(qn(tag))):ppr.remove(x)
        if 'N/A' in p.text:_text(p,'）%','）')
        if before.startswith(('一、','二、','三、','四、','五、','六、')):sections.append(p.text)
    # P2-5（2026-09-23 视觉审查）：封面黑条根因是题包模板"Title Bar"段落
    # 样式自带 w:val="solid" 实心底纹，封面上的空样式段落整段渲染为横贯
    # 黑条。把该样式的底纹改为 clear（保留其余版式定义），全局生效。
    for _st in doc.styles.element.findall(qn('w:style')):
        _nm=_st.find(qn('w:name'))
        if _nm is None or _nm.get(qn('w:val'))!='Title Bar':continue
        _ppr=_st.find(qn('w:pPr'))
        if _ppr is None:continue
        _shd=_ppr.find(qn('w:shd'))
        if _shd is not None:
            _shd.set(qn('w:val'),'clear');_shd.set(qn('w:color'),'auto');_shd.set(qn('w:fill'),'auto')
    # P3（视觉审查）：封面落款三行（文件版本/编制日期/编制单位）首行缩进
    # 不一致导致左缘参差——统一清除缩进并对齐到同一起点。
    for p in _all_paragraphs(doc):
        if any(k in p.text for k in ('文件版本','编制日期','编制单位')) and len(p.text.strip())<40:
            ppr=p._p.find(qn('w:pPr'))
            if ppr is None:continue
            ind=ppr.find(qn('w:ind'))
            if ind is not None:
                for attr in ('w:firstLine','w:left','w:hanging'):
                    if ind.get(qn(attr)) is not None:ind.set(qn(attr),'0')
    for section in doc.sections:
        for part in [section.header,section.footer]:
            for p in part.paragraphs:
                replace_text_nodes(list(p._p.iter('{'+W+'}t')),values)
            pg=section._sectPr.find(qn('w:pgNumType'))
            if pg is not None:pg.attrib.pop(qn('w:start'),None)
    dynamic_tbl_specs=[]  # 书签 YHU_TBL_i → 语义名（供"表几-几"题注；lxml 代理 id() 不稳定，不可作键）
    def table(anchor,headers,rows,paragraph=None,caption=None):
        from docx.oxml import OxmlElement as _OE
        from docx.oxml.ns import qn as _qn
        from docx.enum.text import WD_ALIGN_PARAGRAPH as _TA
        p=paragraph if paragraph is not None else dynamic_anchors.get(anchor)
        if p is None:raise ValueError('模板动态块缺失:'+anchor)
        t=doc.add_table(rows=1,cols=len(headers))
        if doc.tables[0].style:t.style=doc.tables[0].style
        for cell,label in zip(t.rows[0].cells,headers):cell.text=str(label)
        for row in rows or [['N/A：无可用明细']+['—']*(len(headers)-1)]:
            for cell,val in zip(t.add_row().cells,row):cell.text=str(val if val is not None else NA)
        p._p.addnext(t._tbl)
        # 防御（2026-09-23 季度报告损坏根因）：锚点段落在表格单元格内时，
        # 单元格必须以 w:p 结尾——OOXML 要求 tc 的最后一个块是段落，否则
        # Word 判"文件损坏"。补一个空段收尾。
        if p._p.getparent().tag==_qn('w:tc') and (p._p.getnext() is None or p._p.getnext().tag==_qn('w:tbl')):
            _tail=_OE('w:p');t._tbl.addnext(_tail)
        idx=len(dynamic_tbl_specs)
        dynamic_tbl_specs.append(caption if caption is not None else (anchor or '').replace('表格',''))
        cell_p=t.rows[0].cells[0].paragraphs[0]._p
        bm=_OE('w:bookmarkStart');bm.set(_qn('w:id'),str(40000+idx));bm.set(_qn('w:name'),'YHU_TBL_'+str(idx))
        be=_OE('w:bookmarkEnd');be.set(_qn('w:id'),str(40000+idx))
        cell_p.insert(0,bm);cell_p.append(be)
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
            # cantSplit 无条件启用：长表仍可跨页（tblHeader 重复表头），但单个
            # 行不被从中间劈开——视觉审查 P1-1 伴生（序号14 行跨 p8/p9 断裂）。
            if trpr.find(_qn('w:cantSplit')) is None:trpr.append(_OE('w:cantSplit'))
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
        return number(v,2) if v not in (None,'') else '—'
    def _delta_pct(name):
        # 2026-09-23 修正：materials_summary.delta 是元/盒绝对额，此前直接
        # 拼 '%' 标成百分比（山茱萸 3.00←2.88 显示 -0.12%，实际 -4.17%）。
        # 现按 本月/上月单价 计算真实环比百分比。
        row=_ms_map.get(name,{})
        prev=row.get('previous');cur=row.get('current') or row.get('unit')
        try:
            p=float(prev);c=float(cur)
            if p>0:return ('+' if c>=p else '')+f'{(c-p)/p*100:.2f}%'
        except (TypeError,ValueError):pass
        try:
            v=float(row.get('delta'))
            return ('+' if v>0 else '')+f'{v:.2f}元/盒'  # 无基期时如实标注绝对额
        except (TypeError,ValueError):return '—'
    def _reason(name):
        c=_ms_map.get(name,{}).get('contribution')
        # P1-1（2026-09-23 视觉审查）：contribution 是 Decimal 聚合值，str() 直出
        # 20+ 位原始浮点（"31.201353702460167…%"），统一走 number() 两位小数。
        return ('贡献材料变动 '+number(c)+'%（品种级），优先核查' if c is not None else '待核查（见4.2方向评估）')
    _mat_note_tbl=table('原材料成本明细表格',['序号','原材料名称','本月单价(元/盒)','上月单价(元/盒)','环比变动（品种级）','变动原因初步判断'],[[
        str(i+1),r['原材料名称'],r['单位消耗成本(元/盒)'],_prev(r['原材料名称']),_delta_pct(r['原材料名称']),_reason(r['原材料名称'])]
        for i,r in enumerate(details.get('materials',[]))])
    # P2-1（视觉审查）：每味药材分批多行、单价逐行不同，环比与贡献列是品种级
    # 聚合口径——表下补口径说明，避免按行核对时"单价与百分比矛盾"的误读。
    if _mat_note_tbl is not None:
        from docx.oxml import OxmlElement as _OE2
        from docx.oxml.ns import qn as _qn2
        _np=_OE2('w:p');_pPr=_OE2('w:pPr')
        _st=_OE2('w:rPr');_sz=_OE2('w:sz');_sz.set(_qn2('w:val'),'15');_st.append(_sz)
        _pPr.append(_st);_np.append(_pPr)
        _r=_OE2('w:r');_rt=_OE2('w:t');_rt.set(_qn2('xml:space'),'preserve')
        _rt.text='注：环比变动与贡献占比为品种级聚合口径（该品种各批次均价环比）；同品种不同批次单价存在差异属正常，行级批次价以原始明细为准。'
        _r.append(_rt);_np.append(_r)
        _mat_note_tbl._tbl.addnext(_np)
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
    _price_tbl=table('原材料价格跟踪表格',['原材料','年初价(元/kg)','本月价(元/kg)','涨幅','市场趋势','对材料成本影响'],_rows_m)
    # 药材涨跌排行图（2026-09-23 用户反馈 #11）：材料明细表旁用横向条形图
    # 直观呈现涨跌幅前 8 的药材（涨红跌绿），回答"哪些药材在拉动成本"。
    # 2026-09-23 修正：按真实环比百分比绘制（delta 是元/盒绝对额，此前轴标
    # % 却画了绝对额；牡丹皮等小幅药材标成无意义的 -0.0%）。
    def _mover_pct(r):
        try:
            p=float(r.get('previous'));c=float(r.get('current') or r.get('unit'))
            if p>0:return (c-p)/p*100
        except (TypeError,ValueError):pass
        return None
    _movers=sorted(((r,_mover_pct(r)) for r in _ms if _mover_pct(r) is not None),
                   key=lambda t:abs(t[1]),reverse=True)[:8]
    if _movers:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib import font_manager
        from docx.shared import Cm as _Cm
        cjk=str(ROOT/'05_原型/assets/fonts/NotoSansSC-Regular.ttf')
        if Path(cjk).is_file():font_manager.fontManager.addfont(cjk);_fam=font_manager.FontProperties(fname=cjk).get_name()
        else:_fam='sans-serif'
        plt.rcParams.update({'font.family':_fam,'font.size':9,'axes.unicode_minus':False,'axes.spines.top':False,'axes.spines.right':False})
        _mv=sorted(_movers,key=lambda t:t[1],reverse=True)  # 降序+倒y轴：最大涨幅在顶（审查P3：此前+4.8%沉底）
        vals=[v for _,v in _mv]
        fig,ax=plt.subplots(figsize=(6.8,max(2.2,0.38*len(_mv)+0.9)))
        ys=list(range(len(_mv)))
        ax.barh(ys,vals,color=['#1F6E5E' if v<0 else '#C0392B' for v in vals],zorder=3)
        ax.axvline(0,color='#3A3A3A',lw=1,zorder=2)
        ax.set_yticks(ys,[str(r.get('name')) for r,v in _mv])
        ax.invert_yaxis()
        vmax=max(abs(v) for v in vals) or 1;ax.set_xlim(min(min(vals)-vmax*0.38,-vmax*0.12),max(vals)+vmax*0.38)
        for y,v in zip(ys,vals):
            ax.text(v+(vmax*0.03 if v>=0 else -vmax*0.03),y,('+' if v>=0 else '−')+f'{abs(v):.1f}%',va='center',ha='left' if v>=0 else 'right',fontsize=8.5,color='#C0392B' if v>=0 else '#1F6E5E')
        ax.set_xlabel('本月单价环比涨跌幅（%）');ax.grid(axis='x',alpha=.2)
        # 图插在价格表之后（w:tbl.addnext），图题在图下方；编号走 _number_and_caption
        _mv_path=output.with_name('movers.png') if 'output' in dir() else None
        from docx.enum.text import WD_ALIGN_PARAGRAPH as _AL2
        fig.tight_layout();fig.savefig(output.with_name('movers.png'),dpi=190,bbox_inches='tight');plt.close(fig)
        _picp=doc.add_paragraph();_picp.alignment=_AL2.CENTER;_picp.paragraph_format.keep_with_next=True
        _picp.add_run().add_picture(str(output.with_name('movers.png')),width=_Cm(15))
        _price_tbl._tbl.addnext(_picp._p)
        _capp=doc.add_paragraph('图｜'+snapshot['product']+' · '+snapshot['factory']+' · '+snapshot['month']+'｜药材单价涨跌排行（前'+str(len(_mv))+'，涨红跌绿）')
        _picp._p.addnext(_capp._p)
    # 根因定位表（2026-09-22 方法论落地）：程序计算的多维归因（EP/JSD/Shapley/DiD），
    # 数字程序所有；插在 4.2 成本异常点排查标题之后。模板无对应占位符，独立锚定。
    _attr=snapshot.get('attribution') or {}
    if _attr.get('status')=='PASS' and (_attr.get('ranking') or []):
        # 锚点必须是正文级的 4.2 标题段：须在 body 直下（单元格内的 '4.25%'
        # 曾被 startswith('4.2') 误匹配，根因表插进概览表单元格里、单元格以
        # tbl 结尾缺收尾段落 → Word 判文件损坏，2026-09-23 季度报告实测）。
        anchor42=next((p for p in _all_paragraphs(doc)
                       if re.match(r'^4\.2[ 　]',p.text.strip())
                       and p._p.getparent().tag==qn('w:body')),None)
        if anchor42 is not None:
            cap=doc.add_paragraph()
            cap.add_run('根因定位（程序计算的多维归因，非模型结论；解释力=该根因解释的总变动占比，DiD为对照厂反事实估计）').font.size=Pt(9)
            anchor42._p.addnext(cap._p)
            _rk_rows=[[str(i+1),r['cause'],r['ep_pct'],r['direction'],f"{r['label']}（{float(r['score']):.2f}）" if str(r.get('score','')).replace('.','',1).replace('-','',1).isdigit() else f"{r['label']}（{r['score']}）",r['basis']]
                      for i,r in enumerate(_attr['ranking'][:5])]
            _did=_attr.get('did') or {}
            if _did.get('status')=='PASS':
                _rk_rows.append(['附','对照厂反事实（DiD，'+str(_did.get('control'))+'）',str(_did.get('tau'))+' 元/盒',
                                 '—','平行趋势'+str(_did.get('parallel_trend')),
                                 '安慰剂τ='+str(_did.get('placebo_tau') or '未检')+'；估计值，'+str(_did.get('assumption',''))[:40]])
            table(None,['排序','根因集','解释力/估计','方向','可能性(评分)','依据'],_rk_rows,paragraph=cap,caption='根因定位')
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
    add_reader_summary(doc,snapshot,narrative,output,benchmark=benchmark)
    # 编制说明与知识库引用（模板 md 尾部要求；引用位置取自本期检索证据）。
    # 2026-09-23 用户反馈：编制说明/知识库引用要成为小标题（进导航与目录）；
    # 人工归因评分要有可填写的区域（表单）而非一行文字。内容先建齐，再统一
    # 走美化/编号/字体管线。
    doc.add_paragraph('七、编制说明').style=doc.styles['Heading 2']
    doc.add_paragraph('本报告由成本智能分析系统自动生成，数据来源于ERP系统，分析文本由AI大模型结合行业知识库自动撰写。如有疑问请联系财务部。')
    doc.add_paragraph('数据说明：本报告使用比赛模拟数据。事实、原因假设与缺失证据分别标注；整改任务确认后仅模拟发送。')
    doc.add_paragraph('八、知识库引用').style=doc.styles['Heading 2']
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
    doc.add_paragraph('九、来源与审核说明').style=doc.styles['Heading 2']
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
    # 人工归因评分（2026-09-23 用户反馈 #8）：赛题要求真人 0—5 分评分，此前
    # 只有一行文字无处可填——改为评分表单，空格留待真人署名填写，系统不代填。
    doc.add_paragraph('十、人工归因评分').style=doc.styles['Heading 2']
    doc.add_paragraph('以下评分由真人评审填写（系统与模型不代填），0—5 分，5 为最好。引用只说明依据来源，不等于已证实因果。')
    _score=doc.add_table(rows=1,cols=4)
    for c,h in zip(_score.rows[0].cells,['评审维度','评分（0—5）','评审人（署名）','评审说明']):c.text=h
    for dim in ('归因准确性与证据支撑','内容可读性与结构完整性','逐页版式与图表质量','总体评价'):
        _score.add_row().cells[0].text=dim
    _spec_i=len(dynamic_tbl_specs);dynamic_tbl_specs.append('人工归因评分表')
    _cp=_score.rows[0].cells[0].paragraphs[0]._p
    _bm=OxmlElement('w:bookmarkStart');_bm.set(qn('w:id'),str(41000+_spec_i));_bm.set(qn('w:name'),'YHU_TBL_'+str(_spec_i))
    _be=OxmlElement('w:bookmarkEnd');_be.set(qn('w:id'),str(41000+_spec_i))
    _cp.insert(0,_bm);_cp.append(_be)
    # 表格统一美化 + 图表规范编号 + 前置区分页 + 中文版式统一（2026-09-23）。
    _layout_front_pages(doc)
    _beautify_native_tables(doc)
    _number_and_caption(doc,dynamic_tbl_specs)
    _standardize_typography(doc)
    style_reader(doc)
    audit=output.with_name('machine_audit.json')
    audit.write_text(json.dumps({'snapshot':snapshot,'narrative':narrative,'evidence':evidence,'benchmark':benchmark,'bindings':values},ensure_ascii=False,indent=2))
    temp=output.with_suffix('.tmp.docx');doc.save(temp)
    check=verify_docx(temp,snapshot,sections,narrative=narrative,placeholders=meta['placeholders'])
    if check['status']!='PASS':raise ValueError('报告验证失败:'+json.dumps(check,ensure_ascii=False))
    validate_word_compat(temp)
    temp.replace(output)
    return {'status':'PASS','scope':'file_generation','path':str(output),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'verification':check,'bindings':values}

def verify_docx(path,snapshot,sections=None,narrative=None,placeholders=None):
    if snapshot.get('context_id') and snapshot['context_id']!='pharmaceutical:competition':
        from .reference_report import verify
        result=verify(path,snapshot)
        result.update(explanation_presence(path,narrative,scoped=False))
        if result['explanation_binding_failures']:result['status']='FAIL'
        return result
    explanation_check=explanation_presence(path,narrative)
    # 书签核对必须用本次渲染的占位符清单（2026-09-22 修复）：用户安装模板的
    # 书签前缀/位置与题包 MAP 不同，死读题包 map 会把全部绑定误判为 null。
    if placeholders is None:placeholders=json.loads(MAP_PATH.read_text())['placeholders']
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
        for entry in placeholders:
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
            proc=subprocess.Popen([exe,f'-env:UserInstallation={profile.as_uri()}','--headless','--convert-to','pdf','--outdir',work,str(path)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=env)
            try:
                out,err=proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                # soffice.exe 与 venv python.exe 同为"启动器"型：真身 soffice.bin
                # 是其子进程，超时只 TerminateProcess 直接子进程会孤儿化 bin——
                # 残留进程还锁死临时 profile 目录（Windows 上 TemporaryDirectory
                # 清理会因此报错）。树杀一并回收（2026-09-23 同族排查 manage.py）。
                if os.name=='nt':subprocess.run(['taskkill','/F','/T','/PID',str(proc.pid)],capture_output=True)
                else:proc.kill()
                proc.communicate()
                return {'status':'FAILED','reason':'CONVERT_TIMEOUT'}
            if proc.returncode or not target.exists():return {'status':'FAILED','reason':'CONVERSION_FAILED','log':err[-1000:]}
            import fitz
            with fitz.open(target) as doc:
                text=''.join(p.get_text() for p in doc);pages=len(doc)
                page_map={};entry_pages={};orphan_headings=[]
                headings=['一、封面与基本信息','二、总成本概览','三、成本要素明细分析','四、重点产品专项分析','五、对标分析','六、总结与建议']
                for index,page in enumerate(doc,1):
                    lines=page.get_text().splitlines()
                    # 目录行（点线引导/页码结尾）不参与孤儿标题判定——原生目录
                    # 缓存条目以"一、/6.4"开头，会被误判为页尾孤儿标题。
                    meaningful=[line.strip() for line in lines if line.strip() and not re.match(r'^第\s*\d+\s*页',line.strip()) and not line.startswith(chr(0x3000)) and '.....' not in line and not re.search(r'第\s*\d+\s*页$',line)]
                    if meaningful and (re.match(r'^[一二三四五六]、|^[2-6]\.\d+(?:\.\d+)?\s+',meaningful[-1]) or '｜' in meaningful[-1]):orphan_headings.append(meaningful[-1])
                    # 章节标题按“≥13pt 大字号行”识别（2026-09-21 四轮 F 项）：目录行
                    # (10.5pt) 与表格单元格(9pt，含阅读指南引用)中的同名文本不再误判。
                    big=set()
                    for b in page.get_text('dict')['blocks']:
                        for l in b.get('lines',[]):
                            ltext=''.join(sp['text'] for sp in l['spans']).strip()
                            sizes=[sp['size'] for sp in l['spans'] if sp['text'].strip()]
                            if ltext and sizes and max(sizes)>=13:
                                big.add(ltext)
                                # 2026-09-22 原生目录：H2=14pt 同入大字号集，顺带收集子标题页码。
                                if re.match(r'^\d[.]\d[ ]',ltext):entry_pages.setdefault(ltext.replace('\u00a0',' ').strip(),index)
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
            if paragraph.text.startswith(chr(0x3000)):continue  # 静态目录行不是孤儿标题
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
                # 孤儿标题补救：keep-with-next（2026-09-21 五轮：page_break_before
                # 会把标题强推新页、在上一页留下大片空白；keepNext 只把标题与后续
                # 首段绑在一起移动，空白上界为后续首段高度）。
                # 例外（2026-09-23 视觉验收）：标题后（可隔题注等空段）紧跟表
                # 格时 LibreOffice 不跨块 honoring keepNext（3.1.1 悬在页底而
                # 表在下页）——此时改用 page_break_before，标题带着它的表格
                # 整体到新页，上一页空出的本来就是标题孤行所占的行。
                _nxt=start._p.getnext();_leads_tbl=False
                while _nxt is not None and _nxt.tag==qn('w:p'):
                    if _nxt.findall('.//'+qn('w:drawing')):break
                    _nxt=_nxt.getnext()
                if _nxt is not None and _nxt.tag==qn('w:tbl'):_leads_tbl=True
                if _leads_tbl or _toc_pass>=2:
                    # 首轮用 keep-with-next 温和补救；第2轮仍孤行说明
                    # LibreOffice 对长 keepNext 链（标题+空段+图+题注）不生效
                    # （5.1 实测），强制分页——上一页空出的本就是孤行所占行。
                    if not start.paragraph_format.page_break_before:
                        start.paragraph_format.page_break_before=True;layout_changed=True
                else:
                    if not start.paragraph_format.keep_with_next:
                        start.paragraph_format.keep_with_next=True;layout_changed=True
                    # 回溯可能越过孤儿标题本身（空段+上级章标题），孤儿段必须
                    # 自身也绑定下一段，否则 keepNext 设在了别处（5.1 悬页底实测）
                    if not paragraph.paragraph_format.keep_with_next:
                        paragraph.paragraph_format.keep_with_next=True;layout_changed=True
        # 原生目录域缓存条目回填实际页码（2026-09-22）：条目文本与页码都在
        # w:hyperlink 内，Paragraph.text 取不到，按 XML 定位；页码为条目段
        # 最后一个 w:t。条目文本匹配优先子标题页码表，回退六章页码表。
        from docx.oxml.ns import qn as _qn
        def _norm(s):return re.sub(r'[\s\u00a0\u3000]+','',s)
        toc_entry_paras=[p for p in d.paragraphs if p._p.xpath('.//w:hyperlink[starts-with(@w:anchor,"YH_SEC_T")]')]
        toc_updated=False;toc_verified={}
        for paragraph in toc_entry_paras:
            texts=paragraph._p.findall('.//'+_qn('w:t'))
            if len(texts)<2:continue
            base=re.sub(r'第\d+页$','',_norm(''.join(t.text or '' for t in texts[:-1])))
            page=next((pg for key,pg in entry_pages.items() if _norm(key).startswith(base) or base.startswith(_norm(key))),None)
            if page is None:page=next((pg for key,pg in page_map.items() if base.startswith(_norm(key)) or _norm(key).startswith(base)),None)
            if not page:continue
            fresh='第'+str(page)+'页'
            if (texts[-1].text or '')!=fresh:
                texts[-1].text=fresh;texts[-1].set(_qn('xml:space'),'preserve');toc_updated=True
            toc_verified[base]=page
        if _toc_pass<5 and (layout_changed or toc_updated):
            d.save(path)
            return convert_pdf(path,timeout,converter,_toc_pass+1)
        return {'status':'PASS','scope':'file_conversion','toc_updated':bool(toc_verified) and len(toc_verified)>=len(toc_entry_paras) and not toc_updated,'orphan_headings':orphan_headings,'toc_pages':page_map,'path':str(pdf),'pages':pages,'sha256':hashlib.sha256(pdf.read_bytes()).hexdigest()}
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
    if meta.get('reader_template_version')=='reader-v5':return
    body=d.element.body
    # 2026-09-21 四轮：前置章节（解决方案封面、文档控制三表、阅读指南、目录域）
    # 完整保留不裁剪。五轮（用户反馈）：前置区内部解除强制分页与分节（消除
    # 2-6 页大片空白与页数虚增、编制单位回流封面、目录标题与内容同页），内容
    # 连续排布；正文起始章强制新起一页。正文（一、封面与基本信息 起）的
    # 原生分页/分节不受影响。
    paras=_all_paragraphs(d)
    body_start=None
    for pp_ in paras:
        if pp_.text.strip()=='一、封面与基本信息':body_start=pp_;break
    in_front=True
    for pp_ in paras:
        if body_start is not None and pp_._p is body_start._p:in_front=False
        if not in_front:continue
        for br in list(pp_._p.iter(qn('w:br'))):
            if br.get(qn('w:type'))=='page':br.getparent().remove(br)
        ppr=pp_._p.find(qn('w:pPr'))
        if ppr is not None:
            for tag in ('pageBreakBefore','sectPr'):
                for x in list(ppr.findall(qn('w:'+tag))):ppr.remove(x)
        # 目录域残留处理（五轮：用户反馈目录标题与内容分两页）：空 TOC 域的
        # fldChar/instrText 会让 LibreOffice 把域后内容强推下一页；静态目录
        # 由渲染期生成，域字符与"更新域"提示行一并移除。
        for r_el in list(pp_._p.iter(qn('w:r'))):
            if r_el.find(qn('w:fldChar')) is not None or r_el.find(qn('w:instrText')) is not None:
                pp_._p.remove(r_el)
        if pp_.text.strip().startswith('（右键点击此处'):
            pp_._p.getparent().remove(pp_._p)
    if body_start is not None:body_start.paragraph_format.page_break_before=True
    # Existing blank同比 cells are omissions, not missing data.
    # 2026-09-23 修复（审计 AUD-TPL-01）：与 install_template 同源按表头文字
    # 定位，不再按 rows[4:7]/列4-5 硬编码；未命中跳过并写入 working_changes。
    overview=next((t for t in d.tables if any('去年同月' in c.text for c in t.rows[0].cells)),None)
    yoy_note=None
    if overview is not None:
        yoy_col,rate_col,element_rows,skipped=_locate_overview_yoy_cells(overview)
        bound=0
        for cn in ('材料','人工','制造费用'):
            row=element_rows.get(cn)
            if row is None or yoy_col is None or rate_col is None:continue
            field_amount='去年'+cn+'成本' if cn!='制造费用' else '去年制造费用'
            _bind_overview_yoy_cell(row,yoy_col,field_amount,False,meta['placeholders'],22000)
            _bind_overview_yoy_cell(row,rate_col,cn+'成本同比',True,meta['placeholders'],22000)
            bound+=2
        yoy_note=(f'同比补绑定 {bound} 个单元格' if bound else '同比补绑定全部跳过：'+'；'.join(skipped)) if (bound or skipped) else None
        if skipped and bound:yoy_note+='；跳过：'+'；'.join(skipped)
    # 2026-09-21 真人评审四轮（B 项）：模板原生分页（封面/文档控制/阅读指南/目录
    # 各归各页）完整保留，不再剥离 w:br page 与 pageBreakBefore。
    style_reader(d)
    d.save(output)
    meta['reader_template_version']='reader-v5'
    meta['template_hash']=hashlib.sha256(Path(output).read_bytes()).hexdigest()
    meta['working_changes']=['前置章节与原生分页完整保留（模板为准）','六个赛题固定章节保留','同比三要素单独绑定','动态表格按模板md列结构']
    if yoy_note:meta['working_changes'].append(yoy_note)
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
        # 图表题注（2026-09-23）：旧"图｜"与新"图几-几/表几-几"统一居中灰字
        if re.match(r'^(图｜|图\d+-\d+|表\d+-\d+)',text):
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


_FONT='宋体'            # 中文正文（Windows 全机可用，解决 Noto 缺字体导致的替换/缺字）
_FONT_HEAD='黑体'        # 标题层级
_FONT_ASCII='Times New Roman'  # 西文与数字（2026-09-23 用户要求：数字用新罗马）
_CN_NUM={'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}

def _set_east_asia(rpr_holder,ea=None):
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    rpr=rpr_holder.get_or_add_rPr() if hasattr(rpr_holder,'get_or_add_rPr') else rpr_holder
    rf=rpr.find(qn('w:rFonts'))
    if rf is None:
        rf=OxmlElement('w:rFonts');rpr.insert(0,rf)
    ea=ea or _FONT
    for attr,val in (('w:ascii',_FONT_ASCII),('w:hAnsi',_FONT_ASCII),('w:eastAsia',ea),('w:cs',_FONT_ASCII)):
        rf.set(qn(attr),val)

def _standardize_typography(doc):
    """中文版式统一（2026-09-23 用户反馈 行距不等/数字字体/首行缩进）：

    ① 全部 run 字体：西文/数字 Times New Roman，中文宋体（标题黑体）——
       解决 Noto Sans SC 未装机时 Word 替换字体导致的行距不齐与缺字方框；
    ② 正文段（非标题/题注/目录条目/表格内）：行距统一 1.5 倍
       （w:spacing line=360 auto）、关闭"对齐到文档网格"（混排行距不等的
       另一根因）、首行缩进 2 字符——标签行/列表行/短行除外；
    ③ 表格内 run 只统一字体，不动行距缩进。"""
    from docx.shared import Pt
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    skip_prefix=('图｜','·','报告编号','人工审核','核心结论','（','第')
    list_re=re.compile(r'^\d+[.、．]\s*')
    caption_re=re.compile(r'^(图｜|图\d+-\d+|表\d+-\d+)')
    for para in _all_paragraphs(doc):
        in_table=para._p.getparent().tag!=qn('w:body')
        is_head=para.style.name.startswith('Heading')
        text=layout_text(para.text).strip()
        for r in para.runs:
            _set_east_asia(r._element,_FONT_HEAD if is_head else _FONT)
        if in_table or is_head:continue
        has_field=bool(para._p.xpath('.//w:hyperlink|.//w:fldChar'))
        if has_field or caption_re.match(text):continue  # 目录条目/题注
        if text and not text.startswith(skip_prefix) and not list_re.match(text) and len(text)>14:
            # 正文散文：首行缩进 2 字符 + 行距 1.5 + 不吸附文档网格
            pf=para.paragraph_format
            pf.first_line_indent=Pt(21)
            pf.line_spacing=1.5
        elif text:
            # 非缩进行也统一行距与网格（核心结论条目/标签行/提示行）
            para.paragraph_format.line_spacing=1.5
        ppr=para._p.get_or_add_pPr()
        if ppr.find(qn('w:snapToGrid')) is None:
            snap=OxmlElement('w:snapToGrid');snap.set(qn('w:val'),'0');ppr.append(snap)

def _body_usable_emu(doc):
    """正文区可用宽度（EMU）；边距未显式设置的节回退 1 英寸。"""
    _EMU_INCH=914400
    sec=doc.sections[-1]
    return sec.page_width-(sec.left_margin or _EMU_INCH)-(sec.right_margin or _EMU_INCH)

def _fit_table_columns(t,usable_emu):
    """表格列宽自适应（2026-09-23 用户反馈"最开头的表丑陋"）：固定布局，
    列宽按内容渲染宽度分配。核心约束——数字绝不允许折行：数值列宽度=最长
    数字渲染宽度（含收窄后的单元格边距），文本列可按词换行故限宽弹性
    压缩；整体放不下时先降数据字号 8.5pt 再等比缩。含合并单元格的表跳过。"""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    ncols=len(t.columns)
    if ncols<2:return False
    for row in t.rows:
        if len(row.cells)!=ncols:return False
    avail=int(usable_emu/635)-60  # 1 twip = 635 EMU；60 为边框余量
    num_pat=re.compile(r'^[-+−]?[\d.,]+\s*(%|％|元|盒|万|h|kg|kWh|元/盒)?[。]?$')
    # 收窄单元格左右边距（默认 108/侧 → 50/侧），宽表省出的宽度可观
    mar=OxmlElement('w:tblCellMar')
    for side,v in (('top',15),('left',50),('bottom',15),('right',50)):
        e=OxmlElement('w:'+side);e.set(qn('w:w'),str(v));e.set(qn('w:type'),'dxa');mar.append(e)
    tblPr=t._tbl.tblPr
    for old in tblPr.findall(qn('w:tblCellMar')):tblPr.remove(old)
    tblPr.append(mar)
    def plan(font_pt):
        cjk=font_pt*20;asc=font_pt*11;margin=140  # 边距100+缓冲40
        needs=[];numeric_flags=[]
        for ci in range(ncols):
            need=0;numeric=0
            for row in t.rows:
                txt=(row.cells[ci].text or '').strip()
                for seg in txt.split('\n'):
                    w=0
                    for ch in seg:w+=cjk if ord(ch)>0x2E80 else asc
                    need=max(need,w)
                if num_pat.match(txt):numeric+=1
            needs.append(need+margin)
            numeric_flags.append(numeric>=max(2,int(0.6*(len(t.rows)-1))))
        return needs,numeric_flags
    def allocate(needs,numeric_flags):
        widths=[]
        for need,isnum in zip(needs,numeric_flags):
            widths.append(need if isnum else min(need,1800))  # 文本列限宽（可按词换行）
        total=sum(widths)
        if total>avail:  # 数值全保仍溢出：等比缩（极端表）
            f=avail/total
            widths=[int(w*f) for w in widths]
        else:  # 富余全部补给文本列（按需比例）
            extra=avail-total
            text_total=sum(w for w,isnum in zip(widths,numeric_flags) if not isnum)
            if text_total>0:
                for i,(w,isnum) in enumerate(zip(widths,numeric_flags)):
                    if not isnum:widths[i]=w+int(extra*w/text_total)
            else:
                widths=[avail//ncols]*ncols
        widths[widths.index(max(widths))]+=avail-sum(widths)
        return widths
    needs,flags=plan(9)
    widths=allocate(needs,flags)
    shrunk=False
    if sum(needs)>avail and any(f and n>0 for f,n in zip(flags,needs)):
        # 9pt 放不下数值列需求：数据字号降到 8.5pt 重新规划
        needs2,flags2=plan(8.5)
        if sum(min(n,1800 if not f else n) for n,f in zip(needs2,flags2))<sum(min(n,1800 if not f else n) for n,f in zip(needs,flags)):
            widths=allocate(needs2,flags2);shrunk=True
    if shrunk:
        from docx.shared import Pt
        for i,row in enumerate(t.rows):
            if i==0:continue
            for c in row.cells:
                for pp in c.paragraphs:
                    for r in pp.runs:r.font.size=Pt(8.5)
    for old in tblPr.findall(qn('w:tblLayout')):tblPr.remove(old)
    layout=OxmlElement('w:tblLayout');layout.set(qn('w:type'),'fixed');tblPr.append(layout)
    for old in tblPr.findall(qn('w:tblW')):tblPr.remove(old)
    tw=OxmlElement('w:tblW');tw.set(qn('w:w'),str(int(usable_emu/635)));tw.set(qn('w:type'),'dxa');tblPr.append(tw)
    grid=t._tbl.find(qn('w:tblGrid'))
    if grid is not None:
        for col,w in zip(grid.findall(qn('w:gridCol')),widths):
            col.set(qn('w:w'),str(int(w)))
    for row in t.rows:
        for ci,cell in enumerate(row.cells):
            tcPr=cell._tc.get_or_add_tcPr()
            for old in tcPr.findall(qn('w:tcW')):tcPr.remove(old)
            tcw=OxmlElement('w:tcW');tcw.set(qn('w:w'),str(int(widths[ci])));tcw.set(qn('w:type'),'dxa');tcPr.append(tcw)
    return True

def _beautify_native_tables(doc):
    """统一所有表格外观（2026-09-23）：模板原生表此前完全无样式（无表头底
    色/无跨页表头/第一列挤压），与动态表格观感割裂。此处对全部表格统一：
    表头灰底加粗+跨页重复、隔行浅灰、数据 9pt、涨跌列红绿着色（成本升红/
    降绿，中文财务惯例）、列宽按内容加权。"""
    from docx.oxml import OxmlElement as _OE
    from docx.oxml.ns import qn as _qn
    from docx.shared import Pt,RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH as _TA
    usable=_body_usable_emu(doc)
    for t in doc.tables:
        first=t.rows[0]
        def _fill(cell):
            pr=cell._tc.tcPr
            return pr is not None and pr.find(_qn('w:shd')) is not None and pr.find(_qn('w:shd')).get(_qn('w:fill'))
        has_header=any(_fill(c)=='D9D9D9' for c in first.cells)
        if not has_header:
            for c in first.cells:
                pr=c._tc.get_or_add_tcPr()
                if pr.find(_qn('w:shd')) is None:
                    shd=_OE('w:shd');shd.set(_qn('w:fill'),'D9D9D9');pr.append(shd)
                for pp in c.paragraphs:
                    pp.alignment=_TA.CENTER
                    for r in pp.runs:r.font.bold=True;r.font.size=Pt(9)
            trpr=first._tr.get_or_add_trPr()
            if trpr.find(_qn('w:tblHeader')) is None:trpr.append(_OE('w:tblHeader'))
            borders=_OE('w:tblBorders')
            for edge in ('top','left','bottom','right','insideH','insideV'):
                e=_OE('w:'+edge);e.set(_qn('w:val'),'single');e.set(_qn('w:sz'),'4');e.set(_qn('w:color'),'000000');borders.append(e)
            t._tbl.tblPr.append(borders)
        headers=[c.text.strip() for c in first.cells]
        delta_cols={i for i,h in enumerate(headers) if any(k in h for k in ('环比','同比','变动','偏差','涨幅','差异率'))}
        num_pat=re.compile(r'^[-+−]?[\d.,]+\s*(%|％|元|盒|万|h|kg|kWh|元/盒)?[。]?$')
        for i,row in enumerate(t.rows):
            if i==0:continue
            if i%2==0:
                for c in row.cells:
                    pr=c._tc.get_or_add_tcPr()
                    if pr.find(_qn('w:shd')) is None:
                        shd=_OE('w:shd');shd.set(_qn('w:fill'),'F7F7F7');pr.append(shd)
            for ci,c in enumerate(row.cells):
                if num_pat.match((c.text or '').strip()):
                    pr=c._tc.get_or_add_tcPr()
                    if pr.find(_qn('w:noWrap')) is None:pr.append(_OE('w:noWrap'))
                for pp in c.paragraphs:
                    for r in pp.runs:r.font.size=Pt(9)
                    if ci in delta_cols:
                        txt=pp.text.strip()
                        color='008000' if txt[:1] in ('-','−','↓') else ('C00000' if txt[:1] in ('+','↑') else None)
                        if color:
                            for r in pp.runs:r.font.color.rgb=RGBColor.from_string(color)
        _fit_table_columns(t,usable)

def _number_and_caption(doc,dynamic_tbl_specs=None):
    """图表规范编号（2026-09-23 用户要求：图表须有"图几-几/表几-几"）。

    仅对程序生成的动态表格加"表几-几"题注（上方，名称来自锚点语义名；
    动态表以表内 YHU_TBL_i 书签识别——lxml 代理 id() 不稳定不可作键）；
    模板原生表格（封面信息/总成本概览等）按用户裁定不加题注——它们是
    赛题模板的固定结构。图题注在图下方（"图4-1 标题"），从旧"图｜副题｜
    标题"重写并绑定图与图题同页。前置区（目录前）与封面装饰图不编号。"""
    from docx.oxml.ns import qn as _qn
    from docx.text.paragraph import Paragraph
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH as _TA
    dynamic_tbl_specs=dynamic_tbl_specs or []
    chapter=None;last_head='';tbl_n={};fig_n={}
    for node in list(doc.element.body):
        if node.tag==_qn('w:p'):
            para=Paragraph(node,doc)
            t=layout_text(para.text).strip()
            lvl=_heading_level(t)
            if lvl==1:
                m=re.match(r'^([一二三四五六七八九十]+)、',t)
                chapter=_CN_NUM.get(m.group(1)) if m else None
                last_head=re.sub(r'^[一二三四五六七八九十]+、','',t)
            elif lvl==2:
                last_head=re.sub(r'^\d+(?:\.\d+)*\s*','',t)
            if chapter and node.findall('.//'+_qn('w:drawing')):
                fig_n[chapter]=fig_n.get(chapter,0)+1
                label='图'+str(chapter)+'-'+str(fig_n[chapter])
                cap=None
                nxt=node.getnext()
                if nxt is not None and nxt.tag==_qn('w:p'):
                    cand=Paragraph(nxt,doc)
                    if cand.text.strip().startswith('图｜'):
                        title=cand.text.strip().split('｜')[-1]
                        ts=list(cand._p.iter('{'+W+'}t'))
                        if ts:
                            ts[0].text=label+' '+title
                            for extra in ts[1:]:extra.text=''
                        else:cand.add_run(label+' '+title)
                        cap=cand
                if cap is None:
                    cap=doc.add_paragraph();node.addnext(cap._p);cap.add_run(label)
                cap.alignment=_TA.CENTER
                para.paragraph_format.keep_with_next=True  # 图与图题同页
        elif node.tag==_qn('w:tbl') and chapter:
            spec=None
            for bm in node.findall('.//'+_qn('w:bookmarkStart')):
                name=bm.get(_qn('w:name')) or ''
                if name.startswith('YHU_TBL_'):
                    try:spec=dynamic_tbl_specs[int(name[len('YHU_TBL_'):])]
                    except (IndexError,ValueError):spec=''
                    break
            if spec is None:continue  # 模板原生表不加题注（用户裁定）
            tbl_n[chapter]=tbl_n.get(chapter,0)+1
            label='表'+str(chapter)+'-'+str(tbl_n[chapter])
            cap=doc.add_paragraph()
            run=cap.add_run(label+' '+(spec or last_head or '数据明细'))
            run.font.bold=True;run.font.size=Pt(9)
            cap.alignment=_TA.CENTER
            cap.paragraph_format.space_before=Pt(6);cap.paragraph_format.space_after=Pt(3)
            cap.paragraph_format.keep_with_next=True  # 题注与表格同页
            node.addprevious(cap._p)

def _layout_front_pages(doc):
    """前置区分页与空行整治（2026-09-23 用户反馈：模板表间空行过多、阅读
    指南不在第3页开头、目录未单独成页、专项分析章未单独成页）。

    ① 文档控制表之后（阅读指南之前）连续空段 >1 折叠为 1；
    ② 阅读指南、目录标题强制 page_break_before（阅读指南=第3页开头，
       目录单独成页）；
    ③ 四、重点产品专项分析（即"六味地黄胶囊 专题分析"章）单独新起一页。
    封面区的空段（标题/版本信息的垂直定位）不动。"""
    from docx.oxml.ns import qn
    def _removable(p):
        # 空段且不含图/书签/域/分页符才可删
        return (not (p.text or '').strip()
                and not p._p.findall('.//'+qn('w:drawing'))
                and not p._p.findall('.//'+qn('w:bookmarkStart'))
                and not p._p.findall('.//'+qn('w:fldChar'))
                and not p._p.findall('.//'+qn('w:br')))
    seen_docctrl=False;empty_run=[];prev_text=''
    for para in doc.paragraphs:
        t=layout_text(para.text).strip()
        # 封面书名号行与主标题完全重复（{{报告标题}} 绑定后的冗余装饰行）→ 删除
        if t.startswith('《') and t.endswith('》') and t[1:-1].strip()==prev_text and t[1:-1].strip():
            para._p.getparent().remove(para._p);continue
        if t:prev_text=t  # 空段不打断相邻判定
        # 目录缓存条目含超链接/域字符，绝不能当章标题加分页（否则目录被拦腰截断）
        if para._p.xpath('.//w:hyperlink|.//w:fldChar'):continue
        if t=='文档控制':seen_docctrl=True
        if seen_docctrl and _removable(para):
            empty_run.append(para)
            if len(empty_run)>1:
                empty_run[-1]._p.getparent().remove(empty_run[-1]._p)
                empty_run.pop()
            continue
        empty_run=[]
        if t=='阅读指南':
            para.paragraph_format.page_break_before=True
        elif t.replace(' ','').replace('\u3000','')=='目录':
            # 目录前紧邻空段清除，目录单独成页
            prev=para._p.getprevious()
            while prev is not None and prev.tag==qn('w:p'):
                from docx.text.paragraph import Paragraph
                cand=Paragraph(prev,para._parent)
                if not _removable(cand):break
                nxt=prev.getprevious()
                prev.getparent().remove(prev);prev=nxt
            para.paragraph_format.page_break_before=True
        elif re.match(r'^四、重点产品专项分析',t):
            para.paragraph_format.page_break_before=True

def _key_conclusion_lines(snapshot,narrative,benchmark=None):
    """核心结论结构化条目（2026-09-23 用户反馈"核心结论太少太简陋"）：
    从快照/归因/对标/建议四个程序数据源各取一条，缺数据则跳过该条，
    不编造。数字全部程序所有（number() 渲染），符合数字合同。"""
    from decimal import Decimal as _D
    lines=[]
    m=snapshot.get('metrics') or {}
    pc=snapshot.get('period_changes') or {}
    def _rate(r):
        try:
            v=float((r or {}).get('rate'))
            return ('上升' if v>0 else '下降' if v<0 else '持平')+f'{abs(v):.2f}%'
        except Exception:return '数据缺失'
    if m.get('unit_cost') is not None:
        line='总量：本月总成本 '+number(m.get('total_cost'))+' 元（产量 '+number(m.get('quantity'),0)+' 盒），单位成本 '+number(m['unit_cost'])+' 元/盒，环比'+_rate((pc.get('unit_cost') or {}).get('mom'))
        yoy=_rate((pc.get('unit_cost') or {}).get('yoy'))
        if yoy!='数据缺失':line+='，同比'+yoy
        lines.append(line+'。')
    els=snapshot.get('elements') or []
    ranked=sorted(els,key=lambda e:abs(_D(str(e.get('unit_delta') or '0'))),reverse=True)
    if ranked:
        seg='、'.join((e['name']+' '+('+' if _D(str(e.get('unit_delta') or '0'))>=0 else '')+number(str(e.get('unit_delta') or '0'))+' 元/盒') for e in ranked)
        lead=ranked[0];d=_D(str(lead.get('unit_delta') or '0'))
        lines.append('要素：三要素单位成本环比 '+seg+'；影响最大的是'+lead['name']+'（每盒'+('增加' if d>=0 else '减少')+' '+number(str(d).lstrip('-'))+' 元）。')
    attr=snapshot.get('attribution') or {}
    if attr.get('status')=='PASS':
        top=(attr.get('ranking') or [{}])[0]
        if top.get('cause'):
            did=(attr.get('did') or {})
            lines.append('根因：多维归因首位“'+str(top.get('cause'))+'”'+str(top.get('direction') or '')+'（解释力 '+str(top.get('ep_pct') or '—')+'，可能性'+str(top.get('label') or '—')+'）；对照厂 DiD 检验'+('稳健' if did.get('parallel_trend')=='稳健' else '结论见 4.2 节')+'。')
    if benchmark:
        rows=(benchmark.get('summary') or [])
        if rows:
            r=rows[0]
            try:delta=float(r.get('delta'))
            except (TypeError,ValueError):delta=None
            if delta is not None:
                lines.append('对标：对比 '+str(benchmark.get('right') or '对标厂')+'，单位成本差异 '+number(r.get('delta'))+' 元/盒（'+('本厂较高' if delta>0 else '对标厂较高')+'），差异结构与拆解见第五章。')
    sugg=[f for f in narrative.get('findings',[]) if (f.get('suggestion') or '').strip()]
    if sugg:
        first=re.sub(r'\s+',' ',sugg[0].get('suggestion',''))[:60]
        lines.append('行动：共 '+str(len(sugg))+' 条整改/核查建议（第六章）；优先项——'+first+'……')
    return lines

def _ensure_outline_styles(doc):
    """定义标准标题与目录样式（2026-09-22 用户要求：原生目录+小标题入目录+
    字号层级符合标准；题包原件标题是 Normal 直排，无任何层级样式）。

    层级：H1 小三 15pt、H2 四号 14pt、H3 小四 12pt，黑体系加粗黑色；
    toc 1/toc 2 供 Word 更新目录域后 regenerate 的条目使用（styleId 固定
    TOC1/TOC2，Word 按名称映射）。"""
    from docx.shared import Pt,RGBColor,Cm
    from docx.enum.style import WD_STYLE_TYPE
    from docx.oxml.ns import qn
    def heading(name,size,before,after):
        try:st=doc.styles[name]
        except KeyError:st=doc.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
        st.font.size=Pt(size);st.font.bold=True;st.font.color.rgb=RGBColor(0,0,0);st.font.name=_FONT
        _set_east_asia(st.element,_FONT_HEAD)
        pf=st.paragraph_format
        pf.space_before=Pt(before);pf.space_after=Pt(after);pf.line_spacing=1.5
        # 不设 keep_with_next：Word 会为带"与下段同页"的段落显示黑色小方块
        # 编辑标记（2026-09-23 用户问题10）；Word 内建 Heading 样式默认已有
        # keepNext 语义，孤行防护交给 Word 默认。
    heading('Heading 1',15,12,6);heading('Heading 2',14,10,5);heading('Heading 3',12,8,4)
    for name,style_id,indent in (('toc 1','TOC1',None),('toc 2','TOC2',Cm(0.74))):
        try:st=doc.styles[name]
        except KeyError:
            st=doc.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
            st.base_style=doc.styles['Normal']
        st.font.size=Pt(10.5);st.font.name=_FONT;_set_east_asia(st.element)
        st.element.set(qn('w:styleId'),style_id)
        pf=st.paragraph_format
        pf.space_before=Pt(1);pf.space_after=Pt(1);pf.line_spacing=1.3;pf.first_line_indent=None
        if indent is not None:pf.left_indent=indent

def _heading_level(text):
    if re.match(r'^[一二三四五六七八九十]+、',text):return 1
    if re.match(r'^[1-9][.][1-9](?:[.][1-9])?[ ]',text):
        return 2 if re.match(r'^[1-9][.][1-9][ ]',text) else 3
    return 0

def _apply_outline_styles(doc,heads):
    """把章节/小标题段落挂到 Heading 样式（进 Word 原生目录与导航窗格），
    同时在 run 层写死字号/加粗/黑色/中文字体——样式与直排双保险，渲染
    外观不依赖样式解析。"""
    from docx.shared import Pt,RGBColor
    sizes={1:15,2:14,3:12}
    for para,t in heads:
        level=_heading_level(t)
        if not level:continue
        try:para.style=doc.styles['Heading '+str(level)]
        except KeyError:pass
        for r in para.runs:
            r.font.size=Pt(sizes[level]);r.font.bold=True
            r.font.color.rgb=RGBColor(0,0,0);r.font.name=_FONT
            _set_east_asia(r._element)

def _fix_reading_guide(doc):
    """修正题包原件自带的阅读指南截断（2026-09-22 用户指出语义不通）：
    原件写作"三、成本要素明、四、重点产品专、…"——章节名被截断，
    补全为完整章节名。替换是纯子串级（非占位符语法），文本并入首 run
    保样式；阅读指南单元格无占位符/书签，重排安全。"""
    from docx.oxml.ns import qn
    fixes={'成本要素明、':'成本要素明细分析、','重点产品专、':'重点产品专项分析、'}
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    nodes=list(p._p.iter('{'+W+'}t'))
                    text=''.join(n.text or '' for n in nodes)
                    if not any(k in text for k in fixes):continue
                    for k,v in fixes.items():text=text.replace(k,v)
                    for i,n in enumerate(nodes):
                        if i==0:
                            n.text=text;n.set(qn('xml:space'),'preserve')
                        else:n.text=''

def _insert_native_toc(doc,title,heads):
    """用 Word 原生目录域替换旧静态目录（2026-09-22 用户要求：目录可自动
    跳转）。结构：多段缓存条目包裹在 TOC 域 begin(separate)…end 之间——
    条目即缓存结果，未更新域的查看器（LibreOffice/PDF）直接可见；域标
    dirty=true，Word 打开时自动重建并接管页码与超链接。缓存条目本身用
    w:hyperlink 指向标题书签（YH_SEC_*），Word/PDF 中均可点击跳转。"""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph
    # 清除旧静态条目/提示行（\u3000 前缀）直至遇到其他正文
    node=title._p
    while True:
        nxt=node.getnext()
        if nxt is None or nxt.tag!=qn('w:p'):break
        cand=Paragraph(nxt,title._parent);t=cand.text or ''
        if t.startswith(chr(0x3000)) or '更新域' in t or not t.strip():
            nxt.getparent().remove(nxt);continue
        break
    sec=doc.sections[-1]
    _EMU_INCH=914400
    usable=sec.page_width-(sec.left_margin or _EMU_INCH)-(sec.right_margin or _EMU_INCH)
    tab_pos=str(int(usable/360000*1440))  # EMU→twips，右对齐制表位带点线
    entries=[(t,_heading_level(t)) for _,t in heads]
    entries=[(t,lvl) for t,lvl in entries if lvl in (1,2)]
    if not entries:return
    paras=[]
    for index,(t,level) in enumerate(entries):
        bmk='YH_SEC_T'+str(index)
        para=OxmlElement('w:p')
        ppr=OxmlElement('w:pPr')
        st=OxmlElement('w:pStyle');st.set(qn('w:val'),'TOC1' if level==1 else 'TOC2');ppr.append(st)
        tabs=OxmlElement('w:tabs');tab=OxmlElement('w:tab')
        tab.set(qn('w:val'),'right');tab.set(qn('w:leader'),'dot');tab.set(qn('w:pos'),tab_pos)
        tabs.append(tab);ppr.append(tabs);para.append(ppr)
        if index==0:
            r=OxmlElement('w:r');fc=OxmlElement('w:fldChar')
            # 不标 w:dirty：Word/WPS 打开时会对脏域弹"该文档包含的域可能
            # 引用了其他文件"询问框（2026-09-22 用户截图反馈）。缓存条目
            # 页码由 convert_pdf 按 LibreOffice 分页回填，且已验证与 Word
            # 自身分页逐条一致（14/14 报告实测），无需打开时强制更新；
            # 需要时用户仍可右键/F9 手动更新域。
            fc.set(qn('w:fldCharType'),'begin');r.append(fc);para.append(r)
            r=OxmlElement('w:r');it=OxmlElement('w:instrText')
            it.set(qn('xml:space'),'preserve')
            # 域参数与题包原件一致（TOC \o "1-4" \h \z \u）：1-4 级标题、
            # 带超链接、隐藏 web 前导、使用大纲级别（2026-09-23 对照模板）。
            it.text=' TOC \\o "1-4" \\h \\z \\u ';r.append(it);para.append(r)
            r=OxmlElement('w:r');fc=OxmlElement('w:fldChar')
            fc.set(qn('w:fldCharType'),'separate');r.append(fc);para.append(r)
        hl=OxmlElement('w:hyperlink');hl.set(qn('w:anchor'),bmk);hl.set(qn('w:history'),'1')
        r=OxmlElement('w:r');wt=OxmlElement('w:t');wt.set(qn('xml:space'),'preserve')
        # 缩进用 TOC1/TOC2 样式 left_indent，不用 U+3000——U+3000 在部分
        # Word 字体下渲染为空心方框（2026-09-23 用户截图问题12）。
        wt.text=t;r.append(wt);hl.append(r)
        r=OxmlElement('w:r');r.append(OxmlElement('w:tab'));hl.append(r)
        r=OxmlElement('w:r');wt=OxmlElement('w:t');wt.text='第1页';r.append(wt);hl.append(r)
        para.append(hl)
        if index==len(entries)-1:
            r=OxmlElement('w:r');fc=OxmlElement('w:fldChar')
            fc.set(qn('w:fldCharType'),'end');r.append(fc);para.append(r)
        paras.append(para)
    for para in reversed(paras):title._p.addnext(para)
    # 更新域提示行（题包原件即有"（右键点击此处 → 更新域 → 更新整个目录）"，
    # 作为域的缓存占位文字；此处恢复为域外独立灰字行，指引手动刷新）。
    hint=OxmlElement('w:p')
    hp=OxmlElement('w:pPr')
    for tag,attr,val in (('w:spacing','w:before','120'),('w:spacing','w:after','0')):
        e=OxmlElement(tag);e.set(qn(attr),val);hp.append(e)
    hint.append(hp)
    r=OxmlElement('w:r');rpr=OxmlElement('w:rPr')
    sz=OxmlElement('w:sz');sz.set(qn('w:val'),'18');rpr.append(sz)  # 9pt
    col=OxmlElement('w:color');col.set(qn('w:val'),'808080');rpr.append(col)
    rf=OxmlElement('w:rFonts')
    for a,v in (('w:ascii',_FONT_ASCII),('w:hAnsi',_FONT_ASCII),('w:eastAsia',_FONT)):rf.set(qn(a),v)
    rpr.append(rf);r.append(rpr)
    wt=OxmlElement('w:t');wt.set(qn('xml:space'),'preserve');wt.text='（若目录页码与实际分页有出入，可右键点击目录 → 更新域 → 更新整个目录。）'
    r.append(wt);hint.append(r)
    paras[-1].addnext(hint)
    return entries


def add_reader_summary(doc,snapshot,narrative,output,benchmark=None):
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt
    # 2026-09-21 真人评审三轮：模板前置章节（封面/文档控制/阅读指南/目录域）完整保留，
    # 自创大标题取消（模板封面已有）。文档头按模板 md 增补；核心结论与审核状态
    # 作为"模板未说明"的增补插在"一、封面与基本信息"之前。
    anchor=next((p for p in doc.paragraphs if p.text.strip()=='一、封面与基本信息'),None)
    if anchor is None:return
    label=snapshot['period']['start'] if snapshot['period']['start']==snapshot['period']['end'] else snapshot['period']['start']+' 至 '+snapshot['period']['end']
    report_no='YH-'+hashlib.sha256((snapshot['snapshot_id']) .encode()).hexdigest()[:8].upper()
    _head=anchor.insert_paragraph_before('报告编号：'+report_no+'（分析周期 '+label+'）')
    # P2-2/P2-3（2026-09-23 视觉审查）：核心结论块插在正文首章锚点之前，
    # 不在“正文首章新起一页”的覆盖范围内——显式从新页开始，消除“目录与
    # 正文同页 + 随后近空白页”的连锁。
    _head.paragraph_format.page_break_before=True
    mode='本次采用基础分析，原因解释待复核。' if not narrative.get('model_live') or narrative.get('status')!='PASS' else '本次采用模型辅助解释；因果归因仍待人工复核。'
    anchor.insert_paragraph_before('人工审核：待审核。'+mode)
    # 核心结论（2026-09-23 用户反馈"核心结论太少太简陋"）：单段改为结构化
    # 条目——总量/要素/根因/对标/行动，数据缺则跳过不编造，数字程序所有。
    conclusions=_key_conclusion_lines(snapshot,narrative,benchmark)
    if conclusions:
        head=anchor.insert_paragraph_before('核心结论（'+str(len(conclusions))+' 项）')
        for r in head.runs:r.font.bold=True;r.font.size=Pt(12)
        for i,line in enumerate(conclusions,1):
            # P2-8（视觉审查）：负值数值的 '-' 允许 Word 在其后断行，曾出现
            # 行尾"直接人工 -"+下行"0.0022 元/盒"被误读为破折号；换 U+2011。
            p=anchor.insert_paragraph_before(str(i)+'. '+re.sub(r'(?<![0-9])-(?=\d)','‑',line))
            for r in p.runs:r.font.size=Pt(10.5)
    # 目录（真人评审二轮）：完整子目录；条目插在模板目录域提示行之后（保留域可更新），
    # 一级行保持全角空格前缀以兼容 convert_pdf 的页码回写。
    title=next((p for p in doc.paragraphs if p.text.strip().replace(chr(0x3000),'').replace(' ','')=='目录'),None)
    if title is None:return
    # 五轮（用户反馈：目录标题与内容被分到两页）：标题与条目之间的域尾部
    # 空段/空标题段删除，标题与首条目 keep-with-next 锁定为同页。
    node=title._p
    removed=0
    while True:
        nxt=node.getnext()
        if nxt is None:break
        from docx.text.paragraph import Paragraph as _P
        cand=_P(nxt,title._parent)
        t=(cand.text or '').strip()
        if t.startswith(chr(0x3000)) or '更新域' in t:break  # 到条目区/提示行为止
        if not t and removed<4:
            node.addnext(nxt);nxt.getparent().remove(nxt);removed+=1;continue
        break
    title.paragraph_format.keep_with_next=True
    heads=[(para,layout_text(para.text).strip()) for para in doc.paragraphs]
    heads=[(para,t) for para,t in heads if _heading_level(t)]
    # 2026-09-22 原生目录改造：标题挂 Heading 样式（小标题进目录+字号层级
    # 标准）；阅读指南截断修复；静态目录行替换为可跳转的 TOC 域缓存条目。
    _ensure_outline_styles(doc)
    _apply_outline_styles(doc,heads)
    _fix_reading_guide(doc)
    entry_index=0
    for index,(para,t) in enumerate(heads):
        level=_heading_level(t)
        name='YH_SEC_T'+str(entry_index) if level in (1,2) else 'YH_SEC_'+str(index)
        entry_index+=1 if level in (1,2) else 0
        bmk=OxmlElement('w:bookmarkStart');bmk.set(qn('w:id'),str(31000+index));bmk.set(qn('w:name'),name)
        bmk_end=OxmlElement('w:bookmarkEnd');bmk_end.set(qn('w:id'),str(31000+index))
        para._p.insert(0,bmk);para._p.append(bmk_end)
    _insert_native_toc(doc,title,heads)
    mark=OxmlElement('w:bookmarkStart');mark.set(qn('w:id'),'30000');mark.set(qn('w:name'),'YH_TOC');title._p.insert(0,mark)


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
        cap=doc.add_paragraph('图｜'+title)
        # 2026-09-23 图题移到图下方（规范），编号由 _number_and_caption
        # 后处理改写为"图几-几 标题"；图段 keep-with-next 绑定图与图题。
        from docx.enum.text import WD_ALIGN_PARAGRAPH as _AL
        _EMU_INCH=914400
        usable=min((s.page_width-(s.left_margin or _EMU_INCH)-(s.right_margin or _EMU_INCH)) for s in doc.sections)
        usable_cm=usable/360000
        pic=doc.add_paragraph();pic.alignment=_AL.CENTER;pic.paragraph_format.keep_with_next=True
        pic.add_run().add_picture(str(path),width=Cm(min(width_cm,usable_cm)))
        anchor.addnext(pic._p);pic._p.addnext(cap._p)
        return cap  # 返回题注段，供后续图表链式接排
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
    _cap22=insert(fig,'structure',anchor,subtitle+'｜三要素单位成本构成占比',width_cm=13)
    # 预算对比图（2026-09-23 用户反馈 #11：直观图片偏少）——三要素实际 vs
    # 预算分组柱，标注偏差%；接排在占比饼图之后（2.2 成本结构节内）。
    _budget=[(e['name'],float(e['unit']),e.get('budget_unit')) for e in els]
    _budget=[(n,a,float(b)) for n,a,b in _budget if b not in (None,'','0')]
    if _budget:
        fig,ax=plt.subplots(figsize=(6.8,2.9));pos=list(range(len(_budget)))
        ax.bar([x-.17 for x in pos],[a for _,a,_ in _budget],width=.34,label='本月实际',color='#176C8C')
        ax.bar([x+.17 for x in pos],[b for _,_,b in _budget],width=.34,label='本月预算',color='#B08968')
        peak=max(max(a,b) for _,a,b in _budget)
        for i,(n,a,b) in enumerate(_budget):
            dev=(a-b)/b*100 if b else 0
            ax.text(i,max(a,b)+peak*0.04,('+' if dev>=0 else '−')+f'{abs(dev):.1f}%',ha='center',va='bottom',fontsize=8.5,color='#C00000' if dev>0 else '#008000')
        ax.set_xticks(pos,[n for n,_,_ in _budget]);ax.set_ylabel('元/盒');ax.set_ylim(0,peak*1.22)
        ax.legend(ncol=2,loc='upper center',frameon=False);ax.grid(axis='y',alpha=.2)
        insert(fig,'budget',_cap22._p,subtitle+'｜三要素实际与预算对比（柱上为预算偏差）')
    base=snapshot.get('comparison',{}).get('mom',{}).get('base');current=snapshot['metrics']['unit_cost']['value']
    if base is not None:
        # P2-9（2026-09-23 视觉审查）：改为真瀑布桥接——各要素变动柱自"累计
        # 基线"浮动绘制（上期→逐要素→本期），恢复瀑布的桥接语义；纵轴紧包
        # 数据区间（不从 0 起），微小的负向柱（-0.0022）在桥接位置上也可见。
        deltas=[float(e.get('unit_delta') or 0) for e in els]
        fig,ax=plt.subplots(figsize=(max(8.6,1.9*(len(els)+2)),3.4))
        xs=['上期\n单位成本']+[e['name'].replace('直接','直接\n').replace('制造费用','制造\n费用')+'\n变动' for e in els]+['本期\n单位成本']
        # 左右总量柱仍自 0 画（语义=水平总量），但被紧缩 y 轴截断可见部分一致。
        ax.bar(0,float(base),width=.58,color='#82939F',zorder=3);ax.text(0,float(base)+abs(float(base))*0.012+0.02,f'{float(base):.2f}',ha='center',va='bottom',fontsize=9,zorder=6)
        run=float(base);levels=[run]
        for i,e in enumerate(els,1):
            v=deltas[i-1]
            b=min(run,run+v)
            ax.bar(i,abs(v) if abs(v)>0 else 1e-6,bottom=b,width=.58,color='#A56B3D' if v>=0 else '#1F6E5E',zorder=3)
            _bbox=dict(boxstyle='round,pad=0.15',facecolor='white',edgecolor='none',alpha=0.85)
            ax.text(i,run+v+((run+v)*0.012+0.02)*(1 if v>=0 else -1),(('+' if v>=0 else '−')+number(e.get('unit_delta') or 0).lstrip('-')),ha='center',va='bottom' if v>=0 else 'top',fontsize=9,color='#5A3B28' if v>=0 else '#1F6E5E',zorder=6,bbox=_bbox)
            run+=v;levels.append(run)
        ax.bar(len(els)+1,float(current),width=.58,color='#176C8C',zorder=3);ax.text(len(els)+1,float(current)+abs(float(current))*0.012+0.02,f'{float(current):.2f}',ha='center',va='bottom',fontsize=9,zorder=6)
        # 桥接虚线：上一柱顶到下一柱浮动的视觉连续性
        for i in range(len(els)+1):
            y=levels[i] if i<len(levels) else run
            ax.plot([i+0.29,i+0.71],[levels[i],levels[i]],ls='--',lw=.8,color='#8A97A0',zorder=2)
        lo=min(levels+[float(current)]);hi=max(levels+[float(current)])
        pad=(hi-lo)*0.28 or 0.5
        ax.set_ylim(max(0,lo-pad),hi+pad*1.6)
        ax.set_xticks(range(len(els)+2),xs,fontsize=8.5);ax.set_ylabel('元/盒（浮动柱=该要素对单位成本的变动桥接）');ax.grid(axis='y',alpha=.22)
        insert(fig,'waterfall',anchor,subtitle+'｜上期至本期单位成本桥接（浮动柱=要素变动，橙涨绿跌）')

    be=(benchmark or {}).get('elements',[])
    if be:
        fig,ax=plt.subplots(figsize=(8,2.4));pos=list(range(len(be)))
        ax.bar([x-.18 for x in pos],[float(r['right']) for r in be],width=.35,label=benchmark_labels(benchmark)[1],color='#176C8C');ax.bar([x+.18 for x in pos],[float(r['left']) for r in be],width=.35,label=benchmark_labels(benchmark)[0],color='#82939F')
        peak=max(float(r[k]) for r in be for k in ('left','right'));top_limit=peak*1.30
        for i,r in enumerate(be):
            pair_top=max(float(r['right']),float(r['left']))
            ax.text(i,pair_top+peak*0.03,'差额 '+number(r['delta']),ha='center',va='bottom',fontsize=8.5,color='#444444')
            ax.text(i-.18,float(r['right'])+peak*0.012,number(r['right']),ha='center',va='bottom',fontsize=8,color='#176C8C')
            ax.text(i+.18,float(r['left'])+peak*0.012,number(r['left']),ha='center',va='bottom',fontsize=8,color='#5A626B')
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
