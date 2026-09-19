import pytest
from pharma.local_validation import require_loopback,require_simulation,NoRedirect
@pytest.mark.parametrize('url',['https://example.org','http://127.0.0.1.evil','http://user:pass@localhost','ftp://localhost','http://0.0.0.0'])
def test_external_confirmation_refused_before_request(url):
    with pytest.raises(ValueError):require_loopback(url)
@pytest.mark.parametrize('url',['http://127.0.0.1:8765','http://localhost:8765','http://[::1]:8765'])
def test_loopback_supported(url):assert require_loopback(url)==url

def test_requires_explicit_server_simulator_and_no_redirects():
    with pytest.raises(ValueError):require_simulation({'simulation':True})
    require_simulation({'simulation':True,'rpa_mode':'local_simulator','rpa_base_url':'http://127.0.0.1:8090'})
    with pytest.raises(ValueError):NoRedirect().redirect_request(None,None,302,'',{},'https://external.invalid')
