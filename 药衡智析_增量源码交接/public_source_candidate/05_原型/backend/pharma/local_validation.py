"""Preflight for automated confirmations; product confirmations remain user-driven."""
import ipaddress
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, build_opener, ProxyHandler

def require_loopback(url):
    parsed=urlsplit(url)
    try:local=ipaddress.ip_address(parsed.hostname or '').is_loopback
    except ValueError:local=parsed.hostname=='localhost'
    if parsed.scheme not in ('http','https') or not local or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError('AUTOMATION_REQUIRES_LOOPBACK_URL')
    return url.rstrip('/')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ValueError('AUTOMATION_REDIRECT_FORBIDDEN')

def local_opener():return build_opener(ProxyHandler({}),NoRedirect())

def require_simulation(health):
    if health.get('simulation') is not True or health.get('rpa_mode')!='local_simulator':
        raise ValueError('AUTOMATION_REQUIRES_SERVER_SIMULATION')
    require_loopback(health.get('rpa_base_url',''))
