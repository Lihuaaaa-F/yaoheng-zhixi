# -*- coding: utf-8 -*-
"""导入数据报告走完整模板渲染的契约测试（2026-09-28 改道）。

钉住四件事：
① 路由谓词只放行 competition 与 imp-* 前缀（演示上下文保持 reference 简版）；
② 显示层适配器只改英文单数要素键，不改任何数值（竞赛形快照恒等）；
③ 导入快照经完整模板管线渲染后通过模板占位符 verify 合同，话术诚实
   （无"比赛模拟数据/ERP系统/中药二厂"失实，缺值一律 NA/缺席）；
④ 两条评审阻断的护栏：缺要素快照响亮失败（IMPORT_ELEMENTS_INCOMPLETE），
   要素 unit=None 不崩（图表统一过滤）。
"""
import os
import json, re, shutil
import pytest
from docx import Document

from pharma.reports import (build_bindings, render_docx, verify_docx, working_template,
                            TEMPLATE, MAP_PATH,
                            _full_template_context, _is_import, _import_template_view)

def _installed_placeholders():
    """书签核对必须用本次渲染模板的占位符清单（reports.py verify 注释：
    安装模板书签前缀与题包 MAP 不同，死读题包 map 会全量误判 null）。"""
    _,map_path=working_template('monthly')
    return json.loads(map_path.read_text(encoding='utf-8'))['placeholders']


def _element(key, name, unit='12.34', **over):
    e={'key':key,'name':name,'unit':unit,'total':'431900.00','share':'70.24',
       'unit_mom':'2.10','unit_delta':'0.25','total_delta':'8750.00','delta':'0.25',
       'contribution':'31.20','alerts':[],'comparisons':{}}
    e.update(over);return e

def import_snapshot(**over):
    """手工最小导入快照：与 industry.analyze_reference 的导入合同同构
    （elements 单数三键、materials_summary/expenses_summary/labor_metrics/
    details.market 全空、data_provenance='user_import'、limits[0]=数据标签）。"""
    s={'snapshot_contract_version':'test','report_template':{'sections':[]},
       'context_id':'pharmaceutical:imp-test0001','snapshot_id':'imp-snapshot-0001',
       'formula_version':'test-formula','factory':'中药一厂','product':'六味地黄胶囊',
       'month':'2026-06','analysis_type':'monthly','basis':'unit','specification':'200 粒',
       'period':{'start':'2026-06','end':'2026-06'},
       'metrics':{'quantity':{'value':'35000','unit':'盒'},'unit_cost':{'value':'17.57','unit':'元/盒'},
                  'total_cost':{'value':'614950.00','unit':'元'},
                  'mom':{'value':None,'unit':'%'},'yoy':{'value':None,'unit':'%'},'budget':{'value':None,'unit':'%'}},
       'elements':[_element('material','材料'),_element('labor','人工',unit='3.21',share='18.28',
                   unit_mom='-0.40',unit_delta='-0.04',total_delta='-1400.00',contribution='5.00',total='112350.00'),
                   _element('overhead','制造费用',unit='2.02',share='11.47',
                   unit_mom='-0.80',unit_delta='-0.08',total_delta='-2800.00',contribution='10.00',total='70700.00')],
       'trend':[{'month':'2026-05','unit_cost':'17.80','total_cost':'623000.00','quantity':'35000','material':'12.50','labor':'3.20','overhead':'2.10'},
                {'month':'2026-06','unit_cost':'17.57','total_cost':'614950.00','quantity':'35000','material':'12.34','labor':'3.21','overhead':'2.02'}],
       'alerts':[],
       'comparison':{'mom':{'base':'17.32','current':'17.57','rate':None,'delta':None},
                     'yoy':{'base':None,'rate':None,'delta':None},'budget':{'base':None,'rate':None,'delta':None}},
       'details':{'available':False,'reason':'当前数据仅含已归集成本与已接入驱动事实；不推算采购/BOM明细',
                  'materials':[],'expenses':[],'labor':[],'market':[]},
       'industry':{'rows':[],'converted_unit_cost':'17.57','unit':'元/盒','notice':''},
       'budget_bridge':None,
       'period_values':{},
       'period_changes':{'quantity':{'mom':{'rate':None,'delta':'-500'}},
                         'unit_cost':{'mom':{'rate':None,'delta':'0.25'}},
                         'total_cost':{'mom':{'rate':None,'delta':'8750.00'}}},
       'materials_summary':[],'expenses_summary':[],'labor_metrics':{},
       'source_hashes':[],'quantity_unit':'盒','currency':'CNY',
       'data_label':'用户导入数据（数据中心发布）','data_provenance':'user_import','capabilities':[],
       'limits':['用户导入数据（数据中心发布）',
                 '未支持联副产品分配和在制品计价；缺少实际价格/实耗不能严格价量分解',
                 '维修记录仅支持待验证假设；不是已证实净原因'],
       'comparison_scope':{},'specialized_metrics':[]}
    s.update(over);return s

def import_narrative():
    """rules 形叙事 + 一条模型缺证解释（section 用导入单数键 material）。"""
    return {'findings':[
        {'section':'material','claim_type':'insufficient_evidence','origin':'model',
         'rendered_text':'材料缺证说明：未提供采购入库单与批次领退料记录，不能确定材料成本变动原因。',
         'missing_evidence':['采购入库单']},
        {'section':'material','claim_type':'recommendation','origin':'rules',
         'suggestion':'核对采购合同单价与批次领退料记录，确认材料单价与单耗的各自影响',
         'verification_target':'材料采购与领料记录','responsible_role':'成本会计',
         'department':'财务部','priority':'high','deadline_basis':'下次成本复核前',
         'expected_evidence':['采购合同','领料单']}], 'model_live':False, 'status':'DEGRADED'}


def test_full_template_context_predicate():
    assert _full_template_context('pharmaceutical:competition') is True
    assert _full_template_context('pharmaceutical:imp-abc123') is True
    # 演示上下文继续走 reference 简版；空 context_id 语义不变（落入完整模板分支
    # 由调用方缺省合同决定，谓词本身不放行也不拦截 None）。
    assert _full_template_context('pharmaceutical:synthetic-pharma') is False
    assert _full_template_context('mechanical_demo:synthetic-mechanical') is False
    assert _full_template_context('chemical_demo:synthetic-chemical') is False


def test_import_view_maps_keys_only():
    s=import_snapshot();n=import_narrative()
    before=json.dumps(s['elements'],ensure_ascii=False,sort_keys=True)
    view,vn=_import_template_view(s,n)
    # 键映射：elements/trend/section 单数→复数
    assert [e['key'] for e in view['elements']]==['materials','labor','overhead']
    assert all('materials' in r and 'material' not in r for r in view['trend'])
    assert [f['section'] for f in vn['findings']][0]=='materials'
    # 数值零改动：映射后 elements 序列化仅 key 字段不同
    stripped=[{**e,'key':{'material':'materials'}.get(e['key'],e['key'])} for e in s['elements']]
    assert json.dumps(stripped,ensure_ascii=False,sort_keys=True)==json.dumps(view['elements'],ensure_ascii=False,sort_keys=True)
    assert view['metrics']==s['metrics'] and view['trend'][0]['month']==s['trend'][0]['month']
    # 幂等：竞赛形（复数键）快照原样返回；重复映射不变形
    competition_like=import_snapshot(data_provenance='synthetic_fixture')
    for e in competition_like['elements']:e['key']={'material':'materials'}.get(e['key'],e['key'])
    again=_import_template_view(competition_like)
    assert again['elements']==competition_like['elements']
    # metrics 不映射（模型 metric_refs 仍指向单数指标键）
    assert 'material' in s['trend'][0] and 'materials' in view['trend'][0]


def test_import_missing_element_fails_loud():
    s=import_snapshot()
    s['elements']=[_element('material','材料')]  # 仅映射直接材料的成本汇总（质检只要求 ≥1 要素列）
    with pytest.raises(ValueError) as exc:
        _import_template_view(s)
    message=str(exc.value)
    assert 'IMPORT_ELEMENTS_INCOMPLETE' in message
    assert 'labor' in message and 'overhead' in message
    assert '材料/人工/制造费用' in message  # 明确的映射指引，替代裸 KeyError


def test_import_none_unit_elements(tmp_path):
    # 三要素齐备但产量缺失 → 要素 unit=None（industry.py 允许）：渲染不崩，
    # 该要素行为 NA，饼图/预算柱统一过滤后跳过该要素；趋势行 unit_cost=None 同守卫。
    s=import_snapshot()
    s['elements'][0]['unit']=None
    s['trend']=[{'month':'2026-06','unit_cost':None,'total_cost':'614950.00','quantity':None,'material':None,'labor':None,'overhead':None}]
    path=tmp_path/'none_unit.docx'
    result=render_docx(s,import_narrative(),{'evidence':[]},path)
    assert result['status']=='PASS' and result['verification']['status']=='PASS'
    text='\n'.join(p.text for p in Document(path).paragraphs)
    assert 'N/A' in text  # 缺值以 NA 呈现，不虚构
    assert verify_docx(path,s,narrative=import_narrative(),placeholders=_installed_placeholders())['status']=='PASS'
    # 全要素 unit=None：饼图与预算柱整体缺席=诚实缺席
    s2=import_snapshot()
    for e in s2['elements']:e['unit']=None
    path2=tmp_path/'all_none.docx'
    result2=render_docx(s2,import_narrative(),{'evidence':[]},path2)
    assert result2['status']=='PASS'


def test_import_snapshot_renders_template_contract(tmp_path):
    s=import_snapshot();n=import_narrative();path=tmp_path/'import.docx'
    result=render_docx(s,n,{'evidence':[]},path)
    check=result['verification']
    assert check['status']=='PASS'
    assert check['numeric_bindings_checked']>=70 and check['tables']>=11 and check['images']>0
    assert len(check['headings'])==6 and not check['residual_placeholders']
    doc=Document(path)
    chapters=[p.text for p in doc.paragraphs if re.match(r'^[一二三四五六七八九十]+、',p.text)]
    for required in ('一、封面与基本信息','二、总成本概览','三、成本要素明细分析','四、重点产品专项分析','六、总结与建议','七、编制说明','十、人工归因评分'):
        assert any(c.startswith(required) for c in chapters), chapters
    # 页脚"第X页 共Y页"字段与核心数字
    footer=''.join(x.text or '' for x in doc.sections[0].footer._element.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
    assert '第' in footer and '页' in footer
    all_text='\n'.join(p.text for p in doc.paragraphs)
    for t in doc.tables:
        for row in t.rows:all_text+='\n'+'|'.join(c.text for c in row.cells)
    assert '17.57' in all_text and '614950.00' in all_text
    assert 'N/A：无可用明细' in all_text  # 空明细表落骨架行（诚实缺席）


def test_import_honest_wording(tmp_path):
    s=import_snapshot();path=tmp_path/'honest.docx'
    render_docx(s,import_narrative(),{'evidence':[]},path)
    doc=Document(path)
    all_text='\n'.join(p.text for p in doc.paragraphs)
    for t in doc.tables:
        for row in t.rows:all_text+='\n'+'|'.join(c.text for c in row.cells)
    # ① 编制说明：导入话术，不出"比赛模拟数据/ERP系统"
    assert '本报告依据用户导入数据及当前知识版本生成。缺失字段不推算为真实数据，原因判断须结合业务资料核实。' in all_text
    assert '数据来源于用户导入数据（数据中心发布）' in all_text
    assert '比赛模拟数据' not in all_text
    # ② 表1-1 数据来源行 = 数据中心标签（sanitize_template_identity 按快照改写）
    identity=[]
    for t in doc.tables:
        for row in t.rows:
            cells=[c.text.strip() for c in row.cells]
            for i,c in enumerate(cells):
                if c.rstrip('：:')=='数据来源':identity.append(cells[i+1] if i+1<len(cells) else '')
    assert identity==['用户导入数据（数据中心发布）']
    # ③ 无对标：五章标题与 5.3 默认句不含"中药二厂/两厂核对"
    assert '五、对标分析（未选择跨厂比较）' in all_text
    assert '中药二厂' not in all_text
    assert '未选择跨厂比较；不构造明细或归因。' in all_text
    # ④ 需关注问题 = 快照自带数据边界（limits[1:]，limits[0] 数据标签不列为问题）
    assert '数据边界：未支持联副产品分配和在制品计价；缺少实际价格/实耗不能严格价量分解；维修记录仅支持待验证假设；不是已证实净原因。' in all_text
    # ⑤ 明细表 NA 骨架行 + 不虚构材料明细
    assert 'N/A：无可用明细' in all_text


def test_import_materials_prose_and_explanation(tmp_path):
    s=import_snapshot();n=import_narrative();path=tmp_path/'prose.docx'
    render_docx(s,n,{'evidence':[]},path)
    rendered='材料缺证说明：未提供采购入库单与批次领退料记录，不能确定材料成本变动原因。'
    # 渲染侧：模型解释逐字落在 3.1 节（prose 收集）
    doc=Document(path)
    section=None;in_section=False
    for p in doc.paragraphs:
        text=p.text
        if text.startswith('3.1'):in_section=True;continue
        if re.match(r'^3\.2|^[一二三四五六]、',text):in_section=False
        if in_section and rendered in text:break
    else:
        raise AssertionError('模型解释未落在 3.1 节：'+rendered)
    # 校验侧：explanation_presence scoped 分节匹配通过（双向钉住防"渲染缺失但校验通过"漂移）
    check=verify_docx(path,s,narrative=n,placeholders=_installed_placeholders())
    assert check['status']=='PASS'
    assert check['explanation_bindings_checked']==1 and not check['explanation_binding_failures']


@pytest.mark.skipif(os.environ.get('PHARMA_TEST_COMPETITION_DATA') != '1',
                    reason='competition asset integration requires PHARMA_TEST_COMPETITION_DATA=1')
def test_competition_bindings_untouched_by_adapter():
    from pharma.industry import analyze_reference
    snapshot=analyze_reference('pharmaceutical:competition',month='2026-06')
    narrative={'findings':[{'section':'materials','claim_type':'insufficient_evidence','origin':'model','rendered_text':'竞赛解释'}]}
    direct=build_bindings(snapshot,narrative)
    adapted=build_bindings(_import_template_view(snapshot),narrative)
    assert direct==adapted  # 回归哨兵：竞赛形快照过适配器后绑定逐键相等


def test_import_report_keeps_header_branding(tmp_path, monkeypatch):
    """页眉水印保留（2026-09-28 裁定反转，取代 has_no_header_branding）：全部
    报告（导入与竞赛）统一完整模板版式，页眉（创灵境水印艺术字/"整体解决方案"）
    原样保留，无一节页眉被清空；页眉文字不进正文段落（正文残留"整体解决方案"
    仍按 2026-09-23 清理改写）；页脚页码不受影响。模板来源确定性：临时 runtime
    装入已知带页眉的工作模板（1 节、rId8→header4），不依赖生产已装模板状态。"""
    rt=tmp_path/'rt-templates';rt.mkdir()
    shutil.copyfile(TEMPLATE,rt/'monthly.docx')
    shutil.copyfile(MAP_PATH,rt/'monthly.placeholder_map.json')
    monkeypatch.setattr('pharma.reports.RUNTIME_TEMPLATES',rt)
    s=import_snapshot();path=tmp_path/'import.docx'
    render_docx(s,import_narrative(),{'evidence':[]},path)
    doc=Document(path)
    nonlinked=0;branded=0
    for section in doc.sections:
        for hdr in (section.header,section.first_page_header,section.even_page_header):
            if hdr.is_linked_to_previous:continue
            nonlinked+=1
            hxml=hdr._element.xml
            # 水印形状（textpath 艺术字，含"创灵境"）原样保留
            if 'textpath' in hxml.lower() and '创灵境' in hxml:branded+=1
    assert nonlinked>0 and branded==nonlinked
    assert any('整体解决方案' in ''.join(p.text for p in h.paragraphs)
               for sec in doc.sections
               for h in (sec.header,sec.first_page_header,sec.even_page_header)
               if not h.is_linked_to_previous)  # 正文节页眉"整体解决方案"文字保留
    # 页眉文字不在正文段落里：正文副标题仍被残留清理改写为"产品成本智能分析报告"
    body='\n'.join(p.text for p in doc.paragraphs)
    assert '整体解决方案' not in body
    assert '产品成本智能分析报告' in body
    footer=''.join(x.text or '' for x in doc.sections[0].footer._element.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
    assert '第' in footer and '页' in footer


@pytest.mark.skipif(not __import__('os').getenv('PHARMA_E2E_SLOW'),reason='慢速隔离 E2E：设 PHARMA_E2E_SLOW=1 执行（默认不进快速门）')
def test_import_isolated_e2e_smoke(tmp_path):
    """Real API + queue + content checks; separate process prevents shared state."""
    import os, subprocess, sys
    from pathlib import Path
    if not shutil.which('soffice'):pytest.skip('需要已安装的 LibreOffice 才能验证真实 PDF')
    root=Path(__file__).resolve().parents[2]
    env={k:v for k,v in os.environ.items() if not k.startswith(('PHARMA_','GLM_','ZHIPU_'))}
    templates=tmp_path/'templates';templates.mkdir()
    source,mapping=working_template('monthly')
    shutil.copy2(source,templates/'月度成本分析报告工作模板.docx')
    shutil.copy2(mapping,templates/'placeholder_map.json')
    env.update(PYTHONPATH=str(root/'05_原型/backend'), PHARMA_RUNTIME_DIR=str(tmp_path/'runtime'),
        PHARMA_ARTIFACTS_DIR=str(tmp_path/'候选测试件'),PHARMA_TEMPLATE_DIR=str(templates),
        PHARMA_API_KEY='',PHARMA_MODEL_KEY_FILE=str(tmp_path/'no-key'),PHARMA_AUTO_EXPLAIN='0',
        PHARMA_API_TOKEN='',TMPDIR='/tmp')
    completed=subprocess.run([sys.executable,str(root/'05_原型/scripts/check_import_report.py')],
        env=env,cwd=root,text=True,capture_output=True,timeout=240)
    assert completed.returncode==0,completed.stdout+'\n'+completed.stderr
    result=json.loads(completed.stdout.strip().splitlines()[-1])
    assert result['status']=='PASS' and result['model_calls']==0
    assert {r['kind'] for r in result['reports']}=={'monthly','quarterly','special'}
