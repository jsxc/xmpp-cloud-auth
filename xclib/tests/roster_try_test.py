# Exercise try_roster()
import requests
import logging
from xclib.sigcloud import sigcloud
from xclib.ejabberdctl import ejabberdctl
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

def post_404(url, data='', headers='', allow_redirects=False,
        timeout=5):
    return fakeResponse(404, None, '404 Not found')

def post_200_empty(url, data='', headers='', allow_redirects=False,
        timeout=5):
    return fakeResponse(200, None, '200 Success')

def make_rosterfunc(sharedRoster):
    def post_200_ok(url, data='', headers='', allow_redirects=False,
                    timeout=5):
        return fakeResponse(200, {
            'result': 'success',
            'data': {
                'sharedRoster': sharedRoster
            }}, 'fake body')
    return post_200_ok

def setup_module():
    global xc, sc
    xc = xcauth(domain_db={
            'xdomain': '99999\thttps://remotehost\tydomain\t',
            'udomain': '8888\thttps://oldhost\t',
        },
        default_url='https://localhost', default_secret='01234',
        ejabberdctl='/bin/true',
        shared_roster_db={}
    )
    xc.ejabberd_controller = ejabberdctl(xc)
    sc = sigcloud(xc, 'user1', 'domain1')

def teardown_module():
    pass

def ctrl_none(args):
    return None
def ctrl_fail(args):
    assert False
def ctrl_end(args):
    assert False
def test_try_10none():
    xc.session.post = post_timeout
    xc.ejabberd_controller.execute = ctrl_fail
    assert sc.try_roster(async=False) == True
def test_try_11none():
    xc.session.post = post_200_empty
    xc.ejabberd_controller.execute = ctrl_fail
    assert sc.try_roster(async=False) == True

def ctrl_getfn20(args):
    logging.debug('ctrl_getfn20')
    assert args == ['get_vcard', 'user1', 'domain1', 'FN']
    xc.ejabberd_controller.execute = ctrl_setfn20
    return None
def ctrl_setfn20(args):
    logging.debug('ctrl_setfn20')
    assert args == ['set_vcard', 'user1', 'domain1', 'FN', 'Ah Be']
    xc.ejabberd_controller.execute = ctrl_end
    return True
def ctrl_getfn22(args):
    logging.debug('ctrl_getfn22')
    assert args == ['get_vcard', 'user1', 'domain1', 'FN']
    xc.ejabberd_controller.execute = ctrl_end
    return 'Ah Be'
def test_try_20first_name():
    # Expected: a get and a set vcard
    xc.session.post = make_rosterfunc({'user1@domain1':{'name':'Ah Be'}})
    xc.ejabberd_controller.execute = ctrl_getfn20
    assert sc.try_roster(async=False) == True
    assert xc.ejabberd_controller.execute == ctrl_end
def test_try_21same_name_cached():
    # Expected: no vcard calls
    xc.session.post = make_rosterfunc({'user1@domain1':{'name':'Ah Be'}})
    xc.ejabberd_controller.execute = ctrl_fail
    assert sc.try_roster(async=False) == True
def test_try_22same_name_uncached():
    # Expected: a get call
    xc.session.post = make_rosterfunc({'user1@domain1':{'name':'Ah Be','dummy':'1'}})
    xc.ejabberd_controller.execute = ctrl_end
    assert sc.try_roster(async=False) == True
    logging.debug(xc.ejabberd_controller.execute)
    assert xc.ejabberd_controller.execute == ctrl_end

