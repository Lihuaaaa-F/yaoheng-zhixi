"""性能合同（2026-09-23 审查 SSE-5）：benchmark_analysis 每厂只允许 analyze 一次。

同输入 analyze 确定性等价，重复计算纯属浪费（对标接口与每份报告都走此路径）。
"""
from pharma import metrics


def test_benchmark_analysis_analyzes_each_factory_exactly_once(monkeypatch):
    calls = []
    orig = metrics.analyze

    def counting(*a, **k):
        calls.append(a)
        return orig(*a, **k)

    monkeypatch.setattr(metrics, 'analyze', counting)
    snapshot, comparison = metrics.benchmark_analysis('六味地黄胶囊', '2026-06')
    assert len(calls) == 2, f'benchmark_analysis 触发了 {len(calls)} 次 analyze，应为左右厂各 1 次'
