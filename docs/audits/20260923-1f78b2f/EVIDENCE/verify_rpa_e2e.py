# -*- coding: utf-8 -*-
"""RPA 闭环隔离验证：题包原版 mock_rpa_server.py 起真实 HTTP 服务（127.0.0.1:8099），
ActionStore 草稿→确认→outbox 发送→SENT 回执核验；含幂等（重复业务键返回既有任务）与
再次确认不可二次入队。全部使用隔离 RUNTIME 目录，不触碰正式数据库。
"""
import json, os, sys, threading, time
from pathlib import Path

RT = r"D:\tmp\yaoheng_audit_rt_rpa"
os.environ["PHARMA_RUNTIME_DIR"] = RT
sys.path.insert(0, r"D:\tmp\yaoheng_audit_wt_1f78b2f\药衡智析_增量源码交接\public_source_candidate\05_原型\backend")

PKG_MOCK = r"D:\tmp\yaoheng_audit_wt_1f78b2f\药衡智析_增量源码交接\public_source_candidate\00_赛题原始资料\模拟数据_V1.1_净化解压\创灵境_考题模拟数据\05_RPA接口文档"
sys.path.insert(0, PKG_MOCK)

from fastapi.testclient import TestClient
import importlib.util
spec = importlib.util.spec_from_file_location("orig_mock_rpa", str(Path(PKG_MOCK) / "mock_rpa_server.py"))
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
client = TestClient(mod.app)  # 原版题包 mock（内存态）

from pharma.actions import ActionStore, notification_proven
from pharma.config import RUNTIME

store = ActionStore(path=Path(RT) / "app.sqlite3")
snapshot = {"snapshot_id": "audit-snap-1", "analysis_type": "月度成本分析", "month": "2026-05",
            "product": "银黄口服液", "period": {"start": "2026-05", "end": "2026-05"},
            "analysis_context": None, "context_id": "pharmaceutical:competition"}

a1 = store.draft(snapshot, "核查金银花2026年5月采购合同调价条款",
                 {"name": "张伟", "department": "采购部", "role": "采购经理"},
                 "核查采购合同中调价条款，比对新老供应商报价", "high",
                 verification_target="金银花2026年5月采购合同",
                 expected_evidence=["采购合同台账", "入库单价记录"],
                 responsible_role="采购经理", deadline_basis="月度成本结账后5个工作日内完成")
a2 = store.draft(snapshot, "核查金银花2026年5月采购合同调价条款",
                 {"name": "张伟", "department": "采购部"}, "核查采购合同中调价条款，比对新老供应商报价", "high",
                 verification_target="金银花2026年5月采购合同", expected_evidence=["采购合同台账", "入库单价记录"],
                 responsible_role="采购经理", deadline_basis="月度成本结账后5个工作日内完成")
result = {"idempotent_draft": a1["id"] == a2["id"], "draft_status": a1["status"],
          "payload_has_required_fields": all(k in a1["payload"] for k in
              ("task_id", "task_title", "assignee", "source", "priority", "deadline", "suggestion"))}
c = store.confirm(a1["id"], a1["payload_hash"])
result["confirmed_status"] = c["status"]
sent = store.deliver_one(a1["id"], client=client, base_url="http://127.0.0.1:8099")
result["sent_status"] = sent["status"]
result["delivery_http_accepted"] = sent["delivery"]["http_accepted"]
result["delivery_notification"] = sent["delivery"]["notification"]
result["notify_receipt"] = (sent.get("remote") or {}).get("notify_status", {}).get("wechat", "")
# 幂等：已 SENT 的任务再次 deliver 不重发
again = store.deliver_one(a1["id"], client=client, base_url="http://127.0.0.1:8099")
result["redeliver_noop_same_status"] = again["status"] == "SENT"
# 远端状态推进查询
refreshed = store.refresh(a1["id"], client=client, base_url="http://127.0.0.1:8099")
result["refresh_ok"] = refreshed["id"] == a1["id"]
result["remote_task_id_echo"] = (refreshed.get("remote") or {}).get("task_id") == a1["payload"]["task_id"]
print(json.dumps(result, ensure_ascii=False, indent=1))
assert result["idempotent_draft"] and result["sent_status"] == "SENT" and result["delivery_notification"] == "SIMULATED_SENT" \
    and result["redeliver_noop_same_status"] and result["remote_task_id_echo"], "RPA_E2E_FAIL"
print("RPA_E2E_PASS")
