# Code coverage

Unit tests result in a code coverage of
[![codecov](https://codecov.io/gh/jsxc/xmpp-cloud-auth/branch/master/graph/badge.svg)](https://codecov.io/gh/jsxc/xmpp-cloud-auth).

However, with system tests (which require `/etc/xcauth.accounts` based on [xcauth.accounts.sample](./xcauth.accounts.sample) and a running Nextcloud+JSXC instance), code coverage as of [`48a3d8e`](https://github.com/jsxc/xmpp-cloud-auth/commit/48a3d8e) raises this to 98%.

This is the output of `nosetests` in the top-level directory (with online tests, based on the above version).

```
...........................................................................................
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
xclib/__init__.py           34      0   100%
xclib/auth.py               98      2    98%   14, 66
xclib/authops.py            75      1    99%   76
xclib/check.py               8      0   100%
xclib/configuration.py      69      0   100%
xclib/dbmops.py             19      0   100%
xclib/ejabberd_io.py        26      0   100%
xclib/ejabberdctl.py        31      0   100%
xclib/isuser.py             27      1    96%   6
xclib/postfix_io.py         22      0   100%
xclib/prosody_io.py         17      0   100%
xclib/roster.py             48      0   100%
xclib/roster_thread.py      81      0   100%
xclib/saslauthd_io.py       28      0   100%
xclib/sigcloud.py           49      5    90%   32, 59, 64, 70, 76
xclib/utf8.py               18      0   100%
xclib/version.py             1      0   100%
------------------------------------------------------
TOTAL                      651      9    99%
----------------------------------------------------------------------
Ran 91 tests in 1.510s

OK
```
