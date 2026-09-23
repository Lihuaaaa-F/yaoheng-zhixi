# -*- coding: utf-8 -*-
"""独立数值复算：期望值直接从题包原始 CSV 用 Decimal 推导，不调用被测引擎生成。
对比对象：worktree(1f78b2f) 后端 pharma.metrics 引擎输出。
覆盖：单位成本/环比/同比/预算偏差/贡献度/±10%阈值/原料明细排序/对标差异与≤1%精度/预算桥。
"""
import csv, io, json, os, sys
from decimal import Decimal as D, getcontext
getcontext().prec = 40

PKG = r"D:\tmp\yaoheng_audit_wt_1f78b2f\药衡智析_增量源码交接\public_source_candidate\00_赛题原始资料\模拟数据_V1.1_净化解压\创灵境_考题模拟数据"
DATA = PKK = os.path.join(PKG, "01_成本明细数据")

def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

cost26 = load("中药一厂_成本汇总_2026年1-6月.csv")
cost25 = load("中药一厂_成本汇总_2025年1-6月.csv")
budget = load("中药一厂_预算数据_2026年.csv")
mats   = load("中药一厂_原材料消耗明细_2026年1-6月.csv")
p2_26  = load("中药二厂_成本汇总_2026年1-6月.csv")
p2_25  = load("中药二厂_成本汇总_2025年1-6月.csv")

def row(rows, factory, product, month):
    for r in rows:
        if r["工厂"] == factory and r["产品名称"] == product and r["月份"] == month:
            return r
    return None

ELEMS = [("直接材料(元/盒)", "materials"), ("直接人工(元/盒)", "labor"), ("制造费用(元/盒)", "overhead")]

def shift(m, k):
    y, mm = int(m[:4]), int(m[5:7]); t = y * 12 + mm - 1 + k
    return f"{t//12:04}-{t%12+1:02}"

expected = {}
def check(name, got, exp, tol=D("0.0001")):
    ok = got is not None and exp is not None and abs(D(str(got)) - D(str(exp))) <= tol
    expected[name] = {"expected": str(exp), "engine": str(got), "match": bool(ok)}
    if not ok:
        expected[name]["MISMATCH"] = True

for product, month in [("银黄口服液", "2026-05"), ("板蓝根颗粒", "2026-05"), ("六味地黄胶囊", "2026-03")]:
    cur = row(cost26, "中药一厂", product, month)
    prev = row(cost26, "中药一厂", product, shift(month, -1))
    yoy = row(cost25, "中药一厂", product, shift(month, -12))
    bud = row(budget, "中药一厂", product, month)
    q, uc, tc = D(cur["产量(盒)"]), D(cur["单位成本(元/盒)"]), D(cur["总成本(元)"])
    p_uc, p_tc = D(prev["单位成本(元/盒)"]), D(prev["总成本(元)"])
    y_uc = D(yoy["单位成本(元/盒)"]) if yoy else None
    b_uc, b_q, b_tc = D(bud["预算单位成本(元/盒)"]), D(bud["预算产量(盒)"]), D(bud["预算总成本(元)"])
    check(f"{product}:{month}:unit_cost", None, uc); expected[f"{product}:{month}:unit_cost"]["engine"] = "见下"
    # 原料单位消耗：本期/上期同名原料 Σ原材料总成本/Σ产量
    def mat_unit(name, m):
        rs = [r for r in mats if r["产品名称"] == product and r["月份"] == m and r["原材料名称"] == name]
        if not rs: return None, None
        tot = sum(D(r["原材料总成本(元)"]) for r in rs); qt = sum(D(r["产量(盒)"]) for r in rs)
        return tot / qt, tot
    mat_names = sorted({r["原材料名称"] for r in mats if r["产品名称"] == product and r["月份"] == month})
    mat_deltas = []
    for name in mat_names:
        cu_v, _ = mat_unit(name, month); pv_v, _ = mat_unit(name, shift(month, -1))
        if cu_v is not None and pv_v is not None:
            mat_deltas.append((cu_v - pv_v, name, cu_v, pv_v))
    mat_deltas.sort(key=lambda x: -abs(x[0]))
    expected[f"{product}:{month}:top_material"] = {
        "expected": f"{mat_deltas[0][1]} delta={mat_deltas[0][0]:.6f}" if mat_deltas else "N/A",
        "engine": "见下"}
    if mat_deltas:
        expected[f"{product}:{month}:top_material"]["expected_top_name"] = mat_deltas[0][1]
        expected[f"{product}:{month}:top_material"]["expected_delta"] = str(mat_deltas[0][0])
    # 独立存档（引擎对比在第二段填）
    expected[f"{product}:{month}:indep"] = {
        "unit_cost": str(uc), "mom_rate": str((uc - p_uc) / p_uc * 100),
        "yoy_rate": str((uc - y_uc) / y_uc * 100) if y_uc else None,
        "budget_rate": str((uc - b_uc) / b_uc * 100),
        "mom_unit_cost_delta": str(uc - p_uc),
        "elements": {k: {"unit": cur[f], "mom_delta_unit": str(D(cur[f]) - D(prev[f])),
                          "mom_rate": str((D(cur[f]) - D(prev[f])) / D(prev[f]) * 100),
                          "alert_strict": bool(abs((D(cur[f]) - D(prev[f])) / D(prev[f]) * 100) > D(10))}
                     for f, k in ELEMS},
        "contributions": {k: str((D(cur[f]) - D(prev[f])) / (uc - p_uc) * 100) for f, k in ELEMS},
        "budget_bridge": {"quantity_effect": str((q - b_q) * b_uc), "unit_effect": str(q * (uc - b_uc)),
                           "total_delta": str(tc - b_tc)},
    }

# 对标：一厂−二厂 同产品同期，以二厂为分母（银黄口服液 2026-05 单位成本）
for product, month in [("银黄口服液", "2026-05"), ("板蓝根颗粒", "2026-05")]:
    a = row(cost26, "中药一厂", product, month); b = row(p2_26, "中药二厂", product, month)
    ua, ub = D(a["单位成本(元/盒)"]), D(b["单位成本(元/盒)"])
    expected[f"benchmark:{product}:{month}"] = {
        "expected_delta": str(ua - ub), "expected_rate": str((ua - ub) / ub * 100), "engine": "见下"}

print(json.dumps(expected, ensure_ascii=False, indent=1))
with open(r"D:\tmp\audit_indep_expected.json", "w", encoding="utf-8") as f:
    json.dump(expected, f, ensure_ascii=False, indent=1)
print("INDEP_EXPECTED_WRITTEN")
