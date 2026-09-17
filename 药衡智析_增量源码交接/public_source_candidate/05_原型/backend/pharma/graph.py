"""制药知识图谱（赛题加分项）：把产品配方与工艺路线构建为图，辅助混合检索。

设计原则：
- 图谱从当前知识库快照的已解析分片中确定性抽取（规则版本化），
  不引入外部图谱依赖；知识版本变化时图谱自动重建；
- 边只来自文档中明确出现的成分表与工艺箭头链，剂量/页码作为边属性
  保留溯源；解析不到的内容不编造节点；
- 检索增强方式受控：只把图谱邻居（该产品的药材名、工序名）补充进
  BM25 查询词，不改变向量检索与适用性合同，召回仍受原合同约束。
"""
import hashlib
import json
import re
import time

GRAPH_RULES_VERSION = 'pharma-recipe-process-v1'

# 部分题包 PDF 使用康熙部首区字符（如 ⻩/⻄），统一归一化为常用汉字，
# 保证术语、产品名与抽取出的实体可互相匹配。表为按需补充的部分映射。
_RADICAL_MAP = str.maketrans({'⻩': '黄', '⻄': '西', '⻛': '风', '⻘': '青', '⻋': '车', '⻅': '见', '⻉': '贝', '⻢': '马'})


def normalize_entity(text):
    return text.translate(_RADICAL_MAP).strip()


# 处方行：序号 + 药材名 + 数量（kg/g）。剂量后必须还有列内容（行尾恰好
# 以数字结束的行不抽取：该放宽曾改变证据集并引发模型重掷，按v18b口径保留）。
_RECIPE_ROW = re.compile(r'^\s*\d{1,3}\s+([^\s\d][^ ]{0,15}?)\s+(\d+(?:\.\d+)?)\s')
# 工艺链：按各类箭头切分，段内再取首个括号前的工序名。
_ARROW_SPLIT = re.compile(r'[─├└│\-]+\s*[→>]+\s*|→')
_STEP_INLINE = re.compile(r'^(.{2,14}?)(?:\s*[（(].*)?$')


def _is_material(name):
    """药材名：2~8 个汉字，排除合计/符号/说明行。"""
    return 2 <= len(name) <= 8 and re.fullmatch(r'[\u4e00-\u9fff]+', name) is not None and name not in ('以上', '合计', '处方量')


def _clean_step(token):
    token = normalize_entity(re.sub(r'\s+', '', token))
    if not 2 <= len(token) <= 14:
        return None
    if not re.search(r'[\u4e00-\u9fff]', token):
        return None
    # 中间产物（提取液/浓缩液等）保留为节点，但句子、纯流向词不建节点
    if token in ('然后', '依次', '备用', '待用', '送') or any(mark in token for mark in '，。；：、'):
        return None
    return token


class KnowledgeGraph:
    """单一知识上下文（企业/行业包）对应的配方-工艺图谱。"""

    def __init__(self, knowledge):
        """knowledge: 已定位到当前版本的 Knowledge 实例。"""
        self.knowledge = knowledge
        self.root = knowledge.path / 'graph'
        self.root.mkdir(parents=True, exist_ok=True)

    # ---- 构建与加载 -------------------------------------------------
    def version_key(self, knowledge_version):
        digest = hashlib.sha256(f'{knowledge_version}:{GRAPH_RULES_VERSION}'.encode()).hexdigest()[:16]
        return f'{knowledge_version[:12]}-{digest}'

    def load(self, rebuild=False):
        """返回当前知识版本对应的图谱；未构建时先按检索同款逻辑建索引。"""
        status = self.knowledge.status()
        if status.get('status') == 'NOT_BUILT':
            try:
                status = self.knowledge.build()
            except Exception as exc:
                return {'status': 'DEGRADED', 'reason': '知识库构建失败：' + type(exc).__name__, 'nodes': [], 'edges': []}
        if status.get('status') == 'FAILED' or not status.get('knowledge_version'):
            reason = '知识库构建失败' if status.get('status') == 'FAILED' else '知识库尚未构建，先执行知识库构建任务'
            return {'status': 'NOT_BUILT', 'reason': reason, 'nodes': [], 'edges': []}
        knowledge_version = status['knowledge_version']
        target = self.root / (self.version_key(knowledge_version) + '.json')
        if target.is_file() and not rebuild:
            graph = json.loads(target.read_text(encoding='utf-8'))
        else:
            graph = self._build(knowledge_version)
            # 唯一临时名防并发交错；Windows 不能替换被占用的目标文件
            import uuid
            tmp = target.with_name(f'{target.stem}.{uuid.uuid4().hex[:8]}.tmp')
            tmp.write_text(json.dumps(graph, ensure_ascii=False), encoding='utf-8')
            tmp.replace(target)
        return graph

    def _chunks(self, knowledge_version):
        path = self.knowledge.path / knowledge_version / 'chunks.json'
        if not path.is_file():
            return []
        return json.loads(path.read_text(encoding='utf-8'))

    def _build(self, knowledge_version):
        chunks = self._chunks(knowledge_version)
        nodes, edges = {}, []
        node_seen, edge_seen = set(), set()

        def node(node_id, node_type, label, **props):
            key = (node_type, node_id)
            if key not in node_seen:
                node_seen.add(key)
                nodes[node_id] = {'id': node_id, 'type': node_type, 'label': label, 'props': props}
            return node_id

        def edge(src, dst, relation, **props):
            key = (src, relation, dst, json.dumps(props.get('dose', ''), ensure_ascii=False))
            if key not in edge_seen and src != dst:
                edge_seen.add(key)
                edges.append({'source': src, 'target': dst, 'relation': relation, 'props': props})

        from .knowledge import pharmaceutical_terminology
        products = [normalize_entity(p) for p in pharmaceutical_terminology()['products']]
        material_labels = set()

        def product_of(chunk, fallback_text=''):
            declared = [normalize_entity(p) for p in chunk.get('products') or []]
            if len(declared) == 1:
                return declared[0]
            text = normalize_entity(fallback_text)
            for p in products:
                if p in normalize_entity(chunk.get('source', '')) or p in text:
                    return p
            return None

        # 第一遍：配方成分（药材与剂量），第二遍：工艺链（工序顺序）。
        # 两遍扫描不依赖文件名排序，药材集合在工序解析前已完整。
        for chunk in chunks:
            source = chunk.get('source', '')
            text = normalize_entity(chunk.get('text', ''))
            if '配方' not in source:
                continue
            product = product_of(chunk)
            if not product:
                continue
            pid = node(product, 'product', product)
            for line in text.splitlines():
                match = _RECIPE_ROW.match(normalize_entity(line))
                if not match:
                    continue
                material, dose = match.group(1), match.group(2)
                if not _is_material(material):
                    continue
                material_labels.add(material)
                mid = node('material:' + material, 'material', material)
                edge(pid, mid, '成分', dose=dose, unit='kg',
                     source=source, location=chunk.get('location'))
        for chunk in chunks:
            source = chunk.get('source', '')
            text = normalize_entity(chunk.get('text', ''))
            if '工艺' not in source:
                continue
            product = product_of(chunk)
            if not product:
                continue
            pid = node(product, 'product', product)
            chain = []
            for segment in _ARROW_SPLIT.split(text):
                stripped = segment.strip()
                match = _STEP_INLINE.match(stripped)
                step = _clean_step(match.group(1)) if match else None
                # 链首常是产品名或药材名，它们不是工序节点
                if step and step != product and step not in material_labels:
                    chain.append(step)
            deduped = list(dict.fromkeys(chain))
            for order, step in enumerate(deduped):
                sid = node('process:' + step, 'process', step)
                edge(pid, sid, '工序', order=order, source=source, location=chunk.get('location'))
            for left, right in zip(deduped, deduped[1:]):
                edge('process:' + left, 'process:' + right, '工序顺序', source=source)
        stats = {'products': sum(1 for n in nodes.values() if n['type'] == 'product'),
                 'materials': sum(1 for n in nodes.values() if n['type'] == 'material'),
                 'process_steps': sum(1 for n in nodes.values() if n['type'] == 'process'),
                 'edges': len(edges)}
        graph = {'status': 'PASS' if stats['products'] else 'EMPTY',
                 'reason': None if stats['products'] else '当前知识源未解析出配方或工艺结构',
                 'graph_version': self.version_key(knowledge_version),
                 'knowledge_version': knowledge_version, 'rules_version': GRAPH_RULES_VERSION,
                 'nodes': list(nodes.values()), 'edges': edges, 'stats': stats, 'built_at': time.time()}
        return graph

    # ---- 检索扩展 ---------------------------------------------------
    def expansion_terms(self, product, query, limit=6):
        """返回该产品在图谱中的药材/工序列表，用作 BM25 补充词。

        只在图谱存在且产品命中时扩展；已出现在原查询中的词不重复加入。
        """
        graph = self.load()
        if graph.get('status') != 'PASS':
            return {'status': graph.get('status'), 'terms': [], 'graph_version': graph.get('graph_version')}
        product = normalize_entity(product or '')
        query_norm = normalize_entity(query or '')
        materials, steps = [], []
        for edge in graph['edges']:
            label = next((n['label'] for n in graph['nodes'] if n['id'] == edge['source']), '')
            if edge['relation'] == '成分' and label == product:
                materials.append((float(edge['props'].get('dose') or 0), next(
                    (n['label'] for n in graph['nodes'] if n['id'] == edge['target']), edge['target'])))
            elif edge['relation'] == '工序' and label == product:
                steps.append((int(edge['props'].get('order') or 0), next(
                    (n['label'] for n in graph['nodes'] if n['id'] == edge['target']), edge['target'])))
        materials.sort(reverse=True)
        steps.sort()
        terms = []
        for _dose, name in materials:
            if name not in query_norm and name not in terms:
                terms.append(name)
        for _order, name in steps:
            if name not in query_norm and name not in terms:
                terms.append(name)
        used = terms[:limit]
        return {'status': 'EXPANDED' if used else 'NO_NEIGHBORS', 'terms': used,
                'graph_version': graph['graph_version'],
                'material_count': len(materials), 'process_count': len(steps)}


def graph_for_context(context):
    """按分析上下文定位 Knowledge 并返回对应图谱（竞争/制药走私有文档集）。"""
    from .knowledge import Knowledge
    if not context or (not context.get('industry_id')):
        knowledge = Knowledge()
    else:
        knowledge = Knowledge(context=context)
    return KnowledgeGraph(knowledge)
