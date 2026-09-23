# -*- coding: utf-8 -*-
"""第二段：在同一隔离环境调用被测引擎 pharma.metrics，与独立期望对比。
"""
import json, os, sys
from decimal import Decimal as D

os.environ.setdefault("PHARMA_RUNTIME_DIR", r"D:\tmp\yaoheng_audit_rt")
os.environ.setdefault("PHARMA_TEMPLATE_DIR", r"D:\tmp\yaoheng_audit_rt\template")
os.environ.setdefault("PHARMA_DATA_PACKAGE", r"D:\tmp\yaoheng_audit_wt_1f78b2f\药衡智析_增量源码交接\public_source_candidate\00_赛题原始资料\模拟数据_V1.1_净化解压\创灵境_考题模拟数据")

sys.path.insert(0, r"D:\tmp\yaoheng_audit_wt_1f78b2f\药衡智析_增量源码交接\public_source_candidate\05_原型\backend")
from pharma import metrics

exp = json.load(open(r"D:\tmp\audit_indep_expected.json", encoding="utf-8"))
report = {"comparisons": [], "all_pass": True}

def cmp_case(name, engine_value, expected_value, tol=0.0001):
    ok = False
    if expected_value is None:
        ok = engine_value is None
    elif engine_value is not None:
        ok = abs(D(str(engine_value)) - D(str(expected_value))) <= D(str(tol))
    report["comparisons"].append({"case": name, "engine": None if engine_value is None else str(engine_value),
                                   "independent": None if expected_value is None else str(expected_value),
                                   "pass": ok})
    if not ok: report["all_pass"] = False

for product, month in [("银黄口服液", "2026-05"), ("板蓝根颗粒", "2026-05"), ("六味地黄胶囊", "2026-03")]:
    snap = metrics.analyze("中药一厂", product, month, "monthly", "unit")
    indep = exp[f"{product}:{month}:indep"]
    tag = f"{product}:{month}"
    cmp_case(tag + " unit_cost", snap["metrics"]["unit_cost"]["value"], indep["unit_cost"])
    cmp_case(tag + " mom_rate", snap["comparison"]["mom"]["rate"], indep["mom_rate"])
    cmp_case(tag + " yoy_rate", snap["comparison"]["yoy"]["rate"], indep["yoy_rate"])
    cmp_case(tag + " budget_rate", snap["comparison"]["budget"]["rate"], indep["budget_rate"])
    cmp_case(tag + " mom_unit_cost_delta", snap["comparison"]["mom"]["delta"], indep["mom_unit_cost_delta"])
    for e in snap["elements"]:
        ie = indep["elements"][e["key"]]
        cmp_case(f"{tag} {e['key']} unit", e["unit"], ie["unit"])
        cmp_case(f"{tag} {e['key']} unit_delta", e["comparisons"]["mom"]["unit"]["delta"], ie["mom_delta_unit"])
        cmp_case(f"{tag} {e['key']} unit_rate", e["comparisons"]["mom"]["unit"]["rate"], ie["mom_rate"])
        cmp_case(f"{tag} {e['key']} unit_contribution", e["comparisons"]["mom"]["unit"]["contribution"], indep["contributions"][e["key"]])
        engine_alert = any(a["element_key"] == e["key"] and a["basis"] == "unit" for a in snap["alerts"])
        report["comparisons"].append({"case": f"{tag} {e['key']} alert_strict>10%", "engine": engine_alert,
                                       "independent": ie["alert_strict"], "pass": engine_alert == ie["alert_strict"]})
        if engine_alert != ie["alert_strict"]: report["all_pass"] = False
    bb = snap["budget_bridge"]
    cmp_case(tag + " bridge.quantity_effect", bb["quantity_effect"], indep["budget_bridge"]["quantity_effect"])
    cmp_case(tag + " bridge.unit_cost_effect", bb["unit_cost_effect"], indep["budget_bridge"]["unit_effect"])
    cmp_case(tag + " bridge.total_delta", bb["total_delta"], indep["budget_bridge"]["total_delta"])
    ms = snap["materials_summary"]
    top = exp[f"{product}:{month}:top_material"]
    if ms and top.get("expected_top_name"):
        engine_top = ms[0]
        report["comparisons"].append({"case": f"{tag} top_material name",
            "engine": engine_top["name"], "independent": top["expected_top_name"],
            "pass": engine_top["name"] == top["expected_top_name"]})
        if engine_top["name"] != top["expected_top_name"]: report["all_pass"] = False
        else: cmp_case(f"{tag} top_material delta", engine_top["delta"], top["expected_delta"])
    # 数据源哈希与快照稳定性
    report.setdefault("snapshots", {})[tag] = snap["snapshot_id"][:16]

# 对标 ≤1%
for product, month in [("银黄口服液", "2026-05"), ("板蓝根颗粒", "2026-05")]:
    comp = metrics.benchmark(product, month)
    s0 = comp["summary"][0]
    eb = exp[f"benchmark:{product}:{month}"]
    cmp_case(f"benchmark {product} delta", s0["delta"], eb["expected_delta"])
    cmp_case(f"benchmark {product} rate", s0["rate"], eb["expected_rate"])
    rel = abs(D(s0["delta"]) - D(eb["expected_delta"])) / abs(D(eb["expected_delta"])) * 100 if D(eb["expected_delta"]) != 0 else D(0)
    report["comparisons"].append({"case": f"benchmark {product} relative_error_pct<=1",
                                   "engine": str(rel), "independent": "0", "pass": rel <= D("1")})
    if rel > D("1"): report["all_pass"] = False

print(json.dumps(report, ensure_ascii=False, indent=1))
with open(r"D:\tmp\audit_engine_compare.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print("ALL_PASS" if report["all_pass"] else "HAS_MISMATCH")
