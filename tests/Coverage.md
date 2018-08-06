# Code coverage

Unit tests result in a code coverage of
[![codecov](https://codecov.io/gh/jsxc/xmpp-cloud-auth/branch/master/graph/badge.svg)](https://codecov.io/gh/jsxc/xmpp-cloud-auth).

However, with system tests (which require `/etc/xcauth.accounts` based on [xcauth.accounts.sample](./xcauth.accounts.sample) and a running Nextcloud+JSXC instance), code coverage as of [`f97ec4f0f`](https://github.com/jsxc/xmpp-cloud-auth/commit/f97ec4f0f) achieves a stunning 99%. [!Code coverage](./codecov.svg)

This is the output of `nosetests` in the top-level directory (with online tests, based on the above version).

```
...............................--............................................
.......................
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
xclib/__init__.py           30      0   100%
xclib/auth.py               97      0   100%
xclib/authops.py           135      1    99%   116
xclib/check.py               8      0   100%
xclib/configuration.py      70      1    99%   152
xclib/db.py                135      2    99%   156, 196
xclib/dbmops.py             19      0   100%
xclib/ejabberd_io.py        34      2    94%   33-34
xclib/ejabberdctl.py        31      0   100%
xclib/isuser.py             25      0   100%
xclib/postfix_io.py         25      0   100%
xclib/prosody_io.py         17      0   100%
xclib/roster.py             55      0   100%
xclib/roster_thread.py      88      0   100%
xclib/saslauthd_io.py       36      2    94%   35-36
xclib/sigcloud.py           49      1    98%   76
xclib/sockact.py            27      0   100%
xclib/utf8.py               18      0   100%
xclib/version.py             1      0   100%
------------------------------------------------------
TOTAL                      900      9    99%

-----------------------------------------------------------------------------
100 tests run in 2.9 seconds. 
2 skipped (98 tests passed)
```
