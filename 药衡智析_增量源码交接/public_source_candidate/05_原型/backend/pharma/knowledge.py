"""版本化本地检索：文档是不可信证据，绝不当作指令执行。
Versioned local retrieval. Documents are untrusted evidence, never instructions.

检索栈：jieba 分词 + SQLite FTS5（BM25）与 Chroma 向量（bge-large-zh ONNX 量化）
双路召回，RRF 融合排序；候选先过产品/工厂/期间/规格/文档版本适用性过滤，
再进入排名。切分保留标题继承与维修事件行隔离，版本指纹绑定词表与源文件。
"""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import os
import re
import sqlite3
import time
from .config import ROOT, PACKAGE, RUNTIME

EMBEDDING_SHA = 'a48549b3259a6165364f226599cd91f39923d5d5'
PARSER_VERSION = 'scope-prefilter-v7-private-terminology'
RETRIEVER_VERSION = 'bm25-chroma-prefilter-rrf-v5-keyword-expansion'
def _string_list(value, label):
    if not isinstance(value,list) or any(not isinstance(x,str) or not x.strip() or len(x)>200 for x in value) or len(value)!=len(set(value)):
        raise ValueError('INVALID_TERMINOLOGY_'+label)
    return value


def pharmaceutical_terminology():
    """Only the explicit local JSON file may override public synthetic terms."""
    from .config import APP
    # 与主数据同源：默认解析仓库内赛题术语文件，部署不依赖外部绝对路径。
    configured=os.getenv('PHARMA_PRIVATE_TERMINOLOGY_FILE') or ''
    if not configured:
        competition=Path(os.environ.get('PHARMA_COMPETITION_CONFIG_DIR',str(APP.parent/'competition_configuration')))
        default=competition/'pharmaceutical_terminology_original.json'
        configured=str(default) if default.is_file() else ''
    path=Path(configured) if configured else APP/'industry_packs/pharmaceutical/terminology.json'
    if path.suffix.lower()!='.json' or path.stat().st_size>1_000_000:raise ValueError('INVALID_TERMINOLOGY_FILE')
    value=json.loads(path.read_text(encoding='utf-8'))
    keys={'products','product_aliases','equipment_aliases','tokenizer_terms'}
    if not isinstance(value,dict) or set(value)!=keys:raise ValueError('INVALID_TERMINOLOGY_SHAPE')
    products=_string_list(value['products'],'PRODUCTS')
    _string_list(value['tokenizer_terms'],'TOKENIZER')
    for key in ('product_aliases','equipment_aliases'):
        aliases=value[key]
        if not isinstance(aliases,dict) or not set(aliases).issubset(products):raise ValueError('INVALID_TERMINOLOGY_MAPPING')
        for words in aliases.values():_string_list(words,key)
    return value


def terminology_hash():
    return hashlib.sha256(json.dumps(pharmaceutical_terminology(),sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()


@lru_cache(maxsize=8)
def _term_tokenizer(words):
    import jieba
    tokenizer=jieba.Tokenizer()
    for word in words:tokenizer.add_word(word)
    return tokenizer


def source_snapshot(source_dir):
    files = sorted(p for p in Path(source_dir).iterdir() if p.suffix.lower() in ('.pdf','.docx','.txt'))
    fingerprints = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    return hashlib.sha256(json.dumps({'sources':fingerprints,'terminology_hash':terminology_hash()},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def reciprocal_rank_fusion(rankings, limit=5, k=60, weights=None):
    scores = {}
    for index, ranking in enumerate(rankings):
        for rank, item in enumerate(dict.fromkeys(ranking), 1):
            scores[item] = scores.get(item, 0) + (weights[index] if weights else 1) / (k + rank)
    return sorted(scores, key=lambda x: (-scores[x], x))[:limit]


def tokenize(text):
    tokenizer=_term_tokenizer(tuple(pharmaceutical_terminology()['tokenizer_terms']))
    return [x.lower() for x in tokenizer.cut(text) if re.search(r'[\w\u4e00-\u9fff]', x)]


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
    elif suffix == '.json':
        records = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(records,list): raise ValueError('knowledge records must be a list')
        for i, record in enumerate(records,1):
            if not isinstance(record,dict) or not isinstance(record.get('text'),str): raise ValueError('invalid knowledge record')
            yield {**record,'page':None,'location':record.get('location',f'记录{i}'),'original_text':record['text'],'scope':record.get('scope','product' if record.get('products') else 'general')}
    elif suffix == '.txt':
        lines = path.read_text(encoding='utf-8-sig').splitlines()
        for i in range(0, len(lines), 12):
            yield {'page': None, 'location': f'行{i+1}-{min(i+12,len(lines))}', 'original_text': '\n'.join(lines[i:i+12])}


def section_blocks(path, industry_id=None):
    """Inherit explicit headings across pages, and isolate dated maintenance rows."""
    if path.suffix.lower() == '.json' or industry_id not in (None,'pharmaceutical'):
        yield from parse_document(path)
        return
    terminology=pharmaceutical_terminology()
    aliases_by_product=terminology['product_aliases']
    products = [p for p in terminology['products'] if p in path.name]
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
                declared = [p for p, aliases in aliases_by_product.items() if any(a in heading for a in aliases)]
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
                    event_products = [p for p,aliases in aliases_by_product.items() if any(a in compact for a in aliases)]
                    event_scope = 'product' if event_products else 'unknown'
                yield dict(block, **metadata, original_text=event, heading=heading, products=event_products,
                           scope=event_scope, event_period=f'{period[1]}-{period[2]}' if period else None)


class Knowledge:
    def __init__(self, root=None, vector_enabled=True, source_dir=None, reranker=None, context=None, reranker_version=None, source_files=None):
        self.root = Path(root) if root else ROOT
        runtime = self.root / '05_原型/.runtime' if root is not None else RUNTIME
        package = self.root / '00_赛题原始资料/模拟数据_V1.1_净化解压/创灵境_考题模拟数据' if root is not None else PACKAGE
        self.context = context.model_dump() if hasattr(context, 'model_dump') else dict(context or {})
        if isinstance(source_files,(str,Path)): raise ValueError('SOURCE_FILES_MUST_BE_SEQUENCE')
        self.source_files = tuple(Path(p).resolve() for p in source_files) if source_files is not None else None
        if self.source_files is not None:
            if not self.source_files: raise ValueError('EMPTY_EXPLICIT_SOURCE_FILES')
            if any(p.suffix.lower() not in ('.pdf','.docx','.txt','.json') for p in self.source_files): raise ValueError('UNSUPPORTED_EXPLICIT_SOURCE_FILE')
            if len({p.name for p in self.source_files}) != len(self.source_files): raise ValueError('DUPLICATE_SOURCE_FILENAME')
        namespace_inputs = {'context':self.context,'source_files':[str(p) for p in self.source_files]} if self.source_files is not None else self.context
        namespace = hashlib.sha256(json.dumps(namespace_inputs, sort_keys=True).encode()).hexdigest()[:24] if namespace_inputs else None
        self.path = runtime / 'knowledge'
        if namespace: self.path = self.path / namespace
        self.path.mkdir(parents=True, exist_ok=True)
        self.source_dir = Path(source_dir) if source_dir else package / '03_制药知识文档'
        # 竞赛上下文补充知识（2026-09-21 修复 #7）：默认上下文（题包制药）追加
        # 仓库自有的补充知识目录——行情/基准题包 CSV 转知识文本、异常处理记录与
        # 对标基线补建。行业包（context/source_files 显式指定）不追加，allowlist
        # 语义不变；文件哈希计入知识版本指纹，增删改自动重建。
        from .config import KNOWLEDGE_SUPPLEMENT_DIR
        self.extra_dir = None
        self.ingest_dir = None
        if not self.context and self.source_files is None and source_dir is None:
            supplement = Path(KNOWLEDGE_SUPPLEMENT_DIR)
            if supplement.is_dir():
                self.extra_dir = supplement
            # 数据中心“知识库数据”用户上传的资料落库目录（2026-09-22 三模块改版）：
            # 与补充目录同语义，仅默认上下文追加；文件哈希进入版本指纹。
            ingest = RUNTIME / 'imports' / 'knowledge'
            if ingest.is_dir():
                self.ingest_dir = ingest
        # 向量模型目录：环境变量 → 模型设置文件（向量模型“确认”切换后写入）→ 默认。
        from . import model_settings as _model_settings
        self.model_dir = _model_settings.embedding_dir()
        self.vector_enabled = vector_enabled
        if reranker and not reranker_version: raise ValueError('RERANKER_VERSION_REQUIRED')
        self.reranker_version = reranker_version
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

    def build(self, progress=None):
        from .locks import exclusive
        with exclusive(self.path / 'build.lock'):
            return self._build(progress)

    def _build(self, progress=None):
        def _report(pct, detail):
            if progress is not None:
                try: progress(int(pct), detail)
                except Exception: pass  # 进度回调绝不影响构建本身
        # An explicit enterprise entry is an allowlist, never a hint to scan its
        # parent. Directory mode remains for the private competition document set.
        sources = sorted(self.source_files) if self.source_files is not None else sorted(p for p in self.source_dir.iterdir() if p.suffix.lower() in ('.pdf','.docx','.txt') or p.name == 'knowledge.json')
        if self.source_files is None:
            if self.extra_dir is not None:
                sources = sources + sorted(p for p in self.extra_dir.iterdir()
                                           if p.suffix.lower() in ('.pdf','.docx','.txt') and p.is_file())
            if self.ingest_dir is not None:
                sources = sources + sorted(p for p in self.ingest_dir.iterdir()
                                           if p.suffix.lower() == '.txt' and p.is_file())
        from . import model_settings as _model_settings
        embedding_sha = _model_settings.embedding_fingerprint(self.model_dir)
        _report(5, f'读取知识源（{len(sources)} 份）…')
        fingerprints = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
        terms_hash=terminology_hash()
        version = hashlib.sha256(json.dumps([fingerprints, embedding_sha, PARSER_VERSION, self.context, terms_hash], sort_keys=True).encode()).hexdigest()[:20]
        target = self.path / version
        manifest = target / 'manifest.json'
        if manifest.exists():
            record = json.loads(manifest.read_text())
            if record['status'] == 'PASS' or (not self.vector_enabled and not record.get('failures')):
                (self.path/'CURRENT.tmp').write_text(version)
                os.replace(self.path/'CURRENT.tmp',self.path/'CURRENT')
                _report(100, '知识索引已是最新版本，直接切换')
                return record
        target.mkdir(exist_ok=True)
        chunks, failures, pages = [], [], 0
        for index, source in enumerate(sources):
            _report(8 + 20 * index / max(len(sources), 1), f'解析文档 {index + 1}/{len(sources)}：{source.name}')
            try:
                source_pages = set()
                for block in section_blocks(source,self.context.get('industry_id')):
                    if self.context and any(block.get(k) and block[k] != self.context.get(k) for k in ('enterprise_id','industry_id')):
                        continue
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
                        chunks.append(dict(block, evidence_id=ident, source=source.name, hash=fingerprints[source.name], text=text, chunk=index, knowledge_version=version, analysis_context=self.context))
                        if end == len(clean): break
                        start, index = max(start+1,end-80), index+1
                pages += len(source_pages)
            except Exception as exc:
                failures.append({'source':source.name,'reason':type(exc).__name__})
        if not chunks:
            return {'status':'FAILED','failures':failures,'knowledge_version':version}
        _report(28, f'文档解析完成（{len(chunks)} 个知识分块），建立词法索引…')
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
        _report(45, '词法索引（BM25）完成，开始向量索引…')
        vector_error = None
        if self.vector_enabled:
            try:
                import chromadb
                client = chromadb.PersistentClient(path=str(target/'chroma'), settings=chromadb.Settings(anonymized_telemetry=False))
                collection = client.get_or_create_collection('pharma_evidence',metadata={'hnsw:space':'cosine'})
                texts=[c['text'] for c in chunks]; ids=[c['evidence_id'] for c in chunks]
                documents=texts; metadatas=[{'evidence_id':c['evidence_id']} for c in chunks]
                batch=32
                for offset in range(0,len(texts),batch):
                    sl=slice(offset,min(offset+batch,len(texts)))
                    vectors=self._model().encode(texts[sl])
                    collection.upsert(ids=ids[sl],embeddings=vectors,documents=documents[sl],metadatas=metadatas[sl])
                    _report(45+40*(offset+batch)/max(len(texts),1), f'向量化 {min(offset+batch,len(texts))}/{len(texts)} 段')
            except Exception as exc:
                vector_error = type(exc).__name__ + ': ' + str(exc)[:180]
        _report(90, '索引构建完成，写入清单并验证…')
        record = {'terminology_hash':terms_hash,'status':'PASS' if self.vector_enabled and not vector_error and not failures else 'DEGRADED','knowledge_version':version,'chunks':len(chunks),'pages':pages,'sources':fingerprints,'embedding':{'repo':self.model_dir.name,'path':str(self.model_dir),'sha':embedding_sha,'pooling':'CLS normalized','runtime':'CPU ONNX quantized' if self.model_dir.is_dir() else 'unknown'},'failures':failures,'vector_error':vector_error,'built_at':time.time()}
        (target/'chunks.json').write_text(json.dumps(chunks,ensure_ascii=False,indent=2))
        manifest.write_text(json.dumps(record,ensure_ascii=False,indent=2))
        # Parsing failure must not replace the last valid knowledge snapshot.
        if terminology_hash()!=terms_hash:raise ValueError('TERMINOLOGY_CHANGED_DURING_BUILD')
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
        if chunk.get('analysis_context',{}).get('industry_id') not in (None,'pharmaceutical'): return False
        mentioned = [p for p in pharmaceutical_terminology()['products'] if p in chunk.get('text','')]
        return product in mentioned and len(mentioned) == 1

    @staticmethod
    def evidence_applicability(chunk, product=None, factory=None, period=None, specification=None, document_version=None, context=None):
        reasons, limits = [], []
        if context:
            expected_context = context.model_dump() if hasattr(context, 'model_dump') else context
            actual_context = chunk.get('analysis_context') or {}
            for key in ('enterprise_id','industry_id','industry_version','dataset_id','knowledge_snapshot'):
                if expected_context.get(key) and actual_context.get(key) != expected_context[key]:
                    reasons.append('分析上下文不匹配:' + key)
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

    def search(self, query, product=None, mode='hybrid', limit=5, factory=None, period=None, specification=None, document_version=None, context=None, event_only=False, keyword_query=None):
        if context is not None and dict(context) != self.context:
            raise ValueError('KNOWLEDGE_CONTEXT_MISMATCH')
        if mode not in ('hybrid','bm25','vector'):
            raise ValueError('mode must be hybrid, bm25 or vector')
        if (self.path/'CURRENT').exists() and self.status().get('terminology_hash')!=terminology_hash():self.build()
        if not (self.path/'CURRENT').exists(): self.build()
        if not (self.path/'CURRENT').exists():
            return {'status':'FAILED','mode':mode,'evidence':[],'reason':'No valid knowledge snapshot'}
        if self.status().get('terminology_hash')!=terminology_hash():raise ValueError('TERMINOLOGY_REBUILD_FAILED')
        version = (self.path/'CURRENT').read_text().strip()
        target = self.path/version
        db = sqlite3.connect(target/'fts.sqlite')
        try:
            chunks = {row[0]:json.loads(row[1]) for row in db.execute('SELECT id,body FROM chunks')}
            applicability = {k:self.evidence_applicability(v,product,factory,period,specification,document_version,context=self.context) for k,v in chunks.items()}
            eligible = {k for k,v in applicability.items() if v['applicable']}
            if event_only:
                # Purpose retrieval still applies all normal scope checks, then
                # restricts candidates before either BM25 or vector ranking.
                eligible = {k for k in eligible if period and period.get('start') and period.get('end') and chunks[k].get('event_period')}
            tokens = list(dict.fromkeys(tokenize(query if keyword_query is None else keyword_query)))[:60]
            match = ' OR '.join('"'+x.replace('"','""')+'"' for x in tokens)
            db.execute('CREATE TEMP TABLE eligible(id TEXT PRIMARY KEY)')
            db.executemany('INSERT INTO eligible VALUES (?)',[(k,) for k in eligible])
            bm25 = [r[0] for r in db.execute('SELECT id FROM search WHERE search MATCH ? AND id IN (SELECT id FROM eligible) ORDER BY bm25(search) ASC LIMIT ?', (match, max(20,limit)))] if match and eligible else []
        finally:
            db.close()  # leaked handles block index replacement on Windows
        vec, error = [], None
        if mode != 'bm25' and self.vector_enabled and eligible:
            try:
                import chromadb
                if self._collection is None or self._collection[0] != version:
                    client = chromadb.PersistentClient(path=str(target/'chroma'), settings=chromadb.Settings(anonymized_telemetry=False))
                    self._collection = (version,client.get_collection('pharma_evidence'))
                result = self._collection[1].query(query_embeddings=self._model().encode([query],query=True), n_results=min(max(20,limit),len(eligible)), where={'evidence_id':{'$in':sorted(eligible)}})
                vec = [k for k in result['ids'][0] if k in eligible]
            except Exception as exc:
                error = type(exc).__name__
        elif mode != 'bm25' and not self.vector_enabled: error = 'VECTOR_DISABLED'
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
            try:
                reranked = self.reranker(query,ids,chunks)
                if any(k not in eligible or k not in ids for k in reranked): raise ValueError('RERANKER_OUT_OF_SCOPE')
                ids = list(dict.fromkeys(reranked))[:limit]
            except Exception as exc: reranker_error = type(exc).__name__
        # Real LlamaIndex retriever adapter: callers consume framework-produced nodes.
        from llama_index.core.retrievers import BaseRetriever
        from llama_index.core.schema import TextNode, NodeWithScore
        class RankedRetriever(BaseRetriever):
            def _retrieve(self, query_bundle):
                return [NodeWithScore(node=TextNode(id_=k,text=chunks[k]['text'],metadata={'source':chunks[k]['source'],'location':chunks[k]['location']}),score=1/(60+i)) for i,k in enumerate(ids,1)]
        nodes = RankedRetriever().retrieve(query)
        evidence = [dict(chunks[n.node.node_id],score=n.score,applicability=applicability[n.node.node_id]) for n in nodes]
        return {'status':status,'knowledge_version':version,'mode':mode,'evidence':evidence,'reason':error,'reranker_error':reranker_error,'fusion_weights':weights if mode=='hybrid' else None,'framework':'llama-index-core BaseRetriever/TextNode','retrieval_status':'EXECUTED' if not error else 'DEGRADED','recall_status':'RECALLED' if evidence else 'NO_MATCH' if eligible else 'NO_APPLICABLE_CANDIDATES','eligible_count':len(eligible),'retriever_version':RETRIEVER_VERSION,'reranker_version':self.reranker_version,'embedding_version':EMBEDDING_SHA,'analysis_context':self.context}
