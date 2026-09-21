"""模型连接设置：API 与后台任务读取同一份配置。

解析优先级（与既有环境变量语义兼容）：
  显式构造参数 → 环境变量 → 本设置文件（RUNTIME/model_settings.json）→ 内置默认。
测试夹具通过环境变量注入配置，因此不受设置文件影响。

安全边界：
- 设置文件只保存 key_file 路径；内联提交的密钥写入 RUNTIME/keys/ 下的受限文件；
- 对外接口只回显 key_set/来源，绝不回显密钥内容；
- RUNTIME 目录被 .gitignore 拦截，不进仓库、不进普通导出。
"""
from __future__ import annotations

import json
import os
import stat
from pathlib import Path
from typing import Any

from .config import RUNTIME, MODEL_BASE_URL_DEFAULT

SETTINGS_PATH = RUNTIME / 'model_settings.json'
KEYS_DIR = RUNTIME / 'keys'
ROUTES = ('narrative', 'decision', 'vector')
FIELDS = ('model', 'base_url', 'protocol', 'key_file')


def _load() -> dict[str, Any]:
    if not SETTINGS_PATH.is_file():
        return {}
    try:
        value = json.loads(SETTINGS_PATH.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


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
    return cleaned


def _validate_connection(section: dict[str, Any]) -> list[str]:
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
    return errors


def save_settings(payload: dict[str, Any]) -> dict[str, Any]:
    """保存连接设置。内联 api_key 写入受限密钥文件，设置文件只存路径。"""
    connections = payload.get('connections')
    if not isinstance(connections, dict) or not connections:
        raise ValueError('INVALID_SETTINGS_SHAPE: 需要 connections 映射')
    cleaned: dict[str, Any] = {'connections': {}}
    for route in ROUTES:
        section = connections.get(route)
        if section in (None, ''):
            continue
        if not isinstance(section, dict):
            raise ValueError('INVALID_SETTINGS_SECTION:' + str(route))
        entry = {k: str(section.get(k, '')).strip() for k in FIELDS if section.get(k)}
        errors = _validate_connection(entry)
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
    """返回某路由的设置文件配置（未配置返回空 dict）。"""
    data = _load().get('connections', {})
    section = data.get(route) if route else data.get('narrative')
    return {k: str(v) for k, v in (section or {}).items() if k in FIELDS and v}


def status() -> dict[str, Any]:
    """对外只回显生效来源与密钥存在性，绝不回显密钥内容。"""
    def source(field: str, route: str) -> str:
        prefix = 'PHARMA_MODEL_' + route.upper() + '_'
        env_names = [prefix + field.upper()] + (['PHARMA_MODEL'] if field == 'model' else []) \
            + (['PHARMA_MODEL_BASE_URL'] if field == 'base_url' else []) \
            + (['PHARMA_MODEL_PROTOCOL'] if field == 'protocol' else []) \
            + (['PHARMA_MODEL_KEY_FILE'] if field == 'key_file' else [])
        if any(os.getenv(name) for name in env_names if name):
            return 'env'
        if resolve(route).get(field):
            return 'settings'
        return 'default'
    connections = {}
    for route in ROUTES:
        configured = resolve(route)
        connections[route] = {
            'configured': bool(configured),
            'model': configured.get('model', ''),
            'base_url': configured.get('base_url', ''),
            'protocol': configured.get('protocol', 'openai'),
            'key_set': bool(configured.get('key_file') and Path(configured['key_file']).is_file()),
            'key_file': configured.get('key_file', ''),
            'sources': {field: source(field, route) for field in FIELDS},
        }
    return {'settings_file': str(SETTINGS_PATH), 'connections': connections,
            'notes': ['环境变量优先于本设置文件；两者都未配置时使用内置默认',
                      '更换生成模型无需重建索引；更换向量模型后需重建知识索引并验证',
                      '容器内 localhost 指向容器自身；连接宿主机服务请使用 host.docker.internal']}


def test_connection(route: str = 'narrative', overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """真实短生成测试：验证连通、身份回显与结构化输出，而非仅探测地址。"""
    from .narrative import ModelGateway
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


def list_remote_models(route: str = 'narrative', overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """尝试拉取模型列表；失败时明确提示可手填，绝不阻塞设置。"""
    import httpx
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
        return {'status': 'OK', 'models': [item.get('id') for item in data if item.get('id')][:100]}
    except Exception as exc:  # noqa: BLE001
        return {'status': 'UNAVAILABLE', 'reason': type(exc).__name__ + ': ' + str(exc)[:200],
                'hint': '自动获取失败不影响使用：可在“模型名称”中手动填写'}
