# -*- coding: utf-8 -*-
"""知识图谱增强检索的增益对照（2026-09-23 审计 AUD-T-06/FIX-7）。

同一查询集在 graph_enabled=True/False 下各检索一次（其余条件完全相同），
对比 Top-N 命中 golden 来源文档的比例与首中排名（MRR）。golden 由题包
事实人工指定（查询→应命中的源文档名），不经被测系统生成。

诚实声明：查询集小（约 10 条）、golden 为单一目标文档（命中该文档任一
分片即算命中），结果只回答"本查询集上有无增益"，不能外推为总体收益。
输出 docs/validation/graph_gain_20260923.json。
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
ROOT = APP.parent
sys.path.insert(0, str(APP / 'backend'))

# 查询集：(查询, 产品或None, golden 源文档文件名片段)
# 产品用于适用性过滤与图谱扩展（expansion_terms 以产品为锚点）。
QUERIES = [
    ('金银花 用量 配比', '银黄口服液', '产品配方文档_银黄口服液'),
    ('黄芩 提取 工艺参数', '银黄口服液', '生产工艺文档_中药一厂'),
    ('银黄口服液 处方组成', '银黄口服液', '产品配方文档_银黄口服液'),
    ('板蓝根 制粒 干燥', '板蓝根颗粒', '生产工艺文档_中药一厂'),
    ('板蓝根颗粒 处方', '板蓝根颗粒', '产品配方文档_板蓝根颗粒'),
    ('山茱萸 用量', '六味地黄胶囊', '产品配方文档_六味地黄胶囊'),
    ('六味地黄胶囊 工序', '六味地黄胶囊', '生产工艺文档_中药一厂'),
    ('灌装 轧盖 工序', '银黄口服液', '生产工艺文档_中药一厂'),
    ('胶囊填充 填充机', '六味地黄胶囊', '车间设备清单_中药一厂'),
    ('GMP 偏差处理', None, 'GMP法规核心摘要_2010修订版'),
]


def evaluate(graph_enabled: bool):
    from pharma.metrics import analyze
    from pharma.context_services import retrieve
    rows = []
    for query, product, golden in QUERIES:
        snapshot = analyze('中药一厂', product or '银黄口服液', '2026-05')
        result = retrieve(snapshot, query, limit=5, graph_enabled=graph_enabled)
        evidence = result.get('evidence', [])
        ranks = [i + 1 for i, e in enumerate(evidence) if golden in str(e.get('source', ''))]
        hit = bool(ranks)
        rows.append({'query': query, 'product': product, 'golden': golden, 'hit': hit,
                     'first_rank': min(ranks) if ranks else None, 'top_sources':
                     [str(e.get('source', '')) for e in evidence[:3]]})
    hits = sum(1 for r in rows if r['hit'])
    mrr = sum(1 / r['first_rank'] for r in rows if r['first_rank']) / len(rows)
    return {'graph_enabled': graph_enabled, 'hits': hits, 'total': len(rows),
            'hit_rate': round(hits / len(rows), 3), 'mrr': round(mrr, 3), 'rows': rows}


def main():
    baseline = evaluate(False)
    enhanced = evaluate(True)
    delta_hits = enhanced['hits'] - baseline['hits']
    delta_mrr = round(enhanced['mrr'] - baseline['mrr'], 3)
    conclusion = ('图谱 BM25 扩展在本查询集上：' +
                  (f"命中 {baseline['hits']}→{enhanced['hits']}，MRR {baseline['mrr']}→{enhanced['mrr']}，"
                   f"{'有正增益' if delta_hits > 0 or delta_mrr > 0 else '无正增益' if delta_hits == 0 and delta_mrr == 0 else '出现负增益'}。"
                   '查询集仅 10 条、golden 为单目标文档，结果不能外推为总体收益；'
                   '该对照用于把 gain_status=NOT_ESTABLISHED 更新为"已做小样本对照"。'))
    result = {'generated_at': '2026-09-23', 'queries': len(QUERIES),
              'baseline': baseline, 'enhanced': enhanced, 'conclusion': conclusion}
    out = ROOT / 'docs/validation/graph_gain_20260923.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    summary = {k: {kk: vv for kk, vv in v.items() if kk != 'rows'} for k, v in (('baseline', baseline), ('enhanced', enhanced))}
    print(json.dumps({'summary': summary, 'conclusion': conclusion}, ensure_ascii=False, indent=1))
    print(f'WRITTEN {out}')


if __name__ == '__main__':
    main()
