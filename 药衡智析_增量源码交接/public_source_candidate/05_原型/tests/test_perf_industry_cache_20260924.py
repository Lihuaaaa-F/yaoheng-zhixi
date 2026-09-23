"""catalog 缓存守卫（2026-09-24 审查 SSE-11）：缓存命中与指纹失效，全部合成对象，不碰赛题字节。

实测背景：context_catalog 未缓存 45-61ms/请求（pydantic 全量校验为主），属每请求固定开销。
"""
import json
import os

from pharma import industry


def _canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False)


def test_context_catalog_stable_across_calls():
    a, b = industry.context_catalog(), industry.context_catalog()
    assert _canon(a) == _canon(b)
    assert a['contexts'] and a['default_context_id']


def test_dataset_cache_hits_and_invalidates_on_fingerprint_change(monkeypatch, tmp_path):
    cfg = tmp_path / 'config.json'
    facts = tmp_path / 'facts.json'
    cfg.write_text('{}', encoding='utf-8')
    facts.write_text('{}', encoding='utf-8')
    ent = {'_config_file': cfg, '_base_dir': tmp_path, 'facts_entry': 'facts.json'}
    calls = []
    monkeypatch.setattr(industry, '_read_dataset_uncached', lambda p, e: calls.append(1) or 'DATASET')

    r1 = industry._read_dataset(None, ent)
    r2 = industry._read_dataset(None, ent)
    assert r1 == 'DATASET' and r2 == 'DATASET' and len(calls) == 1, '同指纹第二次调用必须命中缓存'

    facts.write_text('{}', encoding='utf-8')  # 重写使 mtime_ns 前进
    st = facts.stat()
    os.utime(facts, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000))
    industry._read_dataset(None, ent)
    assert len(calls) == 2, 'facts 文件指纹变化后缓存必须失效重算'


def test_soffice_available_is_memoized(monkeypatch):
    monkeypatch.setattr(industry, '_SOFFICE_AVAILABLE', None)
    probes = []
    import pharma.reports as reports
    real = reports.soffice_exe
    monkeypatch.setattr(reports, 'soffice_exe', lambda: probes.append(1) or 'soffice')
    assert industry._soffice_available() is True
    assert industry._soffice_available() is True
    assert len(probes) == 1, 'soffice 探测应进程级 memo，不随请求重复扫 PATH'
    monkeypatch.setattr(reports, 'soffice_exe', real)
