# Code coverage

Unit tests result in a code coverage of
[![codecov](https://codecov.io/gh/jsxc/xmpp-cloud-auth/branch/master/graph/badge.svg)](https://codecov.io/gh/jsxc/xmpp-cloud-auth).

However, with system tests (which require `/etc/xcauth.accounts` based on [xcauth.accounts.sample](./xcauth.accounts.sample) and a running Nextcloud+JSXC instance), code coverage as of [`402636a`](https://github.com/jsxc/xmpp-cloud-auth/commit/402636a317bfda9295e4d84eb9de4210318729f5) raises this to 96%.

This is the output of `nosetests --with-coverage --cover-package=xclib` in the top-level directory.

```
.....................................................................
Name                     Stmts   Miss  Cover   Missing
------------------------------------------------------
xclib.py                    32      0   100%
xclib/auth.py               89      5    94%   14, 64-65, 87-89
xclib/authops.py            73      1    99%   76
xclib/configuration.py      69      3    96%   122, 134-135
xclib/dbmops.py             18      0   100%
xclib/ejabberd_io.py        25      0   100%
xclib/ejabberdctl.py        30      1    97%   39
xclib/isuser.py             19      1    95%   5
xclib/prosody_io.py         17      0   100%
xclib/roster.py             44      0   100%
xclib/roster_thread.py      78      1    99%   19
xclib/saslauthd_io.py       27      0   100%
xclib/sigcloud.py           48      9    81%   31, 58-59, 63-64, 69-70, 74-75
xclib/version.py             1      0   100%
------------------------------------------------------
TOTAL                      570     21    96%
----------------------------------------------------------------------
Ran 69 tests in 1.206s

OK
```
