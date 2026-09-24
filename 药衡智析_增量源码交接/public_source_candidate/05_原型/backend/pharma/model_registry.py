"""模型厂商注册表：预填充、档位与推理强度映射的单一来源。

模型角色（对应"模型配置"模块）：
- extraction 数据提取模型：建议轻量模型；
- analysis 数据分析模型：建议质量较高的大模型，实际效果由评测决定；
- assistant 独立助手：型号与参数自由配置，凭据不跨角色复用；
- vector    向量模型：本地 ONNX 推理（knowledge.CpuEmbedding），不走 API。

档位数据来源：2026-09-22 逐家核对官方文档（docs.bigmodel.cn、api-docs.deepseek.com、
help.aliyun.com/zh/model-studio、platform.kimi.com、docs.siliconflow.cn、
developers.openai.com、ollama.com、docs.vllm.ai、lmstudio.ai）。厂商模型迭代快，
注册表只做"预填充 + 档位建议"，所有模型 ID 都允许手填，
list_remote_models 可从端点拉取真实清单。
"""
from __future__ import annotations

from typing import Any

EFFORT_LEVELS = ('', 'none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max')
EFFORT_LABELS = {'': '服务默认', 'none': '关闭思考（需模型支持）', 'minimal': '最少',
                 'low': '低', 'medium': '中', 'high': '高', 'xhigh': '更高', 'max': '最高'}

ROLE_RULES = {
    'extraction': {
        'label': '数据提取模型（小模型）',
        'hint': '建议轻量模型处理数据提取与字段映射；仍可自由选择型号，并用实际效果验证。',
        'allowed_tier': 'small', 'rejected_tier': 'large',
    },
    'analysis': {
        'label': '数据分析模型（大模型）',
        'hint': '建议选择结构化输出和中文分析能力强的模型；档位仅作建议，不限制型号。',
        'allowed_tier': 'large', 'rejected_tier': 'small',
    },
    'assistant': {'label': '工作台 AI 助手', 'hint': '独立服务地址、密钥与参数；不借用报告模型的凭据。',
                  'allowed_tier': None, 'rejected_tier': None},
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


def tier_advice(route: str, model: str) -> str | None:
    """档位仅作建议；模型名不能替代真实质量与成本评测。"""
    rule = ROLE_RULES.get(route)
    if not rule or not model or not rule.get('allowed_tier'):
        return None
    tier = classify_tier(model)
    if tier is None or tier == rule['allowed_tier']:
        return None
    return f'{rule["label"]}通常建议选择{rule["allowed_tier"]}档；当前选择仍可保存，请用实际任务检验质量和成本。'


def tier_error(route: str, model: str) -> str | None:
    """旧调用兼容：不再把档位建议用作保存阻塞条件。"""
    return None


def effort_body_params(model: str, base_url: str, effort: str) -> dict[str, Any]:
    params, _, errors = reasoning_parameters(model, base_url, effort)
    if errors:
        raise ValueError('MODEL_PARAMETERS_UNSUPPORTED: ' + '；'.join(errors))
    return params


def reasoning_parameters(model: str, base_url: str, effort: str, protocol: str = 'openai'):
    """明确返回请求字段、提示和阻塞原因，不把“低”偷偷当成“关闭”。

    2026-09-23 核对一手文档：docs.z.ai/guides/capabilities/thinking、
    api-docs.deepseek.com/guides/thinking_mode、
    platform.claude.com/docs/en/build-with-claude/effort。
    默认档完全不发送推理字段；未知兼容端点明示尚未验证。
    """
    if not effort:
        return {}, [], []
    if effort not in EFFORT_LEVELS:
        return {}, [], ['推理强度取值无效']
    from urllib.parse import urlsplit
    host = (urlsplit(base_url or '').hostname or '').lower()
    model_id = (model or '').lower()
    warnings: list[str] = []
    if protocol == 'anthropic':
        if effort in ('none', 'minimal'):
            return {'thinking': {'type': 'disabled'}}, ['关闭思考需该模型支持；不支持时请选服务默认'], []
        mapped = 'max' if effort == 'xhigh' else effort
        return {'output_config': {'effort': mapped}}, ['仅支持 effort 的 Anthropic 兼容模型可使用此参数；旧模型请选服务默认'], []
    if model_id.startswith('glm-5.3'):
        if effort == 'none':
            return {}, [], ['GLM-5.3 不支持关闭思考；请选 low、high、max 或服务默认']
        mapped = {'minimal': 'low', 'medium': 'high', 'xhigh': 'max'}.get(effort, effort)
        if mapped != effort:
            warnings.append(f'GLM-5.3 将 {effort} 明确映射为 {mapped}；思考仍然开启')
        return {'reasoning_effort': mapped}, warnings, []
    if model_id.startswith('glm-5.2'):
        return {'reasoning_effort': effort}, [], []
    if model_id.startswith(('glm-5', 'glm-4.5', 'glm-4.6', 'glm-4.7')):
        return {'thinking': {'type': 'disabled' if effort == 'none' else 'enabled'}}, ['该 GLM 型号仅映射思考开关，不声称支持精确强度档位'], []
    if host == 'api.deepseek.com':
        if effort == 'none':
            return {'thinking': {'type': 'disabled'}}, [], []
        mapped = {'minimal': 'low', 'medium': 'high', 'xhigh': 'max'}.get(effort, effort)
        if mapped != effort:
            warnings.append(f'DeepSeek 将 {effort} 明确映射为 {mapped}')
        return {'thinking': {'type': 'enabled'}, 'reasoning_effort': mapped}, warnings, []
    if host.endswith('.aliyuncs.com'):
        return {'enable_thinking': effort != 'none'}, ['当前通义适配映射思考开关，强度档位不作等效承诺'], []
    if host == 'api.openai.com' or model_id.startswith(('gpt-', 'o1', 'o3', 'o4')):
        return {'reasoning_effort': effort}, ['不同 OpenAI 模型支持的强度不同；以连接测试为准，未支持请选服务默认'], []
    return {'reasoning_effort': effort}, ['此兼容服务的推理参数尚未验证；将原样发送 reasoning_effort，不支持时请选服务默认'], []


def uses_completion_tokens(model: str, base_url: str) -> bool:
    from urllib.parse import urlsplit
    return (urlsplit(base_url or '').hostname == 'api.openai.com'
            and (model or '').lower().startswith(('gpt-5', 'gpt-6', 'o1', 'o3', 'o4')))


def presets_payload() -> dict[str, Any]:
    return {'api_vendors': API_VENDORS, 'local_vendors': LOCAL_VENDORS,
            'local_key_hint': _LOCAL_KEY_HINT,
            'effort_levels': [{'id': x, 'label': EFFORT_LABELS[x]} for x in EFFORT_LEVELS],
            'role_rules': ROLE_RULES}
