"""成本预测（赛题加分项）：确定性时序外推的合同测试。"""
import pytest
from pharma import forecasting


def test_linear_series_forecast_is_deterministic():
    series=[('2026-01',10.0),('2026-02',11.0),('2026-03',12.0),('2026-04',13.0)]
    first=forecasting.forecast_series(series,horizon=2)
    second=forecasting.forecast_series(series,horizon=2)
    assert first==second and first['status']=='PASS'
    # 精确线性序列应保持斜率，每月增加 1
    assert first['points'][0]['month']=='2026-05'
    assert first['points'][0]['point']==pytest.approx(14.0,abs=1e-3)
    assert first['points'][1]['month']=='2026-06'
    assert first['points'][0]['low']==first['points'][0]['point']==first['points'][0]['high']
    assert '实验性' in first['interval'] and '80%' not in first['interval']


def test_flat_series_has_zero_interval_and_exact_point():
    result=forecasting.forecast_series([('2026-01',5),('2026-02',5),('2026-03',5),('2026-04',5)],horizon=3)
    assert result['status']=='PASS'
    for p in result['points']:
        assert p['point']==pytest.approx(5.0) and p['low']==pytest.approx(5.0) and p['high']==pytest.approx(5.0)


def test_month_rollover_crosses_year():
    result=forecasting.forecast_series([('2026-09',1.0),('2026-10',1.0),('2026-11',1.5)],horizon=3)
    assert [p['month'] for p in result['points']]==['2026-12','2027-01','2027-02']


def test_insufficient_history_is_reported_not_faked():
    result=forecasting.forecast_series([('2026-01',1.0),('2026-02',2.0)],horizon=1)
    assert result['status']=='INSUFFICIENT_HISTORY' and result['points']==[]


def test_horizon_bounds_are_enforced():
    series=[('2026-01',1.0),('2026-02',1.0),('2026-03',1.0)]
    with pytest.raises(ValueError):forecasting.forecast_series(series,horizon=0)
    with pytest.raises(ValueError):forecasting.forecast_series(series,horizon=7)


def test_duplicate_months_are_rejected():
    with pytest.raises(ValueError):
        forecasting.forecast_series([('2026-01',1.0),('2026-01',2.0),('2026-02',3.0)],horizon=1)


def test_unordered_months_are_rejected():
    with pytest.raises(ValueError):
        forecasting.forecast_series([('2026-03',3.0),('2026-01',1.0),('2026-02',2.0)],horizon=1)


def test_non_finite_values_block_contiguous_forecast():
    result=forecasting.forecast_series([('2026-01',1.0),('2026-02',float('nan')),('2026-03',2.0),('2026-04',3.0)],horizon=1)
    assert result['status']=='INSUFFICIENT_HISTORY' and result['points']==[]


def test_negative_projection_is_flagged():
    result=forecasting.forecast_series([('2026-01',10.0),('2026-02',7.0),('2026-03',3.0),('2026-04',0.5)],horizon=2)
    assert result['status']=='PASS'
    assert any(p['negative_warning'] for p in result['points'])


def test_snapshot_forecast_covers_overall_and_elements():
    trend=[]
    for i,(m,v) in enumerate([('2026-01',10.0),('2026-02',10.5),('2026-03',11.0),('2026-04',11.2),('2026-05',11.4),('2026-06',11.6)]):
        trend.append({'month':m,'unit_cost':v,'total_cost':v*10,'quantity':10,
                      'materials':v*0.6,'labor':v*0.2,'overhead':v*0.2})
    snapshot={'trend':trend,'basis':'unit','elements':[{'key':'materials'},{'key':'labor'},{'key':'overhead'}],
              'metrics':{'unit_cost':{'unit':'元/盒'}},'product':'合成制剂甲','factory':'合成制药厂甲'}
    result=forecasting.forecast_snapshot(snapshot,horizon=2)
    assert result['status']=='PASS'
    keys=[s['key'] for s in result['series']]
    assert keys[0]=='unit_cost' and {'materials','labor','overhead'}<=set(keys)
    assert all(s['status']=='PASS' for s in result['series'])
    assert result['caveat'] and '不构成' in result['caveat']
    empty=forecasting.forecast_snapshot({'trend':[],'elements':[],'basis':'unit'})
    assert empty['status']=='INSUFFICIENT_HISTORY'


def test_linear_tens_next_is_forty_and_baseline_is_explicit():
    result=forecasting.forecast_series([('2026-01',10),('2026-02',20),('2026-03',30)],horizon=1)
    assert result['points'][0]['point']==40
    assert result['baseline']['method']=='last_observation'
    assert result['baseline']['points'][0]['point']==30
    assert result['baseline']['one_step_mae']==10
    assert result['one_step_mae']==0


@pytest.mark.parametrize('series',[
    [('2026-01',10),('2026-03',20),('2026-04',30)],
    [('2026-01',10),('2026-02',20),('2026-03',30),('2026-04',None)],
])
def test_missing_month_blocks_forecast(series):
    result=forecasting.forecast_series(series,horizon=1)
    assert result['status']=='INSUFFICIENT_HISTORY' and result['points']==[]
    assert result['reason_code']=='NON_CONTIGUOUS_HISTORY'


def test_ols_init_robust_to_second_month_spike():
    """v3 初始化反例（2026-09-22 修复）：次月尖峰 [10, 12.5, 10.2, ...] 不再
    污染初始斜率——两点差分初始斜率=+2.5 会把 3 步预测拉到 12.5+；OLS 初始化
    的预测必须明显低于旧实现且贴近序列真实水平（≈10.2-11.0）。"""
    spike = [('2026-0%d' % m, v) for m, v in enumerate([10.0, 12.5, 10.2, 10.4, 10.6, 10.8], 1)]
    result = forecasting.forecast_series(spike, horizon=3)
    assert result['status'] == 'PASS'
    points = [p['point'] for p in result['points']]
    # 旧两点初始化实测输出 11.73/12.13/12.54；新初始化应全部 < 11.2
    assert all(p < 11.2 for p in points), points
    # OLS 初始化不拟合调参：仍是固定 α/β
    assert forecasting.ALPHA == 0.6 and forecasting.BETA == 0.3


def test_holdout_rolling_origin_reported():
    """滚动原点留出：>=4 点时给出实测留出 MAE；线性序列留出误差为 0。"""
    linear = [('2026-0%d' % m, float(m) * 5) for m in range(1, 7)]  # 5,10,...,30
    result = forecasting.forecast_series(linear, horizon=1)
    holdout = result['holdout']
    assert holdout['origins'] == 3 and holdout['mae'] == 0 and holdout['baseline_mae'] == 5
    assert '留出' in result['evaluation_notice'] and '3 个原点' in result['evaluation_notice']
    # 3 点历史无独立留出原点：如实声明而非伪造
    short = forecasting.forecast_series([('2026-01', 1.0), ('2026-02', 2.0), ('2026-03', 3.0)], horizon=1)
    assert short['holdout']['origins'] == 0 and short['holdout']['mae'] is None
    assert '无独立留出原点' in short['evaluation_notice']


def test_real_contest_series_holdout_improves_over_two_point_init():
    """真实题包序列（银黄 2026 单位成本）回归锚点：v3 留出 MAE 优于 v2 两点
    初始化（v2 实测 0.219，v3 实测 0.165）——防回归到敏感初始化。"""
    series = [('2026-0%d' % m, v) for m, v in
              enumerate([10.7, 10.87, 10.53, 10.9, 11.21, 10.93], 1)]
    result = forecasting.forecast_series(series, horizon=1)
    assert result['holdout']['origins'] == 3
    assert result['holdout']['mae'] < 0.219, result['holdout']
