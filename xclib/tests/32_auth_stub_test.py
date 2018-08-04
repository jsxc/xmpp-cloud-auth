# Check whether the auth() function works as it should
# Stubs the cloud_request() functions for this
import time
from datetime import datetime, timedelta
from xclib.sigcloud import sigcloud
from xclib import xcauth
from xclib.check import assertEqual, assertSimilar
from xclib.utf8 import unutf8

cloud_count = 0

def setup_module():
    global xc, sc
    xc = xcauth(default_url='https://localhost', default_secret='01234',
        #sql_db='/tmp/auth.sqlite3', cache_storage='db',
        #sql_db='/tmp/auth.sqlite3', cache_storage='db',
        #sql_db=':memory:', cache_storage='db',
        sql_db=':memory:', cache_storage='memory',
        bcrypt_rounds=6)
    sc = sigcloud(xc, 'user2', 'domain2', 'pass2')

def teardown_module():
    pass

def sql0(sql, *args, **kwargs):
    xc.db.cache.execute(sql, *args, **kwargs)
def sql1(sql, *args, **kwargs):
    return xc.db.cache.execute(sql, *args, **kwargs).fetchone()

def utc(ts):
    return datetime.utcfromtimestamp(int(ts))

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
    assertEqual(0, sql1('SELECT COUNT(*) FROM authcache')[0])
    assertEqual(sc.auth(), True)
    assertEqual(1, sql1('SELECT COUNT(*) FROM authcache')[0])
    assertEqual(1, sql1('''SELECT COUNT(*) FROM authcache WHERE jid = 'user2@domain2' ''')[0])

# Test group 20: Time-limited tokens
def sc_trap(data):
    assert False # Should not reach out to the cloud
def test_20_token_success():
    # ./generateTimeLimitedToken tuser tdomain 01234 3600 1000
    sc = sigcloud(xc, 'tuser', 'tdomain',
        'AMydsCzkh8-8vjcb9U2gqV/FZQAAEfg', now=utc(2000))
    sc.verbose_cloud_request = sc_trap
    assertEqual(sc.auth(), True)
    assertEqual(0, sql1('''SELECT COUNT(*) FROM authcache WHERE jid = 'tuser@tdomain' ''')[0])

def test_20_token_fail():
    # ./generateTimeLimitedToken tuser tdomain 01234 3600 1000
    sc = sigcloud(xc, 'tuser', 'tdomain',
        'AMydsCzkh8-8vjcb9U2gqV/FZQAAEfg', now=utc(5000))
    sc.verbose_cloud_request = sc_noauth
    global cloud_count
    cloud_count = 0
    assertEqual(sc.auth(), False)
    assertEqual(cloud_count, 1)

def test_20_token_version():
    # Wrong version
    sc = sigcloud(xc, 'tuser', 'tdomain',
        'BMydsCzkh8-8vjcb9U2gqV/FZQAAEfg', now=utc(5000))
    sc.verbose_cloud_request = sc_noauth
    global cloud_count
    cloud_count = 0
    assertEqual(sc.auth(), False)
    assertEqual(cloud_count, 1)

# Test group 30: Cache logic
def test_30_cache():
    global cloud_count
    cloud_count = 0
    sc = sigcloud(xc, 'user3', 'domain3', 'pass3', now=utc(1))

    # Timeout first: No cache entry
    sc.verbose_cloud_request = sc_timeout
    assertEqual(sc.auth(), False)
    assertEqual(0, sql1('''SELECT COUNT(*) FROM authcache WHERE jid = 'user3@domain3' ''')[0])
    assertEqual(cloud_count, 1)

    # Success: Cache entry
    sc.verbose_cloud_request = sc_success
    assertEqual(sc.auth(), True)
    assertEqual(1, sql1('''SELECT COUNT(*) FROM authcache WHERE jid = 'user3@domain3' ''')[0])
    entry = sql1('''SELECT * FROM authcache WHERE jid = 'user3@domain3' ''')
    assert(entry != None)
    assert entry['pwhash'].startswith('$2b$06$')
    cachedpw = entry['pwhash']
    assertEqual(entry['firstauth'], utc(1))
    firstauth = entry['firstauth']
    assertEqual(entry['remoteauth'], utc(1))
    assertEqual(entry['anyauth'], utc(1))
    assertEqual(cloud_count, 2)

    # Same request a little bit later: Should use cache (and note it)
    sc.now = utc(100)
    sc.verbose_cloud_request = sc_trap
    assertEqual(sc.auth(), True)
    entry = sql1('''SELECT * FROM authcache WHERE jid = 'user3@domain3' ''')
    assertEqual(cachedpw, entry['pwhash']) # No cache password update
    assertEqual(entry['firstauth'], firstauth)
    assertEqual(entry['remoteauth'], utc(1))
    assertEqual(entry['anyauth'], utc(100))
    assertEqual(cloud_count, 2)

    # Bad password request
    sc.now = utc(200)
    sc.verbose_cloud_request = sc_noauth
    sc.password = 'badpass'
    assertEqual(sc.auth(), False)
    assertEqual(entry, sql1('''SELECT * FROM authcache WHERE jid = 'user3@domain3' ''')) # Unmodified
    assertEqual(cloud_count, 3)
    # Test whether the DEFAULT values from the database are reapplied
    # (is the case when using INSERT OR REPLACE with DEFAULTs in schema)
    time.sleep(1)

    # New successful password request again: Should use cloud again
    sc.now = utc(300)
    sc.password = 'newpass'
    sc.verbose_cloud_request = sc_success
    assertEqual(sc.auth(), True)
    entry = sql1('''SELECT * FROM authcache WHERE jid = 'user3@domain3' ''')
    assert cachedpw != entry['pwhash'] # Update cached password
    assertEqual(entry['firstauth'], firstauth)
    assertEqual(entry['remoteauth'], utc(300))
    assertEqual(entry['anyauth'], utc(300))
    assertEqual(cloud_count, 4)

    # Token request should not change anything
    # ./generateTimeLimitedToken user3 domain3 01234 3600 1
    sc.password = 'ABbL+6M8K7HGF/vnfaZZi5XFZQAADhE'
    assertEqual(sc.auth(), True)
    assertEqual(entry, sql1('''SELECT * FROM authcache WHERE jid = 'user3@domain3' ''')) # Unmodified
    assertEqual(cloud_count, 4)

    # More than an hour of waiting: Go to the cloud again
    sc.now = utc(4000)
    sc.password = 'newpass'
    assertEqual(sc.auth(), True)
    assert entry != sql1('''SELECT * FROM authcache WHERE jid = 'user3@domain3' ''') # Updated
    entry = sql1('''SELECT * FROM authcache WHERE jid = 'user3@domain3' ''')
    assert cachedpw != entry['pwhash'] # Update cached password
    assertEqual(entry['firstauth'], firstauth)
    assertEqual(entry['remoteauth'], utc(4000))
    assertEqual(entry['anyauth'], utc(4000))
    assertEqual(cloud_count, 5)

    # Another hour has passed, but the server is now unreachable
    sc.now = utc(8000)
    sc.verbose_cloud_request = sc_timeout
    assertEqual(sc.auth(), True)
    entry = sql1('''SELECT * FROM authcache WHERE jid = 'user3@domain3' ''')
    assert cachedpw != entry['pwhash'] # Update cached password
    assertEqual(entry['firstauth'], firstauth)
    assertEqual(entry['remoteauth'], utc(4000))
    assertEqual(entry['anyauth'], utc(8000))
    assertEqual(cloud_count, 6)

    # Another request shortly after goes to the cache again
    sc.now = utc(8100)
    assertEqual(sc.auth(), True)
    entry = sql1('''SELECT * FROM authcache WHERE jid = 'user3@domain3' ''')
    assert cachedpw != entry['pwhash'] # Update cached password
    assertEqual(entry['firstauth'], firstauth)
    assertEqual(entry['remoteauth'], utc(4000))
    assertEqual(entry['anyauth'], utc(8100))
    assertEqual(cloud_count, 6)

    # Now 46 more requests spaced half an hour apart should all go to the cache
    while sc.now < utc(4000 + 86400 - 1800):
        sc.now += timedelta(seconds=1800)
        assertEqual(sc.auth(), True)
        assertEqual(cloud_count, 6)

    # The next goes to the cloud again, but as that times out, is considered OK as well
    sc.now += timedelta(seconds=1800)
    assertEqual(sc.auth(), True)
    assertEqual(cloud_count, 7)

    # This could go on for the rest of a week, but then it should finally fail
    sc.now += timedelta(days=6)
    assertEqual(sc.auth(), False)
    assertEqual(cloud_count, 8)
