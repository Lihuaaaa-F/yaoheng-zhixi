# -*- coding: utf-8 -*-
"""二厂合成明细覆盖目录回归（2026-09-21 修复 #19）。

- 默认启用：ingest 的 manifest 含 synthetic 标注文件，audit 全通过；
  analyze(中药二厂) 明细可用并携带 data_label；对标 details 的二厂侧带标注。
- PHARMA_SYNTHETIC_DETAIL_DIR 置空可完全停用，回到纯题包口径（二厂无明细）。
"""
import importlib


def _reload_config():
    import pharma.config as config
    return importlib.reload(config)


def test_ingest_manifest_marks_synthetic_files(tmp_path, monkeypatch):
    monkeypatch.setenv('PHARMA_RUNTIME_DIR', str(tmp_path / 'runtime'))
    config = _reload_config()
    try:
        from pharma import ingestion
        importlib.reload(ingestion)
        manifest = ingestion.ingest(destination=tmp_path / 'snap')
        assert manifest['status'] == 'VALID'
        synthetic = [f for f in manifest['files'] if f.get('synthetic')]
        assert len(synthetic) == 3
        assert all(f['path'].startswith('合成明细/') for f in synthetic)
        assert all('合成' in f['path'] for f in synthetic)
    finally:
        monkeypatch.delenv('PHARMA_RUNTIME_DIR')
        importlib.reload(config)


def test_plant2_details_available_and_labeled():
    from pharma.metrics import analyze
    snapshot = analyze('中药二厂', '六味地黄胶囊', '2026-06')
    details = snapshot['details']
    assert details['available'] is True
    assert len(details['materials']) > 0 and len(details['expenses']) > 0
    assert '合成演示数据' in details.get('data_label', '')
    plant1 = analyze('中药一厂', '六味地黄胶囊', '2026-06')
    assert plant1['details']['available'] is True
    assert 'data_label' not in plant1['details']


def test_benchmark_details_carry_synthetic_label():
    from pharma.metrics import benchmark_analysis
    _, comparison = benchmark_analysis('六味地黄胶囊', '2026-06')
    labeled_sides = [side for side in ('left', 'right')
                     if comparison['details'][side].get('data_label')]
    assert labeled_sides, '二厂侧应携带合成数据标注'


def test_disable_overlay_returns_to_package_only(tmp_path, monkeypatch):
    monkeypatch.setenv('PHARMA_SYNTHETIC_DETAIL_DIR', '')
    monkeypatch.setenv('PHARMA_RUNTIME_DIR', str(tmp_path / 'runtime2'))
    config = _reload_config()
    try:
        assert config.SYNTHETIC_DETAIL_DIR is None
        from pharma.metrics import analyze
        snapshot = analyze('中药二厂', '六味地黄胶囊', '2026-06')
        assert snapshot['details']['available'] is False
    finally:
        monkeypatch.delenv('PHARMA_SYNTHETIC_DETAIL_DIR')
        monkeypatch.delenv('PHARMA_RUNTIME_DIR')
        importlib.reload(config)
