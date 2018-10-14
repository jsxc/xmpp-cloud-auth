# Exercise try_roster()
# Stubs `ejabberctl` and `request`
import requests
import logging
import json
from xclib.sigcloud import sigcloud
from xclib.ejabberdctl import ejabberdctl
from xclib import xcauth
from xclib.check import assertEqual

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
        j = ({
            'result': 'success',
            'data': {
                'sharedRoster': sharedRoster
            }})
        return fakeResponse(200, j, json.dumps(j))
    return post_200_ok

def setup_module():
    global xc, sc
    xc = xcauth(domain_db={
            b'xdomain': b'99999\thttps://remotehost\tydomain\t',
            b'udomain': b'8888\thttps://oldhost\t',
        },
        default_url='https://localhost', default_secret='01234',
        ejabberdctl='/no/bin/ejabberdctl',
        sql_db=':memory:',
        cache_storage='db',
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
    assertEqual(sc.try_roster(async_=False), True)
def test_try_11none():
    xc.session.post = post_200_empty
    xc.ejabberd_controller.execute = ctrl_fail
    assertEqual(sc.try_roster(async_=False), True)

def ctrl_setfn20(args):
    logging.info('ctrl_setfn20')
    assertEqual(args, ['set_vcard', 'user1', 'domain1', 'FN', 'Ah Be'])
    xc.ejabberd_controller.execute = ctrl_end
    return True
def ctrl_setfn23(args):
    logging.info('ctrl_setfn23')
    assertEqual(args, ['set_vcard', 'user1', 'domain1', 'FN', 'Ce De'])
    xc.ejabberd_controller.execute = ctrl_end
    return True
def test_try_20first_name():
    # Expected: a single set vcard
    sc.username = 'user1'
    sc.domain = 'domain1'
    xc.session.post = make_rosterfunc({'user1@domain1':{'name':'Ah Be'}})
    xc.ejabberd_controller.execute = ctrl_setfn20
    assertEqual(sc.try_roster(async_=False), True)
    assertEqual(xc.ejabberd_controller.execute, ctrl_end)
def test_try_21same_name_cached():
    # Expected: no vcard calls
    xc.session.post = make_rosterfunc({'user1@domain1':{'name':'Ah Be'}})
    xc.ejabberd_controller.execute = ctrl_fail
    assertEqual(sc.try_roster(async_=False), True)
def test_try_22same_name_uncached():
    # Expected: no vcard calls
    xc.session.post = make_rosterfunc({'user1@domain1':{'name':'Ah Be','dummy':'1'}})
    xc.ejabberd_controller.execute = ctrl_end
    assertEqual(sc.try_roster(async_=False), True)
    logging.info(xc.ejabberd_controller.execute)
    assertEqual(xc.ejabberd_controller.execute, ctrl_end)
def test_try_23changed_name():
    # Expected: a single set vcard
    xc.session.post = make_rosterfunc({'user1@domain1':{'name':'Ce De'}})
    xc.ejabberd_controller.execute = ctrl_setfn23
    assertEqual(sc.try_roster(async_=False), True)
    assertEqual(xc.ejabberd_controller.execute, ctrl_end)

def assert_grouplist(jid, grouplist):
    for row in xc.db.conn.execute('SELECT grouplist FROM rosterinfo WHERE jid = ?', (jid,)):
        assertEqual(grouplist, row['grouplist'])
        return
    assertEqual('jid does not exist', jid) # Fail on empty list
def assert_groupinfo(groupname, userlist):
    for row in xc.db.conn.execute('SELECT userlist FROM rostergroups WHERE groupname = ?', (groupname,)):
        assertEqual(userlist, row['userlist'])
        return
    assertEqual('groupname does not exist', groupname) # Fail on empty list

def ctrl_collect(args):
    global collect
    collect.append(args)
    return ''
def test_try_30add_lonely_group():
    #logging.debug('isol = %s' % xc.db.conn.isolation_level)
    #xc.db.conn.dump('sqlite_master')
    #xc.db.conn.dump('rosterinfo')
    # Expected: groups calls
    global collect
    collect = []
    xc.session.post = make_rosterfunc({'user1@domain1':{'name':'Ce De','groups':['Lonely']}})
    xc.ejabberd_controller.execute = ctrl_collect
    assertEqual(sc.try_roster(async_=False), True)
    logging.info('collected = ' + str(collect))
    assertEqual(collect, [
        ['srg_create', 'Lonely', 'domain1', 'Lonely', 'Lonely', 'Lonely'],
        ['srg_get_members', 'Lonely', 'domain1'],
        ['srg_user_add', 'user1', 'domain1', 'Lonely', 'domain1'],
        ])
    #xc.db.conn.dump('sqlite_master')
    xc.db.conn.dump('rosterinfo')
    xc.db.conn.dump('rostergroups')
    assert_grouplist('user1@domain1', 'Lonely')
    assert_groupinfo('Lonely@domain1', 'user1@domain1')
    #assert False
def test_try_31login_again():
    # Expected: groups calls
    global collect
    collect = []
    xc.session.post = make_rosterfunc({'user1@domain1':{'name':'Ce De','groups':['Lonely']}})
    xc.ejabberd_controller.execute = ctrl_collect
    assertEqual(sc.try_roster(async_=False), True)
    logging.info(collect)
    assertEqual(collect, [
        ])
    assert_grouplist('user1@domain1', 'Lonely')
    assert_groupinfo('Lonely@domain1', 'user1@domain1')
def test_try_32add_normal_group():
    # Expected: groups calls
    global collect
    collect = []
    xc.session.post = make_rosterfunc({
        'user1@domain1':{'name':'Ce De','groups':['Lonely', 'Family']},
        'user2@domain1':{'name':'De Be','groups':['Family']},
    })
    xc.ejabberd_controller.execute = ctrl_collect
    assertEqual(sc.try_roster(async_=False), True)
    logging.info(collect)
    assert collect == [
        ['set_vcard', 'user2', 'domain1', 'FN', 'De Be'],
        ['srg_create', 'Family', 'domain1', 'Family', 'Family', 'Family'],
        ['srg_get_members', 'Family', 'domain1'],
        ['srg_user_add', 'user1', 'domain1', 'Family', 'domain1'],
        ['srg_user_add', 'user2', 'domain1', 'Family', 'domain1'],
    ] or collect == [
        ['set_vcard', 'user2', 'domain1', 'FN', 'De Be'],
        ['srg_create', 'Family', 'domain1', 'Family', 'Family', 'Family'],
        ['srg_get_members', 'Family', 'domain1'],
        ['srg_user_add', 'user2', 'domain1', 'Family', 'domain1'],
        ['srg_user_add', 'user1', 'domain1', 'Family', 'domain1'],
    ]
    xc.db.conn.dump('rosterinfo')
    xc.db.conn.dump('rostergroups')
    assert_grouplist('user1@domain1', 'Family\tLonely')
    #assert_grouplist('user2@domain1', 'Family')
    assert_grouplist('user2@domain1', None)
    assert_groupinfo('Lonely@domain1', 'user1@domain1')
    assert_groupinfo('Family@domain1', 'user1@domain1\tuser2@domain1')
def test_try_33login_other_user():
    global collect
    collect = []
    xc.session.post = make_rosterfunc({
        'user1@domain1':{'name':'Ce De','groups':['Family']},
        'user2@domain1':{'name':'De Be','groups':['Family', 'Friends']},
        'user3@domain1':{'name':'Xy Zzy','groups':['Friends']},
    })
    xc.ejabberd_controller.execute = ctrl_collect
    sc = sigcloud(xc, 'user2', 'domain1')
    assertEqual(sc.try_roster(async_=False), True)
    logging.info(collect)
    assert collect == [
        ['set_vcard', 'user3', 'domain1', 'FN', 'Xy Zzy'],
        ['srg_create', 'Friends', 'domain1', 'Friends', 'Friends', 'Friends'],
        ['srg_get_members', 'Friends', 'domain1'],
        ['srg_user_add', 'user3', 'domain1', 'Friends', 'domain1'],
        ['srg_user_add', 'user2', 'domain1', 'Friends', 'domain1'],
    ] or collect == [
        ['set_vcard', 'user3', 'domain1', 'FN', 'Xy Zzy'],
        ['srg_create', 'Friends', 'domain1', 'Friends', 'Friends', 'Friends'],
        ['srg_get_members', 'Friends', 'domain1'],
        ['srg_user_add', 'user2', 'domain1', 'Friends', 'domain1'],
        ['srg_user_add', 'user3', 'domain1', 'Friends', 'domain1'],
    ]
    xc.db.conn.dump('rosterinfo')
    xc.db.conn.dump('rostergroups')
    assert_grouplist('user1@domain1', 'Family\tLonely')
    assert_grouplist('user2@domain1', 'Family\tFriends')
    assert_grouplist('user3@domain1', None)
    assert_groupinfo('Lonely@domain1', 'user1@domain1')
    assert_groupinfo('Family@domain1', 'user1@domain1\tuser2@domain1')
    assert_groupinfo('Friends@domain1', 'user2@domain1\tuser3@domain1')
def test_try_34login_other_user_again():
    global collect
    collect = []
    xc.session.post = make_rosterfunc({
        'user1@domain1':{'name':'Ce De','groups':['Family'], 'dummy': '1'},
        'user2@domain1':{'name':'De Be','groups':['Family', 'Friends']},
        'user3@domain1':{'name':'Xy Zzy','groups':['Friends']},
    })
    xc.ejabberd_controller.execute = ctrl_collect
    sc = sigcloud(xc, 'user2', 'domain1')
    assertEqual(sc.try_roster(async_=False), True)
    logging.info(collect)
    assertEqual(collect, [])
    xc.db.conn.dump('rosterinfo')
    xc.db.conn.dump('rostergroups')
    assert_grouplist('user1@domain1', 'Family\tLonely')
    assert_grouplist('user2@domain1', 'Family\tFriends')
    assert_grouplist('user3@domain1', None)
    assert_groupinfo('Lonely@domain1', 'user1@domain1')
    assert_groupinfo('Family@domain1', 'user1@domain1\tuser2@domain1')
    assert_groupinfo('Friends@domain1', 'user2@domain1\tuser3@domain1')

def test_try_40third_party_deletion():
    global collect
    collect = []
    xc.db.conn.dump('rosterinfo')
    xc.session.post = make_rosterfunc({
        'user2@domain1':{'name':'De Be','groups':['Family', 'Friends']},
        'user3@domain1':{'name':'Xy Zzy','groups':['Friends']},
    })
    xc.ejabberd_controller.execute = ctrl_collect
    sc = sigcloud(xc, 'user2', 'domain1')
    assertEqual(sc.try_roster(async_=False), True)
    logging.info(collect)
    assertEqual(collect, [
        ['srg_user_del', 'user1', 'domain1', 'Family', 'domain1']
    ])
    xc.db.conn.dump('rosterinfo')
    xc.db.conn.dump('rostergroups')
    assert_grouplist('user1@domain1', 'Family\tLonely') # This is not touched by 3rd party deletion
    assert_grouplist('user2@domain1', 'Family\tFriends')
    assert_grouplist('user3@domain1', None)
    assert_groupinfo('Lonely@domain1', 'user1@domain1')
    assert_groupinfo('Family@domain1', 'user2@domain1') # Only this
    assert_groupinfo('Friends@domain1', 'user2@domain1\tuser3@domain1')

def test_try_41self_deletion():
    global collect
    collect = []
    xc.db.conn.dump('rosterinfo')
    xc.db.conn.dump('rostergroups')
    xc.session.post = make_rosterfunc({
        'user1@domain1':{'name':'Ce De'}
    })
    xc.ejabberd_controller.execute = ctrl_collect
    sc = sigcloud(xc, 'user1', 'domain1')
    assertEqual(sc.try_roster(async_=False), True)
    xc.db.conn.dump('rosterinfo')
    xc.db.conn.dump('rostergroups')
    logging.info(collect)
    assertEqual(collect, [
        # The first is unnecessary but harmless (idempotent) and not easily avoidable
        ['srg_user_del', 'user1', 'domain1', 'Family', 'domain1'],
        ['srg_user_del', 'user1', 'domain1', 'Lonely', 'domain1']
    ])
    xc.db.conn.dump('rosterinfo')
    xc.db.conn.dump('rostergroups')
    assert_grouplist('user1@domain1', '')
    assert_grouplist('user2@domain1', 'Family\tFriends')
    assert_grouplist('user3@domain1', None)
    assert_groupinfo('Lonely@domain1', 'user1@domain1')
    assert_groupinfo('Family@domain1', 'user2@domain1')
    assert_groupinfo('Friends@domain1', 'user2@domain1\tuser3@domain1')
