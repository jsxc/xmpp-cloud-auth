# Code coverage

Unit tests result in a code coverage of
[![codecov](https://codecov.io/gh/jsxc/xmpp-cloud-auth/branch/master/graph/badge.svg)](https://codecov.io/gh/jsxc/xmpp-cloud-auth).

However, with system tests (which require `/etc/xcauth.accounts` based on [xcauth.accounts.sample](./xcauth.accounts.sample) and a running Nextcloud+JSXC instance), code coverage as of [`48a3d8e`](https://github.com/jsxc/xmpp-cloud-auth/commit/48a3d8e) raises this to 98%.

This is the output of `nosetests --with-coverage --cover-package=xclib` in the top-level directory (with online tests, based on the above version).

```
..........................................................................
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
xclib/__init__.py           32      0   100%
xclib/auth.py               96      3    97%   14, 64-65
xclib/authops.py            75      1    99%   76
xclib/configuration.py      69      0   100%
xclib/dbmops.py             18      0   100%
xclib/ejabberd_io.py        25      0   100%
xclib/ejabberdctl.py        30      1    97%   39
xclib/isuser.py             21      1    95%   5
xclib/postfix_io.py         23      0   100%
xclib/prosody_io.py         17      0   100%
xclib/roster.py             46      0   100%
xclib/roster_thread.py      84      0   100%
xclib/saslauthd_io.py       27      0   100%
xclib/sigcloud.py           48      9    81%   31, 58-59, 63-64, 69-70, 74-75
xclib/version.py             1      0   100%
------------------------------------------------------
TOTAL                      612     15    98%
----------------------------------------------------------------------
Ran 74 tests in 2.242s

OK
```
