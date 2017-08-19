from xclib.sigcloud import sigcloud
from xclib import xcauth

cloud_count = 0

def setup_module():
    global xc, sc
    xc = xcauth(default_url='https://localhost', default_secret='01234',
        bcrypt_rounds=8)
    sc = sigcloud(xc, 'user2', 'domain2', 'pass2')

def teardown_module():
    pass

# Test group 10: Cloud operations (with cloud request stubs)
def sc_params2(data):
    global cloud_count
    cloud_count += 1
    assert data['operation'] == 'auth'
    assert data['username'] == 'user2'
    assert data['domain'] == 'domain2'
    assert data['password'] == 'pass2'
    return (False, None, 'Connection refused', None)
def test_10_params2():
    sc.verbose_cloud_request = sc_params2
    assert sc.auth() == False

def sc_timeout(data):
    global cloud_count
    cloud_count += 1
    return (False, None, 'Timeout', None)
def test_10_timeout():
    sc.verbose_cloud_request = sc_timeout
    assert sc.auth() == False

def sc_404(data):
    global cloud_count
    cloud_count += 1
    return (False, 404, None, None)
def test_10_http404():
    sc.verbose_cloud_request = sc_404
    assert sc.auth() == False

def sc_500json(data):
    global cloud_count
    cloud_count += 1
    return (False, 500, {'result': 'failure'}, None)
def test_10_http500json():
    sc.verbose_cloud_request = sc_500json
    assert sc.auth() == False

def sc_malformed(data):
    global cloud_count
    cloud_count += 1
    return (True, None, {'foo': 'bar'}, None)
def test_10_malformed():
    sc.verbose_cloud_request = sc_malformed
    assert sc.auth() == False

def sc_malformed2(data):
    global cloud_count
    cloud_count += 1
    return (True, None, {'result': 'bar'}, None)
def test_10_malformed2():
    sc.verbose_cloud_request = sc_malformed2
    assert sc.auth() == False

def sc_error(data):
    global cloud_count
    cloud_count += 1
    return (False, 400, {
        'result': 'error',
        }, 'fake body')
def test_10_error():
    sc.verbose_cloud_request = sc_error
    assert sc.auth() == False

def sc_noauth(data):
    global cloud_count
    cloud_count += 1
    return (False, 400, {
        'result': 'error',
        }, 'fake body')
def test_10_noauth():
    sc.verbose_cloud_request = sc_noauth
    assert sc.auth() == False

def sc_success(data):
    global cloud_count
    cloud_count += 1
    return (True, None, {
        'result': 'success',
        }, 'fake body')
def test_10_success():
    sc.verbose_cloud_request = sc_success
    assert len(xc.cache_db) == 0
    assert 'user2:domain2' not in xc.cache_db
    assert sc.auth() == True
    assert 'user2:domain2' in xc.cache_db

# Test group 20: Time-limited tokens
def sc_trap(data):
    assert False # Should not reach out to the cloud
def test_20_token():
    # ./generateTimeLimitedToken tuser tdomain 01234 3600 1000
    sc = sigcloud(xc, 'tuser', 'tdomain',
        'AMydsCzkh8-8vjcb9U2gqV/FZQAAEfg', now=2000)
    sc.verbose_cloud_request = sc_trap

# Test group 30: Cache logic
def test_30_cache():
    sc = sigcloud(xc, 'user3', 'domain3', 'pass3', now=1)

    # Timeout first: No cache entry
    sc.verbose_cloud_request = sc_timeout
    assert sc.auth() == False
    assert 'user3:domain3' not in xc.cache_db

    # Success: Cache entry
    sc.verbose_cloud_request = sc_success
    assert sc.auth() == True
    assert 'user3:domain3' in xc.cache_db
    entry = xc.cache_db['user3:domain3']
    fields = entry.split('\t')
    cachedpw = fields[0]
    assert fields[0].startswith('$2b$08$')
    assert fields[1] == '1'
    assert fields[2] == '1'
    assert fields[3] == '1'

    # Same request a little bit later: Should use cache
    sc.now = 100
    sc.verbose_cloud_request = sc_trap
    assert sc.auth() == True
    entry = xc.cache_db['user3:domain3']
    fields = entry.split('\t')
    assert cachedpw == fields[0] # No password cache update
    assert fields[1] == '1'
    assert fields[2] == '1'
    assert fields[3] == '100'

    # Same request with different password: Should use cloud
    global cloud_count
    cloud_count = 0
    sc.now = 200
    sc.password = 'newpass'
    sc.verbose_cloud_request = sc_success
    assert sc.auth() == True
