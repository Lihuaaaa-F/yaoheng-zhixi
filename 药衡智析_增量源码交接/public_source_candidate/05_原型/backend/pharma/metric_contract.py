"""共用指标合同：制药与通用两条计算路径的快照必须满足同一角色契约。

这是消除重复口径维护风险的第一步（不做一次性重写）：
- 共同部分（change/contribution/threshold_alert/_months/_shift）已由
  metrics.py 单点提供，industry.py 复用；
- 本合同把两条路径产出快照的共有结构锁住：核心指标键集合、单位与公式
  字段必填、比较类指标单位为百分比、N/A 必须携带原因、口径字段一致。
  任何一侧的改动破坏合同都会在 tests/test_metric_contract.py 暴露，
  从而防止“同一公式修复后不同路径表现不一致”。
"""
from typing import Any

CONTRACT_VERSION = 'metric-contract-v1-core-roles'
CORE_METRICS = ('total_cost', 'quantity', 'unit_cost')
COMPARISON_METRICS = ('mom', 'yoy', 'budget')
PERCENT_UNIT = '%'


def validate_snapshot(snapshot: dict[str, Any]) -> list[str]:
    """返回合同违规列表；空列表表示两条路径共有的指标合同成立。"""
    errors: list[str] = []
    metrics = snapshot.get('metrics') or {}
    for key in CORE_METRICS:
        item = metrics.get(key)
        if not isinstance(item, dict):
            errors.append(f'core metric missing: {key}')
            continue
        if not item.get('unit'):
            errors.append(f'{key}: unit empty')
        if not item.get('formula'):
            errors.append(f'{key}: formula missing')
        if item.get('value') is None and not item.get('reason'):
            errors.append(f'{key}: N/A value without reason')
    for key in COMPARISON_METRICS:
        item = metrics.get(key)
        if not isinstance(item, dict):
            errors.append(f'comparison metric missing: {key}')
            continue
        if item.get('value') is not None and item.get('unit') != PERCENT_UNIT:
            errors.append(f'{key}: comparison unit must be {PERCENT_UNIT}, got {item.get("unit")}')
        if item.get('value') is None and not item.get('reason'):
            errors.append(f'{key}: N/A comparison without reason')
    # 口径一致：basis 声明与核心指标口径字段不冲突。
    basis = snapshot.get('basis')
    if basis is not None and basis not in ('unit', 'total'):
        errors.append(f'basis must be unit/total, got {basis}')
    # 元素告警的阈值口径：basis 必为 unit/total（合成演示阈值 ±10%）。
    for alert in snapshot.get('alerts') or []:
        if alert.get('basis') not in ('unit', 'total'):
            errors.append(f'alert {alert.get("alert_id")}: basis missing')
        if alert.get('rate') is None:
            errors.append(f'alert {alert.get("alert_id")}: rate missing')
    return errors
