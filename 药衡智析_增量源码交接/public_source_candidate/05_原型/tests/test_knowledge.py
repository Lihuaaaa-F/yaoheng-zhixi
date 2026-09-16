from pharma.knowledge import reciprocal_rank_fusion

def test_rrf_uses_ranks_not_incompatible_raw_scores():
    assert reciprocal_rank_fusion([['a','b'],['b','c']],limit=3) == ['b','a','c']
    assert reciprocal_rank_fusion([[],[]]) == []


def test_chinese_bm25_direction_and_vector_failure_are_visible(tmp_path):
    from pharma.knowledge import Knowledge
    source=tmp_path/'sources';source.mkdir()
    (source/'a.txt').write_text('胶囊填充机计量盘磨损，设备维护应保留记录，胶囊填充机需要预防性维护。')
    (source/'b.txt').write_text('银黄口服液金银花水提取和浓缩工艺需要监测，设备使用日志应留存。')
    k=Knowledge(root=tmp_path,source_dir=source,vector_enabled=False)
    k.build()
    result=k.search('胶囊填充机计量盘磨损',mode='bm25')
    assert result['evidence'][0]['source']=='a.txt'
    degraded=k.search('胶囊填充机',mode='hybrid')
    assert degraded['status']=='DEGRADED' and degraded['evidence']
