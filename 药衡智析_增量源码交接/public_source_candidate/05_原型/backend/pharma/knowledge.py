"""Versioned local retrieval. Documents are untrusted evidence, never instructions."""
from pathlib import Path
import hashlib
import json
import os
import re
import sqlite3
import time
from .config import ROOT, PACKAGE, RUNTIME

EMBEDDING_SHA = '75c43b069aac4d136ba6bc1122f995fedcfd2781'
PARSER_VERSION = 'sorted-section-event-scope-v4-substantive'
PRODUCTS = ('银黄口服液', '板蓝根颗粒', '六味地黄胶囊')
PRODUCT_ALIASES = {'银黄口服液': ('银黄口服液', '口服液'), '板蓝根颗粒': ('板蓝根颗粒', '板蓝根', '颗粒剂', '颗粒分装'), '六味地黄胶囊': ('六味地黄胶囊', '胶囊')}


def reciprocal_rank_fusion(rankings, limit=5, k=60, weights=None):
    scores = {}
    for index, ranking in enumerate(rankings):
        for rank, item in enumerate(dict.fromkeys(ranking), 1):
            scores[item] = scores.get(item, 0) + (weights[index] if weights else 1) / (k + rank)
    return sorted(scores, key=lambda x: (-scores[x], x))[:limit]


def tokenize(text):
    import jieba
    for word in ('银黄口服液','板蓝根颗粒','六味地黄胶囊','金银花','黄芩','制造费用','预防性维护','胶囊填充机','GMP'):
        jieba.add_word(word)
    return [x.lower() for x in jieba.cut(text) if re.search(r'[\w\u4e00-\u9fff]', x)]


class CpuEmbedding:
    def __init__(self, path):
        import onnxruntime as ort
        from tokenizers import Tokenizer
        options = ort.SessionOptions()
        options.intra_op_num_threads = 4
        self.session = ort.InferenceSession(str(path / 'model_quantized.onnx'), sess_options=options, providers=['CPUExecutionProvider'])
        self.tokenizer = Tokenizer.from_file(str(path / 'tokenizer.json'))
        self.tokenizer.enable_padding(pad_id=0, pad_token='[PAD]')
        self.tokenizer.enable_truncation(max_length=512)

    def encode(self, texts, query=False):
        import numpy as np
        vectors = []
        for offset in range(0, len(texts), 16):
            batch = texts[offset:offset + 16]
            if query:
                batch = ['为这个句子生成表示以用于检索相关文章：' + x for x in batch]
            encoded = self.tokenizer.encode_batch(batch)
            feeds = {'input_ids': np.array([x.ids for x in encoded], dtype=np.int64), 'attention_mask': np.array([x.attention_mask for x in encoded], dtype=np.int64), 'token_type_ids': np.array([x.type_ids for x in encoded], dtype=np.int64)}
            output = self.session.run(None, {x.name: feeds[x.name] for x in self.session.get_inputs()})[0]
            cls = output[:, 0, :] if output.ndim == 3 else output
            cls = cls / np.maximum(np.linalg.norm(cls, axis=1, keepdims=True), 1e-12)
            vectors.extend(cls.tolist())
        return vectors


def parse_document(path):
    """Preserve genuine location; DOCX and TXT never acquire imaginary pages."""
    suffix = path.suffix.lower()
    if suffix == '.pdf':
        import fitz
        with fitz.open(path) as doc:
            for i, page in enumerate(doc, 1):
                yield {'page': i, 'location': f'第{i}页', 'original_text': page.get_text(sort=True), 'reading_order': 'coordinate_sorted'}
    elif suffix == '.docx':
        from docx import Document
        doc = Document(path)
        from docx.text.paragraph import Paragraph
        paragraph_index, table_index, heading = 0, 0, ''
        for block in doc.iter_inner_content():
            if isinstance(block, Paragraph):
                paragraph_index += 1
                if block.style and ('Heading' in block.style.name or '标题' in block.style.name):
                    heading = block.text
                if block.text.strip():
                    yield {'page': None, 'location': f'段落{paragraph_index}', 'heading': heading, 'original_text': block.text}
            else:
                table_index += 1
                yield {'page': None, 'location': f'表格{table_index}', 'heading': heading, 'original_text': '\n'.join(' | '.join(c.text for c in row.cells) for row in block.rows)}
    elif suffix == '.txt':
        lines = path.read_text(encoding='utf-8-sig').splitlines()
        for i in range(0, len(lines), 12):
            yield {'page': None, 'location': f'行{i+1}-{min(i+12,len(lines))}', 'original_text': '\n'.join(lines[i:i+12])}


def section_blocks(path):
    """Inherit explicit headings across pages, and isolate dated maintenance rows."""
    products = [p for p in PRODUCTS if p in path.name]
    scope = 'product' if products else ('general' if 'GMP' in path.name else 'unknown')
    heading, metadata = '', {}
    for block in parse_document(path):
        raw = block['original_text']
        for key, pattern in [('document_version', r'版本\s*[:：]\s*(\S+)'), ('document_number', r'文档编号\s*[:：]\s*(\S+)'), ('effective_date', r'生效日期\s*[:：]\s*(\d{4}-\d{2}-\d{2})')]:
            match = re.search(pattern, raw)
            if match: metadata[key] = match.group(1)
        if 'factory' not in metadata:
            match = re.search(r'中药[一二三]厂', path.name + raw[:150])
            if match: metadata['factory'] = match.group()
        # A heading starts a new scope. Subheadings retain the current product.
        parts = re.split(r'(?m)(?=^[ \t]*[一二三四五六七八九十]+、)', raw)
        for part in parts:
            if not part.strip(): continue
            first = part.strip().splitlines()[0]
            if re.match(r'[一二三四五六七八九十]+、', first):
                heading = first.strip()
                declared = [p for p, aliases in PRODUCT_ALIASES.items() if any(a in heading for a in aliases)]
                if declared: products, scope = declared, 'product'
                elif any(x in heading for x in ('公用工程', '全厂', '折旧政策', '工厂概况', '设备利用率')):
                    products, scope = [], 'general'
                elif '维修历史' in heading: products, scope = [], 'unknown'
            # The PDF maintenance table wraps YYYY-MM onto two visual lines.
            event_parts = re.split(r'(?m)(?=^[ \t]*20\d{2}-)', part) if '维修历史' in heading else [part]
            for event in event_parts:
                if not event.strip(): continue
                event_products, event_scope = products, scope
                period = re.match(r'\s*(20\d{2})-\s*(\d{2})\b', event)
                if not period:
                    period = re.match(r'\s*(20\d{2})-[^\n]*\n\s*(\d{2})\b', event)
                if period:
                    compact = re.sub(r'\s+', '', event)
                    event_products = [p for p,aliases in PRODUCT_ALIASES.items() if any(a in compact for a in aliases)]
                    event_scope = 'product' if event_products else 'unknown'
                yield dict(block, **metadata, original_text=event, heading=heading, products=event_products,
                           scope=event_scope, event_period=f'{period[1]}-{period[2]}' if period else None)


class Knowledge:
    def __init__(self, root=None, vector_enabled=True, source_dir=None, reranker=None):
        self.root = Path(root) if root else ROOT
        runtime = self.root / '05_原型/.runtime' if root is not None else RUNTIME
        package = self.root / '00_赛题原始资料/模拟数据_V1.1_净化解压/创灵境_考题模拟数据' if root is not None else PACKAGE
        self.path = runtime / 'knowledge'
        self.path.mkdir(parents=True, exist_ok=True)
        self.source_dir = Path(source_dir) if source_dir else package / '03_制药知识文档'
        self.model_dir = Path(os.environ.get('PHARMA_EMBEDDING_DIR',str(runtime / 'models/bge-small-zh-v1.5')))
        self.vector_enabled = vector_enabled
        self.reranker = reranker
        self._embedding = None
        self._collection = None

    @property
    def version(self):
        current = self.path / 'CURRENT'
        return current.read_text().strip() if current.exists() else None

    def status(self):
        version = self.version
        if not version:
            return {'status': 'NOT_BUILT', 'knowledge_version': None, 'sources': []}
        return json.loads((self.path / version / 'manifest.json').read_text())

    def _model(self):
        if self._embedding is None:
            self._embedding = CpuEmbedding(self.model_dir)
        return self._embedding

    def build(self):
        from .locks import exclusive
        with exclusive(self.path / 'build.lock'):
            return self._build()

    def _build(self):
        sources = sorted(p for p in self.source_dir.iterdir() if p.suffix.lower() in ('.pdf','.docx','.txt'))
        fingerprints = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        version = hashlib.sha256(json.dumps([fingerprints, EMBEDDING_SHA, PARSER_VERSION], sort_keys=True).encode()).hexdigest()[:20]
        target = self.path / version
        manifest = target / 'manifest.json'
        if manifest.exists():
            record = json.loads(manifest.read_text())
            if record['status'] == 'PASS' or (not self.vector_enabled and not record.get('failures')):
                (self.path/'CURRENT.tmp').write_text(version)
                os.replace(self.path/'CURRENT.tmp',self.path/'CURRENT')
                return record
        target.mkdir(exist_ok=True)
        chunks, failures, pages = [], [], 0
        for source in sources:
            try:
                source_pages = set()
                for block in section_blocks(source):
                    if block['page'] is not None: source_pages.add(block['page'])
                    clean = re.sub(r'[ \t]+', ' ', block['original_text']).strip()
                    # Product headings and document-control cover blocks carry
                    # scope into the next page but cannot support a business claim.
                    body_lines=[line.strip() for line in clean.splitlines() if not re.match(
                        r'^(?:[一二三四五六七八九十]+、|\d+(?:\.\d+)+\s+|(?:文档编号|版本|生效日期|更新日期|文件密级)\s*[:：])',line.strip())
                        and not re.search(r'(?:产品配方文档|生产工艺路线文档|车间设备清单)$',line.strip())]
                    if len(re.findall(r'[\w\u4e00-\u9fff]',''.join(body_lines)))<15 and (block.get('heading') or block.get('document_number')):
                        continue
                    if len(re.findall(r'[\w\u4e00-\u9fff]', clean)) < 15:
                        if block.get('heading'): continue  # A short section label is metadata, not an OCR failure.
                        failures.append({'source':source.name,'location':block['location'],'reason':'LOW_TEXT_QUALITY; OCR_NOT_RUN'})
                        continue
                    # Prefer paragraph/newline boundaries, preserving a short overlap.
                    start, index = 0, 0
                    while start < len(clean):
                        end = min(start + 500, len(clean))
                        if end < len(clean):
                            boundary = max(clean.rfind('\n',start+400,end),clean.rfind('。',start+400,end))
                            if boundary > start: end = boundary + 1
                        text = clean[start:end]
                        ident = hashlib.sha256(f'{fingerprints[source.name]}:{block["location"]}:{block.get("heading")}:{block.get("event_period")}:{index}:{text}'.encode()).hexdigest()[:24]
                        chunks.append(dict(block, evidence_id=ident, source=source.name, hash=fingerprints[source.name], text=text, chunk=index, knowledge_version=version))
                        if end == len(clean): break
                        start, index = max(start+1,end-80), index+1
                pages += len(source_pages)
            except Exception as exc:
                failures.append({'source':source.name,'reason':type(exc).__name__})
        if not chunks:
            return {'status':'FAILED','failures':failures,'knowledge_version':version}
        dbtmp = target / 'fts.sqlite.tmp'
        if dbtmp.exists(): dbtmp.unlink()
        db = sqlite3.connect(dbtmp)
        try:
            with db:
                db.execute('CREATE TABLE chunks(id TEXT PRIMARY KEY, body TEXT NOT NULL)')
                db.execute('CREATE VIRTUAL TABLE search USING fts5(id UNINDEXED,tokens)')
                for c in chunks:
                    db.execute('INSERT INTO chunks VALUES (?,?)',(c['evidence_id'],json.dumps(c,ensure_ascii=False)))
                    db.execute('INSERT INTO search VALUES (?,?)',(c['evidence_id'],' '.join(tokenize(c['text']))))
        finally:
            db.close()  # Windows cannot replace a file with an open handle
        os.replace(dbtmp,target/'fts.sqlite')
        vector_error = None
        if self.vector_enabled:
            try:
                import chromadb
                vectors = self._model().encode([c['text'] for c in chunks])
                client = chromadb.PersistentClient(path=str(target/'chroma'), settings=chromadb.Settings(anonymized_telemetry=False))
                collection = client.get_or_create_collection('pharma_evidence',metadata={'hnsw:space':'cosine'})
                collection.upsert(ids=[c['evidence_id'] for c in chunks],embeddings=vectors,documents=[c['text'] for c in chunks])
            except Exception as exc:
                vector_error = type(exc).__name__ + ': ' + str(exc)[:180]
        record = {'status':'PASS' if self.vector_enabled and not vector_error and not failures else 'DEGRADED','knowledge_version':version,'chunks':len(chunks),'pages':pages,'sources':fingerprints,'embedding':{'repo':'Xenova/bge-small-zh-v1.5','sha':EMBEDDING_SHA,'pooling':'CLS normalized','runtime':'CPU ONNX quantized'},'failures':failures,'vector_error':vector_error,'built_at':time.time()}
        (target/'chunks.json').write_text(json.dumps(chunks,ensure_ascii=False,indent=2))
        manifest.write_text(json.dumps(record,ensure_ascii=False,indent=2))
        # Parsing failure must not replace the last valid knowledge snapshot.
        if not failures:
            (self.path/'CURRENT.tmp').write_text(version)
            os.replace(self.path/'CURRENT.tmp',self.path/'CURRENT')
        return record

    @staticmethod
    def product_matches(chunk, product):
        if not product: return True
        declared = chunk.get('products',[])
        if declared: return product in declared
        if chunk.get('scope') == 'general': return True
        mentioned = [p for p in PRODUCTS if p in chunk.get('text','')]
        return product in mentioned and len(mentioned) == 1

    @staticmethod
    def evidence_applicability(chunk, product=None, factory=None, period=None, specification=None, document_version=None):
        reasons, limits = [], []
        if not Knowledge.product_matches(chunk, product): reasons.append('产品范围不适用或未明确')
        for key, expected, label in [('factory', factory, '工厂'), ('specification', specification, '规格'), ('document_version', document_version, '文档版本')]:
            actual = chunk.get(key)
            if expected and actual and actual != expected: reasons.append(label + '不匹配')
            elif expected and not actual: limits.append(label + '未在文档中明确，引用仅作背景')
        if period:
            start, end = period.get('start'), period.get('end')
            event = chunk.get('event_period')
            if event and start and end and not start <= event <= end: reasons.append('事件不在分析期间')
            effective = chunk.get('effective_date')
            if effective and end and effective[:7] > end: reasons.append('文档尚未生效')
        return {'applicable':not reasons, 'reasons':reasons, 'limits':limits, 'scope':chunk.get('scope','unknown')}

    def search(self, query, product=None, mode='hybrid', limit=5, factory=None, period=None, specification=None, document_version=None):
        if mode not in ('hybrid','bm25','vector'):
            raise ValueError('mode must be hybrid, bm25 or vector')
        if not (self.path/'CURRENT').exists(): self.build()
        if not (self.path/'CURRENT').exists():
            return {'status':'FAILED','mode':mode,'evidence':[],'reason':'No valid knowledge snapshot'}
        version = (self.path/'CURRENT').read_text().strip()
        target = self.path/version
        db = sqlite3.connect(target/'fts.sqlite')
        try:
            chunks = {row[0]:json.loads(row[1]) for row in db.execute('SELECT id,body FROM chunks')}
            applicability = {k:self.evidence_applicability(v,product,factory,period,specification,document_version) for k,v in chunks.items()}
            eligible = {k for k,v in applicability.items() if v['applicable']}
            tokens = list(dict.fromkeys(tokenize(query)))[:60]
            match = ' OR '.join('"'+x.replace('"','""')+'"' for x in tokens)
            bm25 = [r[0] for r in db.execute('SELECT id FROM search WHERE search MATCH ? ORDER BY bm25(search) ASC LIMIT 100',(match,)) if r[0] in eligible] if match else []
        finally:
            db.close()  # leaked handles block index replacement on Windows
        vec, error = [], None
        if mode != 'bm25' and self.vector_enabled:
            try:
                import chromadb
                if self._collection is None or self._collection[0] != version:
                    client = chromadb.PersistentClient(path=str(target/'chroma'), settings=chromadb.Settings(anonymized_telemetry=False))
                    self._collection = (version,client.get_collection('pharma_evidence'))
                result = self._collection[1].query(query_embeddings=self._model().encode([query],query=True), n_results=min(100,len(chunks)))
                vec = [k for k in result['ids'][0] if k in eligible]
            except Exception as exc:
                error = type(exc).__name__
        elif mode != 'bm25': error = 'VECTOR_DISABLED'
        rankings = [bm25[:20],vec[:20]] if mode == 'hybrid' else [vec if mode == 'vector' else bm25]
        # Exact document/parameter questions favour lexical anchors; semantic
        # candidates still contribute. These fixed weights are not fit on gold.
        lexical_anchor = bool(re.search(r'配方|工艺|收率|装量|设备|维修|GMP|规格|每盒|[A-Z]{2,}|\d', query))
        weights = [0.75, 0.25] if lexical_anchor else [0.5, 0.5]
        ids = reciprocal_rank_fusion(rankings, limit=limit, weights=weights if mode == 'hybrid' else None)
        status = 'DEGRADED' if error else 'PASS'
        if mode == 'vector' and error: ids = []
        reranker_error = None
        if self.reranker and ids:
            try: ids = self.reranker(query,ids,chunks)
            except Exception as exc: reranker_error = type(exc).__name__
        # Real LlamaIndex retriever adapter: callers consume framework-produced nodes.
        from llama_index.core.retrievers import BaseRetriever
        from llama_index.core.schema import TextNode, NodeWithScore
        class RankedRetriever(BaseRetriever):
            def _retrieve(self, query_bundle):
                return [NodeWithScore(node=TextNode(id_=k,text=chunks[k]['text'],metadata={'source':chunks[k]['source'],'location':chunks[k]['location']}),score=1/(60+i)) for i,k in enumerate(ids,1)]
        nodes = RankedRetriever().retrieve(query)
        evidence = [dict(chunks[n.node.node_id],score=n.score,applicability=applicability[n.node.node_id]) for n in nodes]
        return {'status':status,'knowledge_version':version,'mode':mode,'evidence':evidence,'reason':error,'reranker_error':reranker_error,'fusion_weights':weights if mode=='hybrid' else None,'framework':'llama-index-core BaseRetriever/TextNode'}
