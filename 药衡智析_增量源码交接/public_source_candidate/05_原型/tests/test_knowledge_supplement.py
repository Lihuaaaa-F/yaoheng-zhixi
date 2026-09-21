# -*- coding: utf-8 -*-
"""竞赛上下文补充知识（修复 #7）：行情/基准/异常记录/对标基线入库。

- 默认（竞赛）上下文：题包目录 + 补充知识目录合并进知识版本指纹与构建；
- 行业包（context / source_files 显式）：不追加，allowlist 语义不变；
- 补充文档可被 BM25 检索命中并携带来源文件名。
"""
from pathlib import Path

from pharma.knowledge import Knowledge

PKG_REL = Path('00_赛题原始资料/模拟数据_V1.1_净化解压/创灵境_考题模拟数据/03_制药知识文档')


def _make_env(tmp_path):
    pkg_dir = tmp_path / PKG_REL
    pkg_dir.mkdir(parents=True)
    (pkg_dir / '配方A.txt').write_text('产品配方：山茱萸用量与提取工艺要求。投料记录须与批生产记录一致。', encoding='utf-8')
    sup = tmp_path / 'supplement'
    sup.mkdir()
    (sup / '行情_行业知识.txt').write_text(
        '山茱萸（统货,陕西产，元/kg）市场价：5月56.0、6月54.5；安国中药材市场。库存偏低推动上涨。市场参考价非采购价。', encoding='utf-8')
    return sup


def test_supplement_included_in_default_context_build(tmp_path, monkeypatch):
    sup = _make_env(tmp_path)
    monkeypatch.setattr('pharma.config.KNOWLEDGE_SUPPLEMENT_DIR', sup)
    k = Knowledge(root=tmp_path, vector_enabled=False)
    assert k.extra_dir == sup
    manifest = k.build()
    raw = manifest['sources']
    names = set(raw) if isinstance(raw, dict) else \
        {s['file'] if isinstance(s, dict) else s for s in raw}
    assert any('行情' in str(n) for n in names)
    assert any('配方A' in str(n) for n in names)


def test_supplement_searchable_with_source(tmp_path, monkeypatch):
    sup = _make_env(tmp_path)
    monkeypatch.setattr('pharma.config.KNOWLEDGE_SUPPLEMENT_DIR', sup)
    k = Knowledge(root=tmp_path, vector_enabled=False)
    k.build()
    results = k.search('山茱萸 市场价 库存', mode='bm25', limit=5)
    assert results['status'] in ('PASS', 'HYBRID_REAL', 'FULL')
    hit_files = {r.get('source_file', r.get('source')) for r in results['evidence']}
    assert any('行情' in str(f) for f in hit_files if f)


def test_explicit_source_dir_or_files_isolate_supplement(tmp_path, monkeypatch):
    sup = _make_env(tmp_path)
    monkeypatch.setattr('pharma.config.KNOWLEDGE_SUPPLEMENT_DIR', sup)
    pkg_dir = tmp_path / PKG_REL
    via_dir = Knowledge(root=tmp_path, vector_enabled=False, source_dir=pkg_dir)
    assert via_dir.extra_dir is None
    via_files = Knowledge(root=tmp_path, vector_enabled=False,
                          context={'industry_id': 'mechanical'}, source_files=(pkg_dir / '配方A.txt',))
    assert via_files.extra_dir is None
