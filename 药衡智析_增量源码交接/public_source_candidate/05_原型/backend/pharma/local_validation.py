"""Preflight for automated confirmations; product confirmations remain user-driven."""
import ipaddress
import os
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, build_opener, ProxyHandler

def require_loopback(url):
    parsed=urlsplit(url)
    # Docker 部署显式opt-in：仅当模拟模式开启且主机名与声明的内部模拟服务
    # 完全一致时放行（PHARMA_RPA_INTERNAL_SIMULATOR=rpa）。默认不设置该变量，
    # 行为与此前完全一致：仅回环地址可通过。
    internal_name=os.getenv('PHARMA_RPA_INTERNAL_SIMULATOR','').strip()
    internal_ok=bool(internal_name) and parsed.hostname==internal_name and os.getenv('PHARMA_RPA_SIMULATION')=='1'
    try:local=ipaddress.ip_address(parsed.hostname or '').is_loopback
    except ValueError:local=parsed.hostname=='localhost'
    if parsed.scheme not in ('http','https') or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('AUTOMATION_REQUIRES_LOOPBACK_URL')
    if not (local or internal_ok):raise ValueError('AUTOMATION_REQUIRES_LOOPBACK_URL')
    return url.rstrip('/')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ValueError('AUTOMATION_REDIRECT_FORBIDDEN')

def local_opener():return build_opener(ProxyHandler({}),NoRedirect())

def require_simulation(health):
    if health.get('simulation') is not True or health.get('rpa_mode')!='local_simulator':
        raise ValueError('AUTOMATION_REQUIRES_SERVER_SIMULATION')
    require_loopback(health.get('rpa_base_url',''))
