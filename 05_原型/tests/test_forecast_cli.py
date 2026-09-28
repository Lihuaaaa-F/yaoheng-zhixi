"""独立交付入口：状态复现、无未来数据泄漏和不完整历史。"""
import csv
import json
from pathlib import Path
import subprocess
import sys

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/forecast_cli.py'


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)


def source(tmp_path, values, months=None):
    path = tmp_path / 'history.csv'
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(['工厂', '产品名称', '月份', '单位成本(元/盒)', '直接材料(元/盒)',
                         '直接人工(元/盒)', '制造费用(元/盒)', '总成本(元)'])
        for i, value in enumerate(values):
            writer.writerow(['测试厂', '测试产品', (months or [f'2026-{m:02d}' for m in range(1, 7)])[i],
                             value, value, value, value, value])
    return path


def test_state_roundtrip_and_prefix_only_holdout(tmp_path):
    path = source(tmp_path, [10, 11, 12, 13, 14, 1000])
    state, first, second = [tmp_path / name for name in ('state.json', 'first.json', 'second.json')]
    result = run('--input', path, '--state-out', state, '--output', first)
    assert result.returncode == 0, result.stderr
    assert run('--state-in', state, '--output', second).returncode == 0
    assert first.read_bytes() == second.read_bytes()
    evaluation = json.loads(first.read_text())['results'][0]['rolling_evaluation']
    assert evaluation['origins'] == 3
    # The final spike is held out; it cannot contaminate any prediction made before it.
    assert [x['prediction'] for x in evaluation['checks']] == [13, 14, 15]
    assert evaluation['checks'][-1]['train_end'] == '2026-05'


def test_missing_month_does_not_create_predictions(tmp_path):
    path = source(tmp_path, [10, 11, 13], ['2026-01', '2026-02', '2026-04'])
    output = tmp_path / 'out.json'
    assert run('--input', path, '--output', output).returncode == 0
    row = json.loads(output.read_text())['results'][0]
    assert row['forecast']['status'] == 'INSUFFICIENT_HISTORY'
    assert row['forecast']['points'] == []
    assert row['rolling_evaluation'] is None


def test_duplicate_month_and_incompatible_state_fail(tmp_path):
    path = source(tmp_path, [10, 11, 12], ['2026-01', '2026-01', '2026-02'])
    output = tmp_path / 'out.json'
    result = run('--input', path, '--output', output)
    assert result.returncode == 2
    assert 'DUPLICATE_FORECAST_MONTH' in result.stderr
    state = tmp_path / 'state.json'
    state.write_text('{"schema_version": 999}')
    assert run('--state-in', state, '--output', output).returncode == 2
    assert not output.exists()
