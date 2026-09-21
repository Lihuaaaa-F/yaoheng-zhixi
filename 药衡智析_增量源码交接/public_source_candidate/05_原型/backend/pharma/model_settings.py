"""模型连接设置：API 与后台任务读取同一份配置。

三个模型角色（"模型配置"模块）：
  extraction 数据提取模型（小模型，赛题加分项）；analysis 数据分析模型（大模型，
  赛题基础项）；vector 向量模型（本地 ONNX，仅本地路径，不提供 API 选项）。

解析优先级（与既有环境变量语义兼容）：
  显式构造参数 → 环境变量 → 本设置文件（RUNTIME/model_settings.json）→ 内置默认。
旧路由名 narrative/decision 自动映射为 analysis/extraction（2026-09-22 三模块改版）。

安全边界：
- 设置文件只保存 key_file 路径；内联提交的密钥写入 RUNTIME/keys/ 下的受限文件；
- 对外接口只回显 key_set/来源，绝不回显密钥内容；
- RUNTIME 目录被 .gitignore 拦截，不进仓库、不进普通导出。
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path
from typing import Any

from .config import RUNTIME, MODEL_BASE_URL_DEFAULT

SETTINGS_PATH = RUNTIME / 'model_settings.json'
KEYS_DIR = RUNTIME / 'keys'
ROUTES = ('extraction', 'analysis')
ROUTE_ALIASES = {'narrative': 'analysis', 'decision': 'extraction'}  # 旧名兼容
FIELDS = ('model', 'base_url', 'protocol', 'key_file', 'vendor', 'reasoning_effort')
EFFORTS = ('low', 'medium', 'high')
DEFAULT_EMBEDDING_SUBDIR = 'models/bge-large-zh-v1.5'


def canonical_route(route: str | None) -> str:
    route = ROUTE_ALIASES.get(route or '', route or '')
    if route not in ROUTES:
        raise ValueError('UNKNOWN_MODEL_ROUTE:' + str(route))
    return route


def _load() -> dict[str, Any]:
    if not SETTINGS_PATH.is_file():
        return {}
    try:
        value = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _migrated() -> dict[str, Any]:
    """读取设置文件并把旧路由名迁移为三角色命名（读时迁移，不重写文件）。"""
    data = _load()
    connections = data.get('connections')
    if not isinstance(connections, dict):
        return data
    for old, new in ROUTE_ALIASES.items():
        if old in connections and new not in connections:
            connections[new] = connections[old]
    return data


def _loopback_host(base: str) -> bool:
    """http 明文仅允许回环/容器内宿主机地址；其余端点必须 https。"""
    try:
        from urllib.parse import urlsplit
        host = (urlsplit(base).hostname or '').lower()
    except ValueError:
        return False
    return host in ('localhost', '127.0.0.1', '::1', '0.0.0.0', 'host.docker.internal')


def _validate_base_url(base: str) -> str | None:
    if not base.startswith(('http://', 'https://')):
        return 'base_url 必须以 http(s):// 开头'
    if '@' in base.split('://', 1)[-1]:
        return 'base_url 不得内嵌凭据'
    if base.startswith('http://') and not _loopback_host(base):
        return '非回环地址必须使用 https://（明文 http 仅允许 localhost/127.0.0.1/::1/host.docker.internal）'
    return None


def _sanitize_overrides(overrides: dict[str, Any] | None) -> dict[str, Any]:
    """请求参数携带的覆盖项安全化（2026-09-21 修复 #4）：

    - key_file 只接受 KEYS_DIR 内的文件名（basename），拒绝任意路径读取；
    - base_url 必须通过 https/回环策略校验，防把密钥发往任意明文端点。
    """
    cleaned = {k: str(v) for k, v in (overrides or {}).items() if k in FIELDS and str(v).strip()}
    if 'key_file' in cleaned:
        name = cleaned['key_file'].strip()
        if name != Path(name).name or name in ('.', '..'):
            raise ValueError('KEY_FILE_OVERRIDE_RESTRICTED: 请求参数中的密钥文件只允许 RUNTIME/keys/ 目录内的文件名')
        cleaned['key_file'] = str(KEYS_DIR / name)
    if 'base_url' in cleaned:
        error = _validate_base_url(cleaned['base_url'])
        if error:
            raise ValueError('BASE_URL_OVERRIDE_INVALID: ' + error)
    if 'reasoning_effort' in cleaned and cleaned['reasoning_effort'] not in EFFORTS:
        raise ValueError('REASONING_EFFORT_INVALID: ' + '/'.join(EFFORTS))
    return cleaned


def _validate_connection(route: str, section: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    protocol = section.get('protocol', 'openai')
    if protocol not in ('openai', 'anthropic'):
        errors.append('protocol 仅支持 openai / anthropic')
    base = str(section.get('base_url', ''))
    if base:
        error = _validate_base_url(base)
        if error:
            errors.append(error)
    if section.get('model') and not str(section['model']).strip():
        errors.append('model 不能为空白')
    if section.get('reasoning_effort') and section['reasoning_effort'] not in EFFORTS:
        errors.append('reasoning_effort 仅支持 ' + '/'.join(EFFORTS))
    from .model_registry import tier_error
    tier = tier_error(route, str(section.get('model', '')))
    if tier:
        errors.append(tier)
    return errors


def save_settings(payload: dict[str, Any]) -> dict[str, Any]:
    """保存连接设置。内联 api_key 写入受限密钥文件，设置文件只存路径。"""
    connections = payload.get('connections')
    if not isinstance(connections, dict) or not connections:
        raise ValueError('INVALID_SETTINGS_SHAPE: 需要 connections 映射')
    cleaned: dict[str, Any] = {'connections': {}, 'vector_model': _load().get('vector_model', {})}
    for raw_route, section in connections.items():
        if section in (None, ''):
            continue
        route = canonical_route(raw_route)
        if not isinstance(section, dict):
            raise ValueError('INVALID_SETTINGS_SECTION:' + route)
        entry = {k: str(section.get(k, '')).strip() for k in FIELDS if section.get(k)}
        errors = _validate_connection(route, entry)
        if errors:
            raise ValueError('INVALID_SETTINGS_SECTION:' + route + ': ' + '；'.join(errors))
        api_key = str(section.get('api_key') or '').strip()
        if api_key:
            KEYS_DIR.mkdir(parents=True, exist_ok=True)
            key_path = KEYS_DIR / (route + '.key')
            key_path.write_text(api_key, encoding='utf-8')
            try:  # 尽力收紧权限（Windows 上可能不完全生效）
                key_path.chmod(stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
            entry['key_file'] = str(key_path)
        if entry.get('key_file'):
            if not Path(entry['key_file']).is_file():
                raise ValueError('KEY_FILE_NOT_FOUND:' + route)
        if entry:
            cleaned['connections'][route] = entry
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2), encoding='utf-8')
    return status()


def resolve(route: str | None = None) -> dict[str, str]:
    """返回某路由的设置文件配置（未配置返回空 dict；旧路由名自动迁移）。"""
    try:
        route = canonical_route(route or 'analysis')
    except ValueError:
        return {}
    data = _migrated().get('connections', {})
    section = data.get(route)
    return {k: str(v) for k, v in (section or {}).items() if k in FIELDS and v}


def status() -> dict[str, Any]:
    """对外只回显生效来源与密钥存在性，绝不回显密钥内容。"""
    def source(field: str, route: str) -> str:
        prefix = 'PHARMA_MODEL_' + route.upper() + '_'
        legacy = {'analysis': 'NARRATIVE', 'extraction': 'DECISION'}.get(route, route.upper())
        env_names = [prefix + field.upper()]
        if field == 'model':
            env_names += ['PHARMA_MODEL', 'PHARMA_MODEL_' + legacy + '_MODEL']
        elif field == 'base_url':
            env_names += ['PHARMA_MODEL_BASE_URL', 'PHARMA_MODEL_' + legacy + '_BASE_URL']
        elif field == 'protocol':
            env_names += ['PHARMA_MODEL_PROTOCOL', 'PHARMA_MODEL_' + legacy + '_PROTOCOL']
        elif field == 'key_file':
            env_names += ['PHARMA_MODEL_KEY_FILE', 'PHARMA_MODEL_' + legacy + '_KEY_FILE']
        elif field == 'reasoning_effort':
            env_names += ['PHARMA_MODEL_REASONING_EFFORT']
        if any(os.getenv(name) for name in env_names if name):
            return 'env'
        if resolve(route).get(field):
            return 'settings'
        return 'default'
    connections = {}
    for route in ROUTES:
        configured = resolve(route)
        from .model_registry import classify_tier
        model = configured.get('model', '')
        connections[route] = {
            'configured': bool(configured),
            'model': model, 'model_tier': classify_tier(model),
            'base_url': configured.get('base_url', ''),
            'protocol': configured.get('protocol', 'openai'),
            'vendor': configured.get('vendor', ''),
            'reasoning_effort': configured.get('reasoning_effort', ''),
            'key_set': bool(configured.get('key_file') and Path(configured['key_file']).is_file()),
            'key_file': configured.get('key_file', ''),
            'sources': {field: source(field, route) for field in FIELDS},
        }
    return {'settings_file': str(SETTINGS_PATH), 'connections': connections,
            'vector_model': vector_status(),
            'notes': ['环境变量优先于本设置文件；两者都未配置时使用内置默认',
                      '数据提取模型为小模型（赛题多模型协作加分项），数据分析模型为大模型（赛题基础项）',
                      '更换生成模型无需重建索引；更换向量模型后由“确认”按钮自动重建知识索引并验证',
                      '容器内 localhost 指向容器自身；连接宿主机服务请使用 host.docker.internal']}


def test_connection(route: str = 'analysis', overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """真实短生成测试：验证连通、身份回显与结构化输出，而非仅探测地址。"""
    from .narrative import ModelGateway
    route = canonical_route(route)
    overrides = _sanitize_overrides(overrides) or None
    gateway = ModelGateway.for_route(route, **(overrides or {})) if overrides else ModelGateway.for_route(route)
    if not gateway.key:
        return {'status': 'NO_KEY', 'reason': '未配置密钥：请先在设置中填写密钥或配置 PHARMA_MODEL_KEY_FILE'}
    import time as _time
    started = _time.monotonic()
    try:
        system = '你是连通性测试器。只返回JSON对象 {"ok": true}。'
        user = '请按系统说明返回。'
        raw, usage, identity = gateway.complete(system, user, operation='settings_test')
    except RuntimeError as exc:
        return {'status': 'FAILED', 'reason': str(exc)[:300], 'model': gateway.model}
    except Exception as exc:  # noqa: BLE001 对用户呈现真实失败原因
        return {'status': 'FAILED', 'reason': type(exc).__name__ + ': ' + str(exc)[:260], 'model': gateway.model}
    elapsed = round(_time.monotonic() - started, 2)
    structured = False
    try:
        structured = isinstance(json.loads(raw), dict)
    except ValueError:
        structured = False
    returned = (identity or {}).get('returned_model')
    return {'status': 'PASS' if structured else 'UNSTRUCTURED',
            'model': gateway.model, 'returned_model': returned,
            'identity_status': (identity or {}).get('identity_status'),
            'structured_output': structured, 'elapsed_seconds': elapsed,
            'usage': usage,
            'reason': '' if structured else '模型未返回JSON对象；结构化输出不满足本系统合同'}


def list_remote_models(route: str = 'analysis', overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """尝试拉取模型列表；失败时明确提示可手填，绝不阻塞设置。"""
    import httpx
    route = canonical_route(route)
    gateway_overrides = _sanitize_overrides(overrides)
    resolved = resolve(route) or {k: v for k, v in gateway_overrides.items()}
    base = (gateway_overrides.get('base_url') or resolved.get('base_url')
            or os.getenv('PHARMA_MODEL_BASE_URL', MODEL_BASE_URL_DEFAULT)).rstrip('/')
    key = ''
    key_file = gateway_overrides.get('key_file') or resolved.get('key_file') or os.getenv('PHARMA_MODEL_KEY_FILE')
    if key_file and Path(key_file).is_file():
        key = Path(key_file).read_text(encoding='utf-8').strip()
    key = key or os.getenv('PHARMA_API_KEY', '')
    try:
        with httpx.Client(timeout=10, trust_env=False) as client:
            response = client.get(base + '/models', headers={'Authorization': 'Bearer ' + key})
        response.raise_for_status()
        data = response.json().get('data', [])
        from .model_registry import classify_tier
        return {'status': 'OK', 'models': [item.get('id') for item in data if item.get('id')][:100],
                'tiers': {item.get('id'): classify_tier(item.get('id') or '') for item in data if item.get('id')}}
    except Exception as exc:  # noqa: BLE001
        return {'status': 'UNAVAILABLE', 'reason': type(exc).__name__ + ': ' + str(exc)[:200],
                'hint': '自动获取失败不影响使用：可在“模型型号”中手动填写'}


# ---- 向量模型（本地 ONNX，无 API 选项） ----

def embedding_dir() -> Path:
    """向量模型目录解析：显式环境变量 → 设置文件 vector_model.path → 内置默认。"""
    env = os.environ.get('PHARMA_EMBEDDING_DIR', '').strip()
    if env:
        return Path(env)
    configured = _migrated().get('vector_model', {})
    path = str(configured.get('path', '')).strip() if isinstance(configured, dict) else ''
    if path:
        return Path(path)
    return RUNTIME / DEFAULT_EMBEDDING_SUBDIR


def embedding_fingerprint(model_dir: Path | None = None) -> str:
    """向量模型资产指纹：进入知识版本，切换模型自动触发重建。"""
    directory = Path(model_dir) if model_dir else embedding_dir()
    digest = hashlib.sha256()
    try:
        for name in ('model_quantized.onnx', 'onnx/model_quantized.onnx', 'model.onnx',
                     'tokenizer.json', 'config.json'):
            target = directory / name
            if target.is_file():
                digest.update(name.encode())
                digest.update(hashlib.sha256(target.read_bytes()).digest())
    except OSError:
        from .knowledge import EMBEDDING_SHA
        return EMBEDDING_SHA
    return digest.hexdigest()[:40]


def set_vector_model(path: str) -> dict[str, Any]:
    """记录向量模型切换（向量切换流水线调用；环境变量存在时拒绝写入）。"""
    if os.environ.get('PHARMA_EMBEDDING_DIR', '').strip():
        raise ValueError('PHARMA_EMBEDDING_DIR_ENV_TAKES_PRIORITY')
    data = _load()
    data['vector_model'] = {'path': str(Path(path)), 'name': Path(path).name}
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return vector_status()


def clear_vector_model() -> None:
    data = _load()
    data.pop('vector_model', None)
    SETTINGS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def vector_status() -> dict[str, Any]:
    """当前本地向量模型信息（预填充展示与切换按钮的默认值）。"""
    directory = embedding_dir()
    files = {name: (directory / name).is_file() for name in
             ('model_quantized.onnx', 'onnx/model_quantized.onnx', 'model.onnx', 'tokenizer.json', 'config.json')}
    onnx_ok = files.get('model_quantized.onnx') or files.get('onnx/model_quantized.onnx') or files.get('model.onnx')
    dim = None
    config_path = directory / 'config.json'
    if config_path.is_file():
        try:
            config = json.loads(config_path.read_text(encoding='utf-8'))
            for key in ('hidden_size', 'd_model'):
                if isinstance(config.get(key), int):
                    dim = config['hidden_size'] if key == 'hidden_size' else config['d_model']
                    break
            name = config.get('_name_or_path') or ''
        except (OSError, ValueError):
            name = ''
    else:
        name = ''
    return {'mode': 'local', 'name': directory.name or str(directory), 'path': str(directory),
            'is_default': str(directory).replace('\\', '/') == str(RUNTIME / DEFAULT_EMBEDDING_SUBDIR).replace('\\', '/'),
            'onnx_present': bool(onnx_ok), 'tokenizer_present': bool(files.get('tokenizer.json')),
            'files': files, 'dimension': dim, 'model_source': name,
            'fingerprint': embedding_fingerprint(directory),
            'note': '向量模型仅支持本地推理（CPU ONNX）；切换路径后点击“确认”完成适配与知识库重建'}
