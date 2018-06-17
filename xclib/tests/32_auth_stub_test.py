# Check whether the auth() function works as it should
# Stubs the cloud_request() functions for this
from xclib.sigcloud import sigcloud
from xclib import xcauth
from xclib.check import assertEqual

cloud_count = 0

def setup_module():
    global xc, sc
    xc = xcauth(default_url='https://localhost', default_secret='01234',
        bcrypt_rounds=6)
    sc = sigcloud(xc, 'user2', 'domain2', 'pass2')

def teardown_module():
    pass

# Test group 10: Cloud operations (with cloud request stubs)
def sc_params2(data):
    global cloud_count
    cloud_count += 1
    assertEqual(data['operation'], 'auth')
    assertEqual(data['username'], 'user2')
    assertEqual(data['domain'], 'domain2')
    assertEqual(data['password'], 'pass2')
    return (False, None, 'Connection refused', None)
def test_10_params2():
    sc.verbose_cloud_request = sc_params2
    assertEqual(sc.auth(), False)

def sc_timeout(data):
    global cloud_count
    cloud_count += 1
    return (False, None, 'Timeout', None)
def test_10_timeout():
    sc.verbose_cloud_request = sc_timeout
    assertEqual(sc.auth(), False)

def sc_404(data):
    global cloud_count
    cloud_count += 1
    return (False, 404, None, None)
def test_10_http404():
    sc.verbose_cloud_request = sc_404
    assertEqual(sc.auth(), False)

def sc_500json(data):
    global cloud_count
    cloud_count += 1
    return (False, 500, {'result': 'failure'}, None)
def test_10_http500json():
    sc.verbose_cloud_request = sc_500json
    assertEqual(sc.auth(), False)

def sc_malformed(data):
    global cloud_count
    cloud_count += 1
    return (True, None, {'foo': 'bar'}, None)
def test_10_malformed():
    sc.verbose_cloud_request = sc_malformed
    assertEqual(sc.auth(), False)

def sc_malformed2(data):
    global cloud_count
    cloud_count += 1
    return (True, None, {'result': 'bar'}, None)
def test_10_malformed2():
    sc.verbose_cloud_request = sc_malformed2
    assertEqual(sc.auth(), False)

def sc_error(data):
    global cloud_count
    cloud_count += 1
    return (False, 400, {
        'result': 'error',
        }, 'fake body')
def test_10_error():
    sc.verbose_cloud_request = sc_error
    assertEqual(sc.auth(), False)

def sc_noauth(data):
    global cloud_count
    cloud_count += 1
    return (False, 400, {
        'result': 'error',
        }, 'fake body')
def test_10_noauth():
    sc.verbose_cloud_request = sc_noauth
    assertEqual(sc.auth(), False)

def sc_success(data):
    global cloud_count
    cloud_count += 1
    return (True, None, {
        'result': 'success',
        }, 'fake body')
def test_10_success():
    sc.verbose_cloud_request = sc_success
    assertEqual(len(xc.cache_db), 0)
    assert b'user2:domain2' not in xc.cache_db
    assertEqual(sc.auth(), True)
    assert b'user2:domain2' in xc.cache_db

# Test group 20: Time-limited tokens
def sc_trap(data):
    assert False # Should not reach out to the cloud
def test_20_token_success():
    # ./generateTimeLimitedToken tuser tdomain 01234 3600 1000
    sc = sigcloud(xc, 'tuser', 'tdomain',
        'AMydsCzkh8-8vjcb9U2gqV/FZQAAEfg', now=2000)
    sc.verbose_cloud_request = sc_trap
    assertEqual(sc.auth(), True)
    assert b'tuser:tdomain' not in xc.cache_db

def test_20_token_fail():
    # ./generateTimeLimitedToken tuser tdomain 01234 3600 1000
    sc = sigcloud(xc, 'tuser', 'tdomain',
        'AMydsCzkh8-8vjcb9U2gqV/FZQAAEfg', now=5000)
    sc.verbose_cloud_request = sc_noauth
    global cloud_count
    cloud_count = 0
    assertEqual(sc.auth(), False)
    assertEqual(cloud_count, 1)

def test_20_token_version():
    # Wrong version
    sc = sigcloud(xc, 'tuser', 'tdomain',
        'BMydsCzkh8-8vjcb9U2gqV/FZQAAEfg', now=5000)
    sc.verbose_cloud_request = sc_noauth
    global cloud_count
    cloud_count = 0
    assertEqual(sc.auth(), False)
    assertEqual(cloud_count, 1)

# Test group 30: Cache logic
def test_30_cache():
    global cloud_count
    cloud_count = 0
    sc = sigcloud(xc, 'user3', 'domain3', 'pass3', now=1)

    # Timeout first: No cache entry
    sc.verbose_cloud_request = sc_timeout
    assertEqual(sc.auth(), False)
    assert b'user3:domain3' not in xc.cache_db
    assertEqual(cloud_count, 1)

    # Success: Cache entry
    sc.verbose_cloud_request = sc_success
    assertEqual(sc.auth(), True)
    assert b'user3:domain3' in xc.cache_db
    entry = xc.cache_db[b'user3:domain3']
    fields = entry.split('\t')
    cachedpw = fields[0]
    assert fields[0].startswith('$2b$06$')
    assertEqual(fields[1], '1')
    assertEqual(fields[2], '1')
    assertEqual(fields[3], '1')
    assertEqual(cloud_count, 2)

    # Same request a little bit later: Should use cache (and note it)
    sc.now = 100
    sc.verbose_cloud_request = sc_trap
    assertEqual(sc.auth(), True)
    entry = xc.cache_db[b'user3:domain3']
    fields = entry.split('\t')
    assertEqual(cachedpw, fields[0]) # No cache password update
    assertEqual(fields[1], '1')
    assertEqual(fields[2], '1')
    assertEqual(fields[3], '100')
    assertEqual(cloud_count, 2)

    # Bad password request
    sc.now = 200
    sc.verbose_cloud_request = sc_noauth
    sc.password = 'badpass'
    assertEqual(sc.auth(), False)
    assertEqual(xc.cache_db[b'user3:domain3'], entry) # Unmodified
    assertEqual(cloud_count, 3)

    # New successful password request again: Should use cloud again
    sc.now = 300
    sc.password = 'newpass'
    sc.verbose_cloud_request = sc_success
    assertEqual(sc.auth(), True)
    entry = xc.cache_db[b'user3:domain3']
    fields = entry.split('\t')
    assert cachedpw != fields[0] # Update cached password
    assertEqual(fields[1], '1')
    assertEqual(fields[2], '300')
    assertEqual(fields[3], '300')
    assertEqual(cloud_count, 4)

    # Token request should not change anything
    # ./generateTimeLimitedToken user3 domain3 01234 3600 1
    sc.password = 'ABbL+6M8K7HGF/vnfaZZi5XFZQAADhE'
    assertEqual(sc.auth(), True)
    assertEqual(xc.cache_db[b'user3:domain3'], entry) # Unmodified
    assertEqual(cloud_count, 4)

    # More than an hour of waiting: Go to the cloud again
    sc.now = 4000
    sc.password = 'newpass'
    assertEqual(sc.auth(), True)
    assert xc.cache_db[b'user3:domain3'] != entry # Updated
    entry = xc.cache_db[b'user3:domain3']
    fields = entry.split('\t')
    assert cachedpw != fields[0] # Update cached password
    assertEqual(fields[1], '1')
    assertEqual(fields[2], '4000')
    assertEqual(fields[3], '4000')
    assertEqual(cloud_count, 5)

    # Another hour has passed, but the server is now unreachable
    sc.now = 8000
    sc.verbose_cloud_request = sc_timeout
    assertEqual(sc.auth(), True)
    entry = xc.cache_db[b'user3:domain3']
    fields = entry.split('\t')
    assert cachedpw != fields[0] # Update cached password
    assertEqual(fields[1], '1')
    assertEqual(fields[2], '4000')
    assertEqual(fields[3], '8000')
    assertEqual(cloud_count, 6)

    # Another request shortly after goes to the cache again
    sc.now = 8100
    assertEqual(sc.auth(), True)
    entry = xc.cache_db[b'user3:domain3']
    fields = entry.split('\t')
    assert cachedpw != fields[0] # Update cached password
    assertEqual(fields[1], '1')
    assertEqual(fields[2], '4000')
    assertEqual(fields[3], '8100')
    assertEqual(cloud_count, 6)

    # Now 46 more requests spaced half an hour apart should all go to the cache
    while sc.now < 4000 + 86400 - 1800:
        sc.now += 1800
        assertEqual(sc.auth(), True)
        assertEqual(cloud_count, 6)

    # The next goes to the cloud again, but as that times out, is considered OK as well
    sc.now += 1800
    assertEqual(sc.auth(), True)
    assertEqual(cloud_count, 7)

    # This could go on for the rest of a week, but then it should finally fail
    sc.now += 6*86400
    assertEqual(sc.auth(), False)
    assertEqual(cloud_count, 8)
