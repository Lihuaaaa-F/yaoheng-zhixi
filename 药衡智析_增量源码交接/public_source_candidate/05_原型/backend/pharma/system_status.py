"""顶栏状态的真实来源：部署配置、无凭据网络探测、已发布数据时间。"""
from datetime import datetime, timezone
import json
import os
import sqlite3
import threading
import time
from urllib.parse import urlsplit

_network_lock = threading.Lock()
_network_cache = {}


def deployment_status():
    configured = os.getenv('PHARMA_DEPLOYMENT_MODE', '').strip().lower()
    mode = configured if configured in ('local', 'cloud') else 'local'
    return {'mode': mode, 'label': '云端运行' if mode == 'cloud' else '本地运行',
            'source': 'configuration' if configured in ('local', 'cloud') else 'local_default',
            'detail': '部署位置由服务部署配置申明；Docker 容器本身不等于云端。'}


def network_status():
    """最多每分钟探测一次；HTTP 可达不等于模型账号可用。不发送任何密钥/业务资料。"""
    target = os.getenv('PHARMA_NETWORK_PROBE_URL', 'https://open.bigmodel.cn').strip()
    if not target:
        return {'status': 'unverified', 'checked_at': None, 'target': None, 'detail': '未启用外网探测。'}
    try:parts = urlsplit(target)
    except ValueError:
        return {'status': 'unverified', 'checked_at': None, 'target': None, 'detail': '网络探测地址配置无效，未发起请求。'}
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        return {'status': 'unverified', 'checked_at': None, 'target': None, 'detail': '网络探测地址配置无效，未发起请求。'}
    with _network_lock:
        cached = _network_cache.get(target)
        if cached and time.monotonic()-cached[0] < 60:
            return {**cached[1], 'cached': True}
        import httpx
        at = datetime.now(timezone.utc).isoformat()
        result = {'status': 'unreachable', 'checked_at': at, 'target': parts.hostname,
                  'detail': '探测站点未响应；不据此断言所有网络都已断开。'}
        try:
            response = httpx.head(target, timeout=httpx.Timeout(4, connect=3), follow_redirects=False)
            result.update(status='reachable', http_status=response.status_code,
                          detail='探测站点可达；这不代表模型密钥、额度或所有外部服务可用。')
        except (httpx.HTTPError, OSError, ImportError, ValueError):
            pass
        _network_cache[target] = (time.monotonic(), result)
        return {**result, 'cached': False}


def data_status(context_id):
    from .industry import catalog
    from .ingestion import SNAPSHOTS
    from .data_import import IMPORT_DB
    result = {'updated_at': None, 'basis': '暂无发布记录', 'latest_period': None}
    if not context_id:
        return result
    try:
        options = catalog(context_id)
        result['latest_period'] = (options.get('months') or [None])[-1]
        if context_id == 'pharmaceutical:competition':
            current = SNAPSHOTS/'current.json'
            if current.is_file():
                manifest = json.loads(current.read_text(encoding='utf-8'))
                result.update(updated_at=manifest.get('created_at'), basis='当前数据快照首次成功载入时间；不是业务发生日期')
        elif IMPORT_DB.is_file():
            with sqlite3.connect(f'file:{IMPORT_DB}?mode=ro', uri=True) as db:
                rows = db.execute("SELECT meta FROM imports WHERE kind='business' AND "
                                  "(json_extract(meta,'$.published.context_id')=? OR json_extract(meta,'$.parsed.context_id')=?)",
                                  (context_id, context_id)).fetchall()
            dates = []
            for row in rows:
                meta = json.loads(row[0])
                stamp = meta.get('published', {}).get('published_at') or meta.get('parsed', {}).get('at')
                if stamp:
                    dates.append(datetime.fromisoformat(stamp))
            if dates:
                result.update(updated_at=max(dates).isoformat(), basis='当前数据范围最近一次成功发布的时间')
    except (ValueError, KeyError, OSError, sqlite3.Error):
        result['basis'] = '当前数据范围尚无可核验的更新时间'
    return result


def status(context_id):
    return {'deployment': deployment_status(), 'network': network_status(),
            'data': data_status(context_id), 'checked_at': datetime.now(timezone.utc).isoformat()}
