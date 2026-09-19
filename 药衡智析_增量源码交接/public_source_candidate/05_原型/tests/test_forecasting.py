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
