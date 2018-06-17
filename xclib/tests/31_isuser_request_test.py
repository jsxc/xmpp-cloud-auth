# Checks whether the isuser() function works as it should
# Test when replacing request.session
# (a level further down from the `stub` tests before)
import sys
import requests
from xclib.sigcloud import sigcloud
from xclib import xcauth, verify_with_isuser
import logging
import hmac
import hashlib
from xclib.check import assertEqual
from xclib.utf8 import unutf8

class fakeResponse:
    # Will be called as follows:
    # r = self.ctx.session.post(self.url, data=payload, headers=headers,
    #               allow_redirects=False, timeout=self.ctx.timeout)
    # r.status_code
    # r.json()
    # r.text
    def __init__(self, status, json, text):
        self.status_code = status
        self._json = json
        self.text = text

    def json(self):
        return self._json

def post_timeout(url, data='', headers='', allow_redirects=False,
        timeout=5):
    raise requests.exceptions.ConnectTimeout("Connection timed out")

def post_404(url, data='', headers='', allow_redirects=False,
        timeout=5):
    return fakeResponse(404, None, '404 Not found')

def post_200_empty(url, data='', headers='', allow_redirects=False,
        timeout=5):
    return fakeResponse(200, None, '200 Success')

def post_200_ok(url, data='', headers='', allow_redirects=False,
        timeout=5):
    return fakeResponse(200, {
        'result': 'success',
        'data': {
            'isUser': '1'
        }}, 'fake body')

def assertSortOf(a, b, separator):
    '''Check whether 'a' is any permutation of 'b', concatenated by 'separator'.'''
    sa = sorted(a.split(separator))
    sb = sorted(b.split(separator))
    assertEqual(sa, sb)

def post_200_ok_verify(url, data='', headers='', allow_redirects=False,
        timeout=5):
    assertEqual(url, 'https://nosuchhost')
    assertSortOf(unutf8(data), 'username=usr&operation=isuser&domain=no.such.doma.in', '&')
    hash = hmac.new(b'999', msg=data, digestmod=hashlib.sha1).hexdigest()
    assertEqual(headers['X-JSXC-SIGNATURE'], 'sha1=' + hash)
    return post_200_ok(url, data, headers, allow_redirects, timeout)

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

def test_timeout():
    xc.session.post = post_timeout
    assertEqual(sc.isuser(), None)

def test_http404():
    xc.session.post = post_404
    assertEqual(sc.isuser(), None)

def test_http200_empty():
    xc.session.post = post_200_empty
    assertEqual(sc.isuser(), None)

def test_success():
    xc.session.post = post_200_ok
    assertEqual(sc.isuser(), True)

def verify_hook(sc):
    sc.ctx.session.post = post_200_ok_verify

def test_verify():
    success, code, response = verify_with_isuser('https://nosuchhost', '999', 'no.such.doma.in', 'usr', (5, 10), verify_hook)
    assertEqual(success, True)
    assertEqual(code, None)
    assertEqual(response, {'data': {'isUser': '1'}, 'result': 'success'})
