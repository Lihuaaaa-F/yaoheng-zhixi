"""报告生成链路版本指纹的单一来源（2026-09-21 修复 #21）。

此前 api._generation_versions 与 worker 的重提交校验各自维护键清单，
改缓存/合同逻辑漏改一处即产生静默漂移（审计问题 #21）。现统一到本模块：

- soft_items：网关耦合项。旧任务可能缺省（缺省不拒收）；已记录且与当前
  不一致 → 必须重提交（模型/端点/提示词/渲染器变化会使产物失真）。
- hard_items：合同与知识项。缺失即拒收——旧任务不能在不同校验/知识解析
  合同下复用部分或全部结果。

api 的指纹字典与 worker 的重提交校验都从这两张清单派生；新增版本键只改
这里，两侧自动一致。
"""
from __future__ import annotations


def soft_items(gateway):
    """网关耦合版本项：[(键, 当前值)]。"""
    from .reports import RENDERER_VERSION
    from .narrative import PROMPT_VERSION
    from .attribution import ATTRIBUTION_VERSION
    return [('renderer', RENDERER_VERSION), ('model', gateway.model), ('protocol', gateway.provider),
            ('endpoint', gateway.base_url), ('prompt', PROMPT_VERSION), ('attribution', ATTRIBUTION_VERSION)]


def hard_items(snapshot):
    """合同/知识版本项：[(键, 当前值)]。快照缺 analysis_context 时按空口径计算。"""
    from .narrative import VALIDATOR_VERSION
    from .context_services import retrieval_policy_version
    from .knowledge import PARSER_VERSION, RETRIEVER_VERSION, EMBEDDING_SHA, terminology_hash
    return [('retrieval_policy', retrieval_policy_version(snapshot.get('analysis_context') or {})),
            ('validator', VALIDATOR_VERSION), ('parser', PARSER_VERSION),
            ('terminology', terminology_hash()), ('retriever', RETRIEVER_VERSION),
            ('embedding', EMBEDDING_SHA)]
