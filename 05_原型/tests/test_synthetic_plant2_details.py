# -*- coding: utf-8 -*-
"""二厂合成明细覆盖目录回归（2026-09-21 修复 #19；2026-09-22 三模块改版默认停用）。

- 默认停用：未设置 PHARMA_SYNTHETIC_DETAIL_DIR 时回到纯题包口径（二厂无明细，
  对标以“证据支持假设”输出归因推测，不再出现合成演示数据）。
- 显式启用（评测对照）：设置 PHARMA_SYNTHETIC_DETAIL_DIR 后 ingest 的 manifest
  含 synthetic 标注文件；analyze(中药二厂) 明细可用并携带 data_label；对标
  details 的二厂侧带标注。
"""
import importlib
from pathlib import Path


def _synthetic_dir() -> str:
    root = Path(__file__).resolve().parents[2]
    return str(root / 'competition_configuration' / 'synthetic_detail_中药二厂')


def _reload_config():
    import pharma.config as config
    return importlib.reload(config)


def test_default_off_returns_to_package_only(tmp_path, monkeypatch):
    monkeypatch.delenv('PHARMA_SYNTHETIC_DETAIL_DIR', raising=False)
    monkeypatch.setenv('PHARMA_RUNTIME_DIR', str(tmp_path / 'runtime-default'))
    config = _reload_config()
    try:
        assert config.SYNTHETIC_DETAIL_DIR is None and config.SYNTHETIC_DETAIL_FACTORIES == set()
        from pharma.metrics import analyze, benchmark_analysis
        snapshot = analyze('中药二厂', '六味地黄胶囊', '2026-06')
        assert snapshot['details']['available'] is False
        _, comparison = benchmark_analysis('六味地黄胶囊', '2026-06')
        labeled = [side for side in ('left', 'right') if comparison['details'][side].get('data_label')]
        assert not labeled, '默认停用合成明细后，任何一侧都不应携带合成标注'
        assert '仅到要素层' in comparison['hypotheses'][0]['hypothesis']
    finally:
        monkeypatch.delenv('PHARMA_RUNTIME_DIR')
        importlib.reload(config)


def test_ingest_manifest_marks_synthetic_files(tmp_path, monkeypatch):
    monkeypatch.setenv('PHARMA_SYNTHETIC_DETAIL_DIR', _synthetic_dir())
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
        monkeypatch.delenv('PHARMA_SYNTHETIC_DETAIL_DIR')
        monkeypatch.delenv('PHARMA_RUNTIME_DIR')
        importlib.reload(config)


def test_plant2_details_available_and_labeled(tmp_path, monkeypatch):
    monkeypatch.setenv('PHARMA_SYNTHETIC_DETAIL_DIR', _synthetic_dir())
    monkeypatch.setenv('PHARMA_RUNTIME_DIR', str(tmp_path / 'runtime3'))
    config = _reload_config()
    try:
        from pharma.metrics import analyze
        snapshot = analyze('中药二厂', '六味地黄胶囊', '2026-06')
        details = snapshot['details']
        assert details['available'] is True
        assert len(details['materials']) > 0 and len(details['expenses']) > 0
        assert '合成演示数据' in details.get('data_label', '')
        plant1 = analyze('中药一厂', '六味地黄胶囊', '2026-06')
        assert plant1['details']['available'] is True
        assert 'data_label' not in plant1['details']
    finally:
        monkeypatch.delenv('PHARMA_SYNTHETIC_DETAIL_DIR')
        monkeypatch.delenv('PHARMA_RUNTIME_DIR')
        importlib.reload(config)


def test_benchmark_details_carry_synthetic_label(tmp_path, monkeypatch):
    monkeypatch.setenv('PHARMA_SYNTHETIC_DETAIL_DIR', _synthetic_dir())
    monkeypatch.setenv('PHARMA_RUNTIME_DIR', str(tmp_path / 'runtime4'))
    config = _reload_config()
    try:
        from pharma.metrics import benchmark_analysis
        _, comparison = benchmark_analysis('六味地黄胶囊', '2026-06')
        labeled_sides = [side for side in ('left', 'right')
                         if comparison['details'][side].get('data_label')]
        assert labeled_sides, '二厂侧应携带合成数据标注'
    finally:
        monkeypatch.delenv('PHARMA_SYNTHETIC_DETAIL_DIR')
        monkeypatch.delenv('PHARMA_RUNTIME_DIR')
        importlib.reload(config)
