from xclib.sigcloud import sigcloud
from xclib import xcauth

def setup_module():
    global xc, sc
    xc = xcauth(domain_db={}, default_url='https://localhost', default_secret='01234')
    sc = sigcloud(xc, 'user1', 'domain1')

def teardown_module():
    pass

def sc_timeout(data):
    assert data['operation'] == 'isuser'
    assert data['username'] == 'user1'
    assert data['domain'] == 'domain1'
    return (False, None, 'Timeout', None)
def timeout_test():
    sc.verbose_cloud_request = sc_timeout
    assert sc.isuser() == False

def sc_404(data):
    return (False, 404, None, None)
def http404_test():
    sc.verbose_cloud_request = sc_404
    assert sc.isuser() == False

def sc_500json(data):
    return (False, 500, {'result': 'failure'}, None)
def http500json_test():
    sc.verbose_cloud_request = sc_500json
    assert sc.isuser() == False

def sc_malformed(data):
    return (True, None, {'result': 'success'}, None)
def malformed_test():
    sc.verbose_cloud_request = sc_malformed
    assert sc.isuser() == False

def sc_success(data):
    return (True, None, {
        'result': 'success',
        'data': {
            'isUser': '1'
        }}, '')
def success_test():
    sc.verbose_cloud_request = sc_success
    assert sc.isuser() == True
