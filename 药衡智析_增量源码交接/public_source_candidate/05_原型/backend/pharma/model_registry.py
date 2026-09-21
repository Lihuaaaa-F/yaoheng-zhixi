"""模型厂商注册表：预填充、档位与推理强度映射的单一来源。

三个模型角色（对应"模型配置"模块）：
- extraction 数据提取模型：赛题加分项"数据提取用小模型"，仅允许轻量档；
- analysis  数据分析模型：赛题基础项"大模型"（报告/归因/任务生成），仅允许旗舰/推理档；
- vector    向量模型：本地 ONNX 推理（knowledge.CpuEmbedding），不走 API。

档位数据来源：2026-09-22 逐家核对官方文档（docs.bigmodel.cn、api-docs.deepseek.com、
help.aliyun.com/zh/model-studio、platform.kimi.com、docs.siliconflow.cn、
developers.openai.com、ollama.com、docs.vllm.ai、lmstudio.ai）。厂商模型迭代快，
注册表只做"预填充 + 已知档位限制"，未收录的模型 ID 允许手填（状态页给出提示），
list_remote_models 可从端点拉取真实清单。
"""
from __future__ import annotations

from typing import Any

EFFORT_LEVELS = ('low', 'medium', 'high')
EFFORT_LABELS = {'low': '低', 'medium': '中', 'high': '高'}

ROLE_RULES = {
    'extraction': {
        'label': '数据提取模型（小模型）',
        'hint': '赛题多模型协作加分项：数据提取/字段映射等轻量任务使用小模型。仅提供轻量档模型；旗舰档被限制。',
        'allowed_tier': 'small', 'rejected_tier': 'large',
    },
    'analysis': {
        'label': '数据分析模型（大模型）',
        'hint': '赛题基础项：报告分析文本、看板归因、对标拆原因、整改任务生成使用大模型。仅提供旗舰/推理档模型；轻量档被限制。',
        'allowed_tier': 'large', 'rejected_tier': 'small',
    },
}

# 已知模型档位（registry 未收录的模型按 pattern 兜底分类，仍允许手填）。
_TIER_PATTERNS_SMALL = ('flash', 'air', 'mini', 'turbo', 'luna', 'terra', 'nano', 'small', 'lite', '-4b', '-7b', '-8b', '-9b', '3b')
_TIER_PATTERNS_LARGE = ('max', 'pro', 'ultra', 'astra', 'sol', '-k3', 'r1', '72b', '32b', '70b', 'reasoner')


def _v(vendor: str, label: str, base_url: str, models: list[tuple[str, str, str]],
       key_url: str = '', protocol: str = 'openai') -> dict[str, Any]:
    return {'id': vendor, 'label': label, 'base_url': base_url, 'protocol': protocol,
            'key_url': key_url,
            'models': [{'id': m, 'tier': tier, 'note': note} for m, tier, note in models]}


API_VENDORS = [
    _v('zhipu', '智谱 AI（BigModel）', 'https://open.bigmodel.cn/api/paas/v4', [
        ('glm-4.5-air', 'small', '轻量（128K）'),
        ('glm-4.5-airx', 'small', '轻量极速'),
        ('glm-4.7-flashx', 'small', '轻量高速（200K）'),
        ('glm-4.7-flash', 'small', '免费档（200K）'),
        ('glm-4.5-flash', 'small', '免费档（128K）'),
        ('glm-4-flash-250414', 'small', '免费档（128K/16K 输出）'),
        ('glm-4.6', 'large', '旗舰：编码/推理（200K）'),
        ('glm-4.7', 'large', '旗舰：通用（200K）'),
        ('glm-5', 'large', '旗舰：Agentic 长程（200K）'),
        ('glm-5.1', 'large', '推理增强（200K）'),
        ('glm-5.2', 'large', '旗舰（1M 上下文）'),
        ('glm-5.3', 'large', '旗舰：编程+智能体（1M/128K）'),
        ('glm-5.3-flash', 'large', '旗舰普惠（1M/128K，多模态）'),
        ('glm-5.3-flashx', 'large', '旗舰高速（约200 tok/s）'),
    ], key_url='https://bigmodel.cn/usercenter/proj-mgmt/apikeys'),
    _v('deepseek', 'DeepSeek', 'https://api.deepseek.com', [
        ('deepseek-flash', 'small', '轻量高速（V4.1-Flash，支持视觉）'),
        ('deepseek-chat', 'small', '旧名（当前文档未列出，未确认在售）'),
        ('deepseek-v4-pro', 'large', '旗舰（1M 上下文/384K 输出，默认思考）'),
        ('deepseek-reasoner', 'large', '旧名（当前文档未列出，未确认在售）'),
    ], key_url='https://platform.deepseek.com/api_keys'),
    _v('dashscope', '阿里云百炼（通义千问）', 'https://dashscope.aliyuncs.com/compatible-mode/v1', [
        ('qwen3.8-flash', 'small', '轻量高速'),
        ('qwen3.8-omni-flash', 'small', '全模态轻量'),
        ('qwen-turbo', 'small', '旧名（未确认在售）'),
        ('qwen3.7-plus', 'large', '均衡档（商业版）'),
        ('qwen-plus', 'large', '旧名（未确认在售）'),
        ('qwen3.8-max', 'large', '旗舰'),
        ('qwen-max', 'large', '旧名（未确认在售）'),
    ], key_url='https://bailian.console.aliyun.com/cn-beijing/model/settings/api-key'),
    _v('moonshot', '月之暗面 Kimi', 'https://api.moonshot.cn/v1', [
        ('kimi-k2.6', 'large', '通用（256K，思考/非思考双模式）'),
        ('kimi-k2.7-code', 'large', '编程专用（256K）'),
        ('kimi-k3', 'large', '旗舰（2.8T，1M 上下文，原生视觉）'),
    ], key_url='https://platform.kimi.com/console/api-keys'),
    _v('siliconflow', '硅基流动 SiliconFlow', 'https://api.siliconflow.cn/v1', [
        ('Qwen/Qwen2.5-3B-Instruct', 'small', '聚合免费/低价小模型'),
        ('Qwen/Qwen2.5-7B-Instruct', 'small', '聚合免费/低价小模型'),
        ('THUDM/glm-4-9b-chat', 'small', '聚合免费/低价小模型'),
        ('Qwen/Qwen2.5-32B-Instruct', 'large', '聚合开源大模型'),
        ('Qwen/Qwen2.5-72B-Instruct', 'large', '聚合开源大模型'),
        ('deepseek-ai/DeepSeek-R1', 'large', '聚合开源推理模型'),
    ], key_url='https://cloud.siliconflow.cn/account/ak'),
    _v('openai', 'OpenAI', 'https://api.openai.com/v1', [
        ('gpt-4o-mini', 'small', '轻量'),
        ('gpt-5.6-luna', 'small', '轻量（nano 级）'),
        ('gpt-5.6-terra', 'small', '平衡（mini 级）'),
        ('gpt-4o', 'large', '旗舰'),
        ('gpt-5.6-sol', 'large', '主力（复杂任务）'),
        ('gpt-6-astra', 'large', '旗舰'),
    ], key_url='https://platform.openai.com/api-keys'),
]

LOCAL_VENDORS = [
    _v('ollama', 'Ollama（本地）', 'http://127.0.0.1:11434/v1', [
        ('qwen2.5:3b', 'small', '3B，结构化提取够用（约2GB）'),
        ('qwen2.5:7b', 'small', '7B，推荐（4.7GB，JSON 遵循好）'),
        ('deepseek-r1:8b', 'small', '8B 蒸馏推理（5.2GB，输出含推理链）'),
        ('glm4:9b', 'small', '9B（5.5GB）'),
        ('qwen2.5:14b', 'large', '14B'),
        ('qwen2.5:32b', 'large', '32B'),
        ('deepseek-r1:32b', 'large', '32B 蒸馏推理'),
    ]),
    _v('vllm', 'vLLM（本地）', 'http://127.0.0.1:8000/v1', [
        ('Qwen2.5-7B-Instruct', 'small', 'vllm serve 启动时加载的模型'),
        ('Qwen2.5-32B-Instruct', 'large', 'vllm serve 启动时加载的模型'),
    ]),
    _v('lmstudio', 'LM Studio（本地）', 'http://127.0.0.1:1234/v1', [
        ('qwen2.5-7b-instruct', 'small', '应用内已加载的模型'),
        ('qwen2.5-32b-instruct', 'large', '应用内已加载的模型'),
    ]),
]

_LOCAL_KEY_HINT = '本地服务通常无需密钥；表单留空即可（Ollama 不校验密钥值）。'


def classify_tier(model: str) -> str | None:
    """返回已知模型档位 small/large；未收录返回 None（允许手填，不硬拒）。"""
    model_id = (model or '').strip().lower()
    if not model_id:
        return None
    for vendor in API_VENDORS + LOCAL_VENDORS:
        for entry in vendor['models']:
            if entry['id'].lower() == model_id:
                return entry['tier']
    # 未收录：按常见命名兜底。本地 tag（如 qwen2.5:7b）先按参数规模判断。
    if any(p in model_id for p in _TIER_PATTERNS_LARGE):
        return 'large'
    if any(p in model_id for p in _TIER_PATTERNS_SMALL):
        return 'small'
    return None


def tier_error(route: str, model: str) -> str | None:
    """档位限制：extraction 拒绝已知 large，analysis 拒绝已知 small。"""
    rule = ROLE_RULES.get(route)
    if not rule or not model:
        return None
    tier = classify_tier(model)
    if tier is None or tier == rule['allowed_tier']:
        return None
    return (f'{rule["label"]}不应使用{"旗舰/推理档" if tier == "large" else "轻量档"}模型 {model}'
            f'（赛题要求：报表生成用大模型、数据提取用小模型）。请选择{"轻量档" if route == "extraction" else "旗舰/推理档"}模型或手动填写未收录模型。')


def effort_body_params(model: str, base_url: str, effort: str) -> dict[str, Any]:
    """把统一推理强度档（low/medium/high）映射为各厂商请求参数。

    依据 2026-09-22 官方文档：GLM-5.3 系列仅接受 low/high/max；GLM-5.2 另有
    medium/xhigh；DeepSeek 用 thinking.type；通义用 enable_thinking；OpenAI 用
    reasoning_effort；Kimi-k3 用顶层 reasoning_effort（low/high/max）。
    未识别的厂商不附加参数（端点忽略未知字段或按默认档执行）。
    """
    if effort not in EFFORT_LEVELS:
        return {}
    model_id = (model or '').lower()
    from urllib.parse import urlsplit
    host = (urlsplit(base_url or '').hostname or '').lower()
    if model_id.startswith('glm-5.3') or 'kimi-k3' in model_id or model_id.startswith('gpt-6'):
        return {'reasoning_effort': {'low': 'low', 'medium': 'high', 'high': 'max'}[effort]}
    if model_id.startswith('glm-5.2'):
        # GLM-5.2 起支持 medium/xhigh（官方 thinking 文档）。
        return {'reasoning_effort': {'low': 'low', 'medium': 'medium', 'high': 'xhigh'}[effort]}
    if model_id.startswith('glm-5'):
        # GLM-5/5.1/5-turbo：沿用实测可用档 low/high/max（1210 错误明示不支持关闭思考）。
        return {'reasoning_effort': {'low': 'low', 'medium': 'high', 'high': 'max'}[effort]}
    if host.endswith('deepseek.com'):
        return {'thinking': {'type': 'enabled' if effort != 'low' else 'disabled'}}
    if host.endswith('aliyuncs.com'):
        return {'enable_thinking': effort != 'low'}
    if host.endswith('openai.com') or model_id.startswith('gpt-'):
        return {'reasoning_effort': effort}
    return {}


def presets_payload() -> dict[str, Any]:
    return {'api_vendors': API_VENDORS, 'local_vendors': LOCAL_VENDORS,
            'local_key_hint': _LOCAL_KEY_HINT,
            'effort_levels': [{'id': x, 'label': EFFORT_LABELS[x]} for x in EFFORT_LEVELS],
            'role_rules': ROLE_RULES}
