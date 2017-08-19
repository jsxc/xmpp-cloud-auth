# Test when replacing request.session
import requests
from xclib.sigcloud import sigcloud
from xclib import xcauth

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

def post_400(url, data='', headers='', allow_redirects=False,
        timeout=5):
    return fakeResponse(400, None, '400 Error')

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
    assert sc.isuser() == False

def test_http404():
    xc.session.post = post_400
    assert sc.isuser() == False

def test_http200_empty():
    xc.session.post = post_200_empty
    assert sc.isuser() == False

def test_success():
    xc.session.post = post_200_ok
    assert sc.isuser() == True
