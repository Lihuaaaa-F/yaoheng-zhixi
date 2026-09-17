"""知识图谱（赛题加分项）：配方/工艺抽取、归一化与检索扩展合同。"""
import json
import pytest
from pharma import graph as knowledge_graph


class FakeKnowledge:
    """只提供图谱所需接口的最小替身：status() 与当前版本分片。"""

    def __init__(self, root, version, chunks):
        self.path = root
        version_dir = root / version
        version_dir.mkdir(parents=True)
        (version_dir / 'chunks.json').write_text(json.dumps(chunks, ensure_ascii=False), encoding='utf-8')
        self.version = version

    def status(self):
        return {'status': 'PASS', 'knowledge_version': self.version}


@pytest.fixture
def pharma_chunks():
    # 覆盖康熙部首归一（⻩→黄）、处方行解析与箭头工艺链
    return [
        {'source': '产品配方文档_六味地黄胶囊.pdf', 'products': ['六味地⻩胶囊'], 'location': '第3页',
         'heading': '二、处方组成(每1000粒/300g内容物)',
         'text': '序号 原料名称 处方量 (kg) 药材来源 质量标准\n1 熟地⻩ 1.20 河南焦作 CP2025\n2 山茱萸 0.60 陕⻄汉中 CP2025\n3 山药 0.60 河南焦作 CP2025'},
        {'source': '生产工艺文档_中药一厂.pdf', 'products': ['六味地⻩胶囊'], 'location': '第2页',
         'heading': '二、六味地⻩胶囊 生产工艺路线',
         'text': '熟地⻩ ─→ 粉碎 (80目) ─→ 过筛 ─→ 混合 ─→ 分装 (胶囊)'},
        {'source': '无关文档.pdf', 'products': [], 'location': '第1页', 'heading': '', 'text': '与图谱无关的正文内容。'},
    ]


def build_graph(tmp_path, chunks):
    knowledge = FakeKnowledge(tmp_path, 'v_test_123456', chunks)
    return knowledge_graph.KnowledgeGraph(knowledge)


def test_graph_extracts_materials_with_doses_and_normalization(tmp_path, pharma_chunks):
    g = build_graph(tmp_path, pharma_chunks)
    result = g.load()
    assert result['status'] == 'PASS'
    materials = {n['label']: n for n in result['nodes'] if n['type'] == 'material'}
    assert {'熟地黄', '山茱萸', '山药'} <= set(materials)  # ⻩/⻄ 已归一化
    recipe_edges = [e for e in result['edges'] if e['relation'] == '成分']
    doses = {e['props']['dose'] for e in recipe_edges}
    assert {'1.20', '0.60'} <= doses
    assert all(e['props']['unit'] == 'kg' for e in recipe_edges)
    assert result['stats']['products'] == 1


def test_graph_extracts_process_chain_and_skips_material_head(tmp_path, pharma_chunks):
    g = build_graph(tmp_path, pharma_chunks)
    result = g.load()
    steps = [e['target'].split(':', 1)[1] for e in result['edges'] if e['relation'] == '工序']
    assert {'粉碎', '过筛', '混合', '分装'} <= set(steps)
    assert '熟地黄' not in steps  # 链首药材不作为工序
    order_edges = [(e['source'].split(':', 1)[1], e['target'].split(':', 1)[1]) for e in result['edges'] if e['relation'] == '工序顺序']
    assert ('粉碎', '过筛') in order_edges and ('过筛', '混合') in order_edges


def test_graph_versioned_and_cached(tmp_path, pharma_chunks):
    g = build_graph(tmp_path, pharma_chunks)
    first = g.load()
    second = g.load()  # 第二次读取缓存文件
    assert first == second
    assert first['rules_version'] == knowledge_graph.GRAPH_RULES_VERSION
    files = list((tmp_path / 'graph').glob('*.json'))
    assert len(files) == 1 and first['graph_version'] in files[0].name


def test_expansion_terms_for_product_exclude_query_words(tmp_path, pharma_chunks):
    g = build_graph(tmp_path, pharma_chunks)
    expansion = g.expansion_terms('六味地黄胶囊', '成本 工序')
    assert expansion['status'] == 'EXPANDED'
    assert '熟地黄' in expansion['terms'] and '粉碎' in expansion['terms']
    assert '工序' not in expansion['terms']  # 查询已有的词不重复
    again = g.expansion_terms('六味地黄胶囊', '熟地黄 山茱萸 山药 粉碎 过筛 混合 分装')
    assert again['terms'] == [] and again['status'] == 'NO_NEIGHBORS'


def test_unknown_product_has_no_neighbors(tmp_path, pharma_chunks):
    g = build_graph(tmp_path, pharma_chunks)
    expansion = g.expansion_terms('不存在的品种', '成本')
    assert expansion['status'] == 'NO_NEIGHBORS' and expansion['terms'] == []


def test_no_recipe_or_process_yields_empty_graph(tmp_path):
    g = build_graph(tmp_path, [{'source': '其他.json', 'products': [], 'text': '无结构内容'}])
    result = g.load()
    assert result['status'] == 'EMPTY' and result['nodes'] == []


def test_not_built_knowledge_reports_not_built(tmp_path):
    class NotBuilt:
        path = tmp_path / 'kb'
        def status(self):
            return {'status': 'NOT_BUILT'}
        def build(self):
            # 真实失败路径：build 返回 FAILED 且可能带版本号（无可用分片）
            return {'status': 'FAILED', 'failures': [], 'knowledge_version': 'deadbeef'}
    result = knowledge_graph.KnowledgeGraph(NotBuilt()).load()
    assert result['status'] == 'NOT_BUILT' and result['nodes'] == []
