"""模型连接设置：API 与后台任务读取同一份配置。

模型角色（"模型配置"模块）：
  extraction 数据提取模型（小模型，赛题加分项）；analysis 数据分析模型（大模型，
  赛题基础项）；assistant 独立助手；vector 向量模型（本地 ONNX）。

解析优先级（与既有环境变量语义兼容）：
  显式构造参数 → 路由环境变量 → 全局环境变量 → 设置文件 → 默认。
  助手没有全局回退；各路由保存的密钥只绑定本路由服务地址。
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
import tempfile
import math
from pathlib import Path
from typing import Any

from .config import RUNTIME, MODEL_BASE_URL_DEFAULT

SETTINGS_PATH = RUNTIME / 'model_settings.json'
KEYS_DIR = RUNTIME / 'keys'
ROUTES = ('extraction', 'analysis', 'assistant')
ROUTE_ALIASES = {'narrative': 'analysis', 'decision': 'extraction'}  # 旧名兼容
FIELDS = ('model', 'base_url', 'protocol', 'key_file', 'vendor', 'reasoning_effort',
          'temperature', 'top_p', 'max_tokens', 'timeout_seconds', 'auth_mode')
METADATA_FIELDS = ('model_context_windows',)
EFFORTS = ('', 'none', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max')
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
    from urllib.parse import urlsplit
    try:
        parts = urlsplit(base)
        if not parts.hostname or parts.query or parts.fragment or parts.port == 0:
            return 'base_url 必须为不含查询参数、片段和凭据的服务地址'
    except ValueError:
        return 'base_url 格式无效'
    if not base.startswith(('http://', 'https://')):
        return 'base_url 必须以 http(s):// 开头'
    if '@' in base.split('://', 1)[-1]:
        return 'base_url 不得内嵌凭据'
    if base.startswith('http://') and not _loopback_host(base):
        return '非回环地址必须使用 https://（明文 http 仅允许 localhost/127.0.0.1/::1/host.docker.internal）'
    return None


def _sanitize_overrides(overrides: dict[str, Any] | None) -> dict[str, Any]:
    """仅允许受控字段。api_key 仅用于本次请求，不写设置、不进 URL。"""
    cleaned = {}
    for k, v in (overrides or {}).items():
        if k not in (*FIELDS, *METADATA_FIELDS, 'api_key'):
            continue
        if k == 'model_context_windows':
            if not isinstance(v, dict) or len(v) > 100:
                raise ValueError('MODEL_CONTEXT_WINDOWS_INVALID: 最多提供100个型号的窗口信息')
            windows = {}
            for model_id, window in v.items():
                if (not isinstance(model_id, str) or not 1 <= len(model_id) <= 160
                        or model_id != model_id.strip() or any(ord(c) < 32 for c in model_id)):
                    raise ValueError('MODEL_CONTEXT_WINDOWS_INVALID: 型号须为1至160字符的非空文本')
                if window is not None and (isinstance(window, bool) or not isinstance(window, int)
                                           or not 1024 <= window <= 2000000):
                    raise ValueError('MODEL_CONTEXT_WINDOWS_INVALID: 窗口须为1024至2000000的整数，或null撤销')
                windows[model_id] = window
            cleaned[k] = windows
        elif k in ('temperature', 'top_p', 'max_tokens', 'timeout_seconds'):
            if v is None or v == '':
                if k in ('temperature', 'top_p'):
                    cleaned[k] = None
                continue
            try:
                number = float(v)
                if isinstance(v, bool) or not math.isfinite(number):
                    raise ValueError()
                low, high = {'temperature': (0, 2), 'top_p': (0, 1),
                             'max_tokens': (1, 32768), 'timeout_seconds': (5, 180)}[k]
                if not low <= number <= high or (k == 'max_tokens' and not number.is_integer()):
                    raise ValueError()
                cleaned[k] = int(number) if k == 'max_tokens' else number
            except (TypeError, ValueError):
                raise ValueError('MODEL_PARAMETER_INVALID:' + k) from None
        elif v is not None:
            value = str(v).strip()
            if value or k == 'reasoning_effort':
                cleaned[k] = value
    if 'key_file' in cleaned:
        name = cleaned['key_file'].strip()
        if name != Path(name).name or name in ('.', '..') or '/' in name or '\\' in name or ':' in name:
            raise ValueError('KEY_FILE_OVERRIDE_RESTRICTED: 请求参数中的密钥文件只允许 RUNTIME/keys/ 目录内的文件名')
        key_path = KEYS_DIR / name
        if key_path.is_symlink() or key_path.resolve().parent != KEYS_DIR.resolve():
            raise ValueError('KEY_FILE_OVERRIDE_RESTRICTED: 密钥文件不能是符号链接')
        cleaned['key_file'] = str(key_path)
    if 'base_url' in cleaned:
        error = _validate_base_url(cleaned['base_url'])
        if error:
            raise ValueError('BASE_URL_OVERRIDE_INVALID: ' + error)
    if 'reasoning_effort' in cleaned and cleaned['reasoning_effort'] not in EFFORTS:
        raise ValueError('REASONING_EFFORT_INVALID: ' + '/'.join(EFFORTS))
    if len(cleaned.get('api_key', '')) > 10 * 1024 or any(c in cleaned.get('api_key', '') for c in ('\r', '\n')):
        raise ValueError('API_KEY_INVALID: 密钥应为单行短文本')
    if cleaned.get('protocol', 'openai') not in ('openai', 'anthropic'):
        raise ValueError('MODEL_PROTOCOL_INVALID: 仅支持 openai / anthropic')
    if cleaned.get('auth_mode', 'auto') not in ('auto', 'required', 'none'):
        raise ValueError('MODEL_AUTH_MODE_INVALID')
    if cleaned.get('auth_mode') == 'none' and cleaned.get('base_url') and not _loopback_host(cleaned['base_url']):
        raise ValueError('MODEL_AUTH_MODE_INVALID: 无鉴权模式仅允许本地回环或容器宿主机地址')
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
    return errors


def _atomic_write(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # 临时文件从创建时起就是 0600，读者只看到完整旧版或完整新版。
    fd, name = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    with os.fdopen(fd, 'w', encoding='utf-8') as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(name, path)


def _valid_key_file(path: str, route: str) -> None:
    key_path = Path(path)
    if not key_path.is_file():
        raise ValueError('KEY_FILE_NOT_FOUND:' + route)
    if key_path.stat().st_size > 10 * 1024:
        raise ValueError('KEY_FILE_TOO_LARGE:' + route + '（密钥文件应小于 10KB）')


def save_settings(payload: dict[str, Any]) -> dict[str, Any]:
    """PATCH 合并；空 api_key 保持原钥；clear_api_key 撤销引用但不删除文件。"""
    connections = payload.get('connections')
    if not isinstance(connections, dict) or not connections:
        raise ValueError('INVALID_SETTINGS_SHAPE: 需要 connections 映射')
    from .locks import exclusive
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    updates = {}
    for raw_route, section in connections.items():
        if section in (None, ''):
            continue
        route = canonical_route(raw_route)
        if not isinstance(section, dict):
            raise ValueError('INVALID_SETTINGS_SECTION:' + route)
        if section.get('clear_api_key') not in (None, True, False):
            raise ValueError('CLEAR_API_KEY_INVALID')
        try:
            entry = _sanitize_overrides(section)
        except ValueError as exc:
            raise ValueError('INVALID_SETTINGS_SECTION:' + route + ': ' + str(exc)) from None
        errors = _validate_connection(route, entry)
        if errors:
            raise ValueError('INVALID_SETTINGS_SECTION:' + route + ': ' + '；'.join(errors))
        if entry.get('key_file'):
            _valid_key_file(entry['key_file'], route)
        updates[route] = (entry, bool(section.get('clear_api_key')))
    with exclusive(SETTINGS_PATH.parent / 'model-settings.lock'):
        cleaned = _migrated()
        stored = cleaned.setdefault('connections', {})
        for route, (entry, clear_key) in updates.items():
            previous = dict(stored.get(route) or {})
            merged = {**previous, **entry}
            if merged.get('auth_mode') == 'none' and not _loopback_host(merged.get('base_url', '')):
                raise ValueError('MODEL_AUTH_MODE_INVALID: 无鉴权模式仅允许本地地址')
            # 端点变更不能静默携带旧密钥；重输凭据即可确认新绑定。
            destination_changed = any(k in entry and entry[k] != previous.get(k)
                                      for k in ('base_url', 'protocol'))
            windows = {} if destination_changed else dict(previous.get('model_context_windows') or {})
            for model_id, window in entry.get('model_context_windows', {}).items():
                if window is None:
                    windows.pop(model_id, None)
                else:
                    windows[model_id] = window
            if len(windows) > 100:
                raise ValueError('MODEL_CONTEXT_WINDOWS_INVALID: 同一连接最多保存100个型号的窗口信息')
            if previous.get('key_file') and destination_changed and not (entry.get('api_key') or entry.get('key_file') or clear_key):
                raise ValueError('CREDENTIAL_REENTRY_REQUIRED: 更换服务地址或协议后请重新填写密钥；本地无鉴权请明确清除密钥')
        for route, (entry, clear_key) in updates.items():
            previous = dict(stored.get(route) or {})
            api_key = entry.pop('api_key', '')
            destination_changed = any(k in entry and entry[k] != previous.get(k)
                                      for k in ('base_url', 'protocol'))
            # 容量属于此连接的具体型号；更换服务后不冒用旧服务的窗口。
            if destination_changed:
                previous['model_context_windows'] = {}
            if 'model_context_windows' in entry:
                windows = dict(previous.get('model_context_windows') or {})
                for model_id, window in entry.pop('model_context_windows').items():
                    if window is None:
                        windows.pop(model_id, None)
                    else:
                        windows[model_id] = window
                previous['model_context_windows'] = windows
            if clear_key:
                previous.pop('key_file', None)
                previous['key_disabled'] = True
            if api_key:
                KEYS_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
                # 每次轮换使用新文件，失败时旧设置仍能读到旧凭据。
                import uuid
                key_path = KEYS_DIR / (route + '-' + uuid.uuid4().hex + '.key')
                _atomic_write(key_path, api_key)
                entry['key_file'] = str(key_path)
            if entry.get('key_file'):
                previous.pop('key_disabled', None)
            previous.update(entry)
            stored[route] = previous
        _atomic_write(SETTINGS_PATH, json.dumps(cleaned, ensure_ascii=False, indent=2))
    return status()


def resolve(route: str | None = None) -> dict[str, Any]:
    """返回某路由的设置文件配置（未配置返回空 dict；旧路由名自动迁移）。"""
    try:
        route = canonical_route(route or 'analysis')
    except ValueError:
        return {}
    data = _migrated().get('connections', {})
    section = data.get(route)
    return {k: v for k, v in (section or {}).items() if k in (*FIELDS, *METADATA_FIELDS, 'key_disabled')}


def context_window_metadata(route: str, model: str, base_url: str | None = None,
                            protocol: str | None = None) -> dict[str, Any]:
    """用户按服务商说明申报的型号容量；未知即未知，不猜测官方窗口。"""
    configured = resolve(route)
    windows = configured.get('model_context_windows') or {}
    window = windows.get(model) if isinstance(windows, dict) else None
    endpoint_matches = ((base_url is None or base_url.rstrip('/') == str(configured.get('base_url') or '').rstrip('/'))
                        and (protocol is None or protocol == configured.get('protocol', 'openai')))
    if (not endpoint_matches or isinstance(window, bool) or not isinstance(window, int)
            or not 1024 <= window <= 2000000):
        window = None
    return {'model': model, 'context_window': window,
            'source': 'user_configured' if window is not None else 'unknown'}


def status() -> dict[str, Any]:
    """对外只回显生效来源与密钥存在性，绝不回显密钥内容。"""
    def source(field: str, route: str) -> str:
        prefix = 'PHARMA_MODEL_' + route.upper() + '_'
        legacy = {'analysis': 'NARRATIVE', 'extraction': 'DECISION'}.get(route, route.upper())
        env_names = [prefix + field.upper()]
        if route == 'assistant':
            if any(os.getenv(name) for name in env_names):
                return 'env'
            return 'settings' if field in resolve(route) else 'default'
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
        from .narrative import ModelGateway
        gateway = ModelGateway.for_route(route)
        model = configured.get('model', '')
        connections[route] = {
            'configured': bool(configured),
            'model': model, 'model_tier': classify_tier(model),
            'base_url': configured.get('base_url', ''),
            'protocol': configured.get('protocol', 'openai'),
            'vendor': configured.get('vendor', ''),
            'reasoning_effort': configured.get('reasoning_effort', ''),
            'temperature': configured.get('temperature'), 'top_p': configured.get('top_p'),
            'max_tokens': configured.get('max_tokens', 8192),
            'timeout_seconds': configured.get('timeout_seconds', 90),
            'auth_mode': configured.get('auth_mode', 'auto'),
            'model_context_windows': configured.get('model_context_windows', {}),
            'context_window_metadata': context_window_metadata(route, gateway.model, gateway.base_url, gateway.provider),
            'key_set': bool(gateway.key or (configured.get('key_file') and Path(configured['key_file']).is_file())),
            'effective_key_set': bool(gateway.key),
            'key_file': Path(configured['key_file']).name if configured.get('key_file') else '',
            'independent': route == 'assistant', 'available': gateway.available,
            'effective': {'model': gateway.model, 'base_url': gateway.base_url,
                          'protocol': gateway.provider, **gateway.generation_parameters},
            'parameter_warnings': gateway.parameter_warnings + gateway.parameter_errors,
            'sources': {field: source(field, route) for field in FIELDS},
        }
    return {'settings_file': SETTINGS_PATH.name, 'connections': connections,
            'vector_model': vector_status(),
            'notes': ['环境变量优先于本设置文件；两者都未配置时使用内置默认',
                      '模型档位仅作建议；助手独立配置，不借用报告或提取模型的密钥',
                      '更换生成模型无需重建索引；更换向量模型后由“确认”按钮自动重建知识索引并验证',
                      '容器内 localhost 指向容器自身；连接宿主机服务请使用 host.docker.internal']}


def _candidate_gateway(route: str, overrides: dict[str, Any] | None):
    from .narrative import ModelGateway
    candidate = _sanitize_overrides(overrides)
    current = ModelGateway.for_route(route)
    changed = (candidate.get('base_url', current.base_url).rstrip('/') != current.base_url
               or candidate.get('protocol', current.provider) != current.provider)
    if changed and not (candidate.get('api_key') or candidate.get('key_file')):
        base = candidate.get('base_url', current.base_url)
        if not _loopback_host(base):
            raise ValueError('CREDENTIAL_REENTRY_REQUIRED: 测试新服务地址前请填写该地址的密钥，不会发送原服务密钥')
        candidate['api_key'] = ''  # 本地无鉴权：显式禁止沿用任何旧钥
    return ModelGateway.for_route(route, **{k: v for k, v in candidate.items() if k not in ('vendor', *METADATA_FIELDS)})


def test_connection(route: str = 'analysis', overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """真实短生成测试：验证连通、身份回显与结构化输出，而非仅探测地址。"""
    from .narrative import ModelGateway
    route = canonical_route(route)
    gateway = _candidate_gateway(route, overrides)
    if not gateway.configured:
        return {'status': 'NOT_CONFIGURED', 'reason': '请填写本角色的模型型号和服务地址'}
    if not gateway.available:
        return {'status': 'NO_KEY', 'reason': '请填写本角色的 API 密钥；本地无鉴权服务可留空'}
    import time as _time
    started = _time.monotonic()
    try:
        system = '你是连通性测试器。只返回JSON对象 {"ok": true}。'
        user = '请按系统说明返回。'
        raw, usage, identity = gateway.complete(system, user, operation='settings_test')
    except RuntimeError as exc:
        reason = str(exc).replace(gateway.key, '[已隐藏]') if gateway.key else str(exc)
        return {'status': 'FAILED', 'reason': reason[:300], 'model': gateway.model}
    except Exception as exc:  # noqa: BLE001 对用户呈现真实失败原因
        import httpx
        reason = ('服务返回 HTTP ' + str(exc.response.status_code) if isinstance(exc, httpx.HTTPStatusError)
                  else '连接或响应失败：' + type(exc).__name__)
        return {'status': 'FAILED', 'reason': reason, 'model': gateway.model}
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
            'parameter_warnings': gateway.parameter_warnings,
            'generation_parameters': gateway.generation_parameters,
            'usage': usage,
            'reason': '' if structured else '模型未返回JSON对象；结构化输出不满足本系统合同'}


def list_remote_models(route: str = 'analysis', overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """尝试拉取模型列表；失败时明确提示可手填，绝不阻塞设置。"""
    import httpx
    route = canonical_route(route)
    gateway = _candidate_gateway(route, overrides)
    base = gateway.base_url
    if not base or (not gateway.key and not _loopback_host(base)):
        return {'status': 'UNAVAILABLE', 'reason': '请填写本角色服务地址与密钥', 'hint': '仍可手动填写模型 ID'}
    try:
        with httpx.Client(timeout=10, trust_env=False) as client:
            response = client.get(base + '/models', headers=gateway._headers(), follow_redirects=False)
        response.raise_for_status()
        data = response.json().get('data', [])
        from .model_registry import classify_tier
        return {'status': 'OK', 'models': [item.get('id') for item in data if item.get('id')][:100],
                'tiers': {item.get('id'): classify_tier(item.get('id') or '') for item in data if item.get('id')}}
    except Exception as exc:  # noqa: BLE001
        return {'status': 'UNAVAILABLE', 'reason': '模型列表不可用：' + type(exc).__name__,
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
    from .locks import exclusive
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with exclusive(SETTINGS_PATH.parent / 'model-settings.lock'):
        data = _load()
        data['vector_model'] = {'path': str(Path(path)), 'name': Path(path).name}
        _atomic_write(SETTINGS_PATH, json.dumps(data, ensure_ascii=False, indent=2))
    return vector_status()


def clear_vector_model() -> None:
    from .locks import exclusive
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with exclusive(SETTINGS_PATH.parent / 'model-settings.lock'):
        data = _load()
        data.pop('vector_model', None)
        _atomic_write(SETTINGS_PATH, json.dumps(data, ensure_ascii=False, indent=2))


def _probe_dimension_cached(directory: Path) -> int | None:
    """向量维度惰性探测（带缓存）：默认模型目录无 config.json（Xenova 布局
    常只有 onnx+tokenizer），从 ONNX 输出形状读最后一维；按资产指纹缓存到
    RUNTIME/vector_dimension.json，切换模型自动失效。探测失败返回 None
    （展示层降级为"—"，不影响检索功能）。
    """
    cache = RUNTIME / 'vector_dimension.json'
    fingerprint = embedding_fingerprint(directory)
    try:
        if cache.is_file():
            data = json.loads(cache.read_text(encoding='utf-8'))
            if data.get('fingerprint') == fingerprint:
                return data.get('dimension')
    except (OSError, ValueError):
        pass
    onnx_path = next((directory / n for n in ('model_quantized.onnx', 'onnx/model_quantized.onnx', 'model.onnx')
                      if (directory / n).is_file()), None)
    if onnx_path is None:
        return None
    try:
        import onnxruntime as ort
        options = ort.SessionOptions()
        options.inter_op_num_threads = 1
        options.intra_op_num_threads = 1
        session = ort.InferenceSession(str(onnx_path), sess_options=options,
                                       providers=['CPUExecutionProvider'])
        shape = session.get_outputs()[0].shape
        dimension = shape[-1] if shape and isinstance(shape[-1], int) else None
        if dimension:
            cache.write_text(json.dumps({'fingerprint': fingerprint, 'dimension': dimension}),
                             encoding='utf-8')
        return dimension
    except Exception:
        return None


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
    if dim is None:
        # Xenova 布局无 config.json：从 ONNX 输出形状惰性探测（带指纹缓存）
        dim = _probe_dimension_cached(directory)
    return {'mode': 'local', 'name': directory.name or str(directory), 'path': str(directory),
            'is_default': str(directory).replace('\\', '/') == str(RUNTIME / DEFAULT_EMBEDDING_SUBDIR).replace('\\', '/'),
            'onnx_present': bool(onnx_ok), 'tokenizer_present': bool(files.get('tokenizer.json')),
            'files': files, 'dimension': dim, 'model_source': name,
            'fingerprint': embedding_fingerprint(directory),
            'note': '向量模型仅支持本地推理（CPU ONNX）；切换路径后点击“确认”完成适配与知识库重建'}
