# xmpp-cloud-auth

This authentication script for [ejabberd](https://www.ejabberd.im) and [prosody](https://prosody.im) allows to authenticate against a
[Nextcloud](https://nextcloud.com)/[Owncloud](https://owncloud.org) instance running [OJSXC](https://www.jsxc.org) (>= 3.2.0).

For installation and configuration instructions, see [doc/Installation.md](doc/Installation.md). :warning: Especially if you plan to [use it on *Prosody*](doc/Installation.md#prosody), as their `mod_auth_external.lua` does not work around a bug in `lpty`.

# Build status
* Build status: [![Build Status](https://travis-ci.org/jsxc/xmpp-cloud-auth.svg?branch=master)](https://travis-ci.org/jsxc/xmpp-cloud-auth)
* Code coverage (offline-only): [![codecov](https://codecov.io/gh/jsxc/xmpp-cloud-auth/branch/master/graph/badge.svg)](https://codecov.io/gh/jsxc/xmpp-cloud-auth) (Travis unfortunately can't do online tests)
* Code coverage (offline and online tests): [99%](tests/Coverage.md) (manually updated every few commits)

