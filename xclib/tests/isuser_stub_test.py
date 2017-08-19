from xclib.sigcloud import sigcloud
from xclib import xcauth

def setup_module():
    global xc, sc
    xc = xcauth(domain_db={
            'xdomain': '99999\thttps://remotehost\tydomain\t',
            'udomain': '8888\thttps://oldhost\t',
        },
        default_url='https://localhost', default_secret='01234')
    sc = sigcloud(xc, 'user1', 'domain1')

def teardown_module():
    pass

def sc_timeout(data):
    assert data['operation'] == 'isuser'
    assert data['username'] == 'user1'
    assert data['domain'] == 'domain1'
    return (False, None, 'Timeout', None)
def test_timeout():
    sc.verbose_cloud_request = sc_timeout
    assert sc.isuser() == False

def sc_404(data):
    return (False, 404, None, None)
def test_http404():
    sc.verbose_cloud_request = sc_404
    assert sc.isuser() == False

def sc_500json(data):
    return (False, 500, {'result': 'failure'}, None)
def test_http500json():
    sc.verbose_cloud_request = sc_500json
    assert sc.isuser() == False

def sc_malformed(data):
    return (True, None, {'result': 'success'}, None)
def test_malformed():
    sc.verbose_cloud_request = sc_malformed
    assert sc.isuser() == False

def sc_success(data):
    return (True, None, {
        'result': 'success',
        'data': {
            'isUser': '1'
        }}, 'fake body')
def test_success():
    sc.verbose_cloud_request = sc_success
    assert sc.isuser() == True

def sc_xdomain(data):
    assert data['operation'] == 'isuser'
    assert data['username'] == 'xuser'
    assert data['domain'] == 'ydomain'
    return (True, None, {
        'result': 'success',
        'data': {
            'isUser': '1'
        }}, 'fake body')
def test_xdomain():
    sc = sigcloud(xc, 'xuser', 'xdomain')
    sc.verbose_cloud_request = sc_xdomain
    assert sc.isuser() == True

def test_domain_upgrade():
    sc = sigcloud(xc, 'uuser', 'udomain')
    sc.verbose_cloud_request = sc_success
    assert sc.isuser() == True
