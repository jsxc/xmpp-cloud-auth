# Checks whether the isuser() function works as it should
# Stubs the cloud_request() functions for these tests
from xclib.sigcloud import sigcloud
from xclib import xcauth
from xclib.check import assertEqual

def setup_module():
    global xc, sc
    xc = xcauth(domain_db={
            b'xdomain': b'99999\thttps://remotehost\tydomain\t',
            b'udomain': b'8888\thttps://oldhost\t',
        },
        default_url='https://localhost', default_secret='01234')
    sc = sigcloud(xc, 'user1', 'domain1')

def teardown_module():
    pass

def sc_timeout(data):
    assertEqual(data['operation'], 'isuser')
    assertEqual(data['username'], 'user1')
    assertEqual(data['domain'], 'domain1')
    return (False, None, 'Timeout', None)
def test_timeout():
    sc.verbose_cloud_request = sc_timeout
    assertEqual(sc.isuser(), None)

def sc_404(data):
    return (False, 404, None, None)
def test_http404():
    sc.verbose_cloud_request = sc_404
    assertEqual(sc.isuser(), None)

def sc_500json(data):
    return (False, 500, {'result': 'failure'}, None)
def test_http500json():
    sc.verbose_cloud_request = sc_500json
    assertEqual(sc.isuser(), None)

def sc_malformed(data):
    return (True, None, {'result': 'success'}, None)
def test_malformed():
    sc.verbose_cloud_request = sc_malformed
    assertEqual(sc.isuser(), None)

def sc_success(data):
    return (True, None, {
        'result': 'success',
        'data': {
            'isUser': '1'
        }}, 'fake body')
def test_success():
    sc.verbose_cloud_request = sc_success
    assertEqual(sc.isuser(), True)

def sc_xdomain(data):
    assertEqual(data['operation'], 'isuser')
    assertEqual(data['username'], 'xuser')
    assertEqual(data['domain'], 'ydomain')
    return (True, None, {
        'result': 'success',
        'data': {
            'isUser': '1'
        }}, 'fake body')
def test_xdomain():
    sc = sigcloud(xc, 'xuser', 'xdomain')
    sc.verbose_cloud_request = sc_xdomain
    assertEqual(sc.isuser(), True)

def test_domain_upgrade():
    sc = sigcloud(xc, 'uuser', 'udomain')
    sc.verbose_cloud_request = sc_success
    assertEqual(sc.isuser(), True)
