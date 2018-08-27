# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## 2.0.1+ - [Unreleased]
### Added
- Have a valid default `type=` in `/etc/xcauth.conf` to reduce required
  configuration steps
- `xcrestart` stops `xcauth.service` as well before restarting the sockets
- `xcrestart` tries to fix permission problems
  (`xcauth` is sometimes manually before it as a test, creating DB and log
  with the wrong user ID)
- `xcrestart` is more verbose on what it does,
  as a weak replacement for a man page
- Support for running `ejabberdctl` through `sudo`
  (to allow user `xcauth` to modify the shared roster related stuff)
- *Prosody* modules are installed "almost ready" in `/usr/lib/prosody/modules`
  (`pseudolpty.lua` ready for action, our `mod_auth_external.lua` as
  `*-xcauth-version` as not to interfere with *Prosody*'s version.
  To activate it, the admin needs to rename it.
- *ejabberd* example configuration files from our
  [Debian setup, not only for the Raspberry Pi](https://github.com/jsxc/xmpp-cloud-auth/wiki/raspberry-pi-en)
  are now installed as `/etc/ejabberd/*-xcauth-example` to simplify
  the installation.

### Fixed
- Changed permissions for `/var/log/xcauth` (`logrotate` would refuse to work on it)
- Add dependency on `python3-bsddb3` and `pyton3-systemd`

### Changed
- Obsoleted `install.sh`


## 2.0.1 - 2018-08-21
### Added
- Added
  [documentation in the wiki](https://github.com/jsxc/xmpp-cloud-auth/wiki)
  how to achieve
  [100% Compliance on the Conversations XMPP tests](https://compliance.conversations.im)

### Fixed
- Deprecation version numbers in the 2.0.0 changelog entry have been fixed.

### Changed


## 2.0.0 - 2018-08-20
### Added
- Added `Makefile`, especially the `make install` target
- Added support for `deb` packaging (now the recommended installation type)
- Added support for *inetd*-style servers (acceptor(!) socket as fd 0)
- Added `tools/xcauth.logrotate` (see [tools/README.md](./tools/README.md)
- Added quick setup instructions for existing *Prosody* or *ejabberd* setups
- Added support for fewer bcrypt() rounds for in-memory databases
  (please perform your own security/risk analysis before using it)

### Fixed

### Changed
- Changed away from multiple `dbm` storages, due to corruption/locking
  problems and the growing number of partially-related databases. The
  database is now `sqlite`.
- **DEPRECATED** the following. As these options will be removed in 2.1,
  **please remove** these options from your configuration after
  converting to the `sqlite`, which happens when launching this version
  for the first time.
  - `xcdbm.py` is no longer needed. Use `sqlite3` to manipulate the
    [database contents](./doc/Database.md)
  - `--domain-db`, `--cache-db`, and `--shared-roster-db` are only used
    for the database upconversion and should be removed afterward.
  - The presence of the above options previously also enabled the use
    of that database. This is now handled as follows:
    - The domain database is always consulted. It will be empty initially.
    - The use of the cache is controlled with the new `--cache-storage`
      option (one of 'none' (default), 'memory', 'db').  
      For 'memory', you might consider lowering `--cache-bcrypt-rounds`
      significantly, based on your threat/risk analysis.
    - The use of the shared roster is enabled when `--ejabberdctl` is set.
  - There is a new option `--db`, defaulting to `/var/lib/xcauth/xcauth.sqlite`.
- As a result, upgrades from <2.0 to >=2.1 will need to go over an
  intermediate step of 2.0.x for the automatic database conversion process
  to kick in.
- Explain `socket` setup for more efficient multi-domain hosting
- Retired `xcauth.sh` (*ejabberd* versions requiring this
  should no longer be around)


## 1.1.0 - 2018-07-24

### Added
- Support *systemd* socket activation
- Now supports [*Postfix* Virtual Mailbox mode](doc/Systemd.md)

### Fixed
- Incorporated *Prosody* upstream mod_auth_external.lua fixes

### Changed
- Starting from *systemd* is now the recommended mode


## 1.0.0 - 2018-01-29

### Added
- Authentication against multiple cloud instances based on
  a dynamic database
- Support for *saslauthd* protocol
- Credentails caching
- Tool to manually create a [time-limited token](doc/Protocol.md) for debugging of that mechanism ([`xclib/tests/generateTimeLimitedToken`](./xclib/tests/generateTimeLimitedToken))
- Connection/request timeout option (default: 5s)
- Support for managed servers: Externally callable
  `verify_with_isuser()` function, differing XMPP and
  authentication domains
- Support for creating/updating *ejabberd* shared roster
  - Automatically on every login (after 0.5s, background the roster update)
  - Trigger manually from the command line (`--update-roster`)

### Fixed

### Changed
- `external_cloud.*` has been renamed to `xcauth.*` everywhere. :warning: You will also need to rename your configuration file, the old name is deprecated and disappear soon.
- `xcauth.conf` in the installation directory will no longer be considered
- Now runs under user `xcauth` with directories `/var/log/xcauth` and `/var/cache/xcauth`
- Removed support for `--per-domain-config`. The more powerful `--domain-db` remains
- No longer load configuration from `/etc/external_cloud.conf`
- Improved test coverage


## 0.2.3 - 2017-07-09
### Added
- Can now authenticate against multiple cloud instances
- Experimental support for talking over a socket
- *systemd* configuration files for sending the authentication requests/responses over a socket
  with `multi-user.target` depending on it
- "quit" and "exit" commands (useful, when used behind a socket)

### Fixed

### Changed
- Now requires "configargparse"
- Use HTTP/1.1 persistent connections for higher throughput
- The new `-t generic` (equivalent to `-t prosody`) is now default (simplifies interactive testing)
- Some refactoring


## 0.2.2 - 2017-06-23
### Added
- [Step-by-step installation and configuration instructions in the wiki](https://github.com/jsxc/xmpp-cloud-auth/wiki)
- Added the Prosody module (again) with better terminal handling ([#21](https://github.com/jsxc/xmpp-cloud-auth/issues/21))
- Meaningful error messages when using old SSL library ([#18](https://github.com/jsxc/xmpp-cloud-auth/issues/18))
- Information that leaking API secrets on the command line
  or in a world-readable configuration file is a security risk.

### Fixed
- Typos ([#17](https://github.com/jsxc/xmpp-cloud-auth/issues/17))

### Changed
- Improved documentation (SSL proxy, Prosody support, …)
- Cleanup: The default configuration method is now via configuration file.
  Removed own version of Prosody module with command-line parameter handling,
  no longer necessary with configuration file.
  ([#2](https://github.com/jsxc/xmpp-cloud-auth/issues/2))
- Debugging output more consistent


## 0.2.1 - 2017-06-08
### Added
- Transmit domain to JSXC externalApi.php (necessary for cloud accounts
  of the form user@domain) ([#13](https://github.com/jsxc/xmpp-cloud-auth/issues/13))
- Support for a configuration file when ConfigArgParse python module
  is installed (`external_cloud.conf` in `/etc` or the installation dir)

### Fixed
- No longer die without explanation on SSL errors caused by old libraries.
  Upgrading your Python libraries would be the actual fix.
  ([#17](https://github.com/jsxc/xmpp-cloud-auth/issues/17))

### Changed
- When the configuration file is for all options, no command line
  parameters are necessary. Then, the modified `mod_auth_external.lua`
  prosody module does not need to be installed.
- Old-style configuration (parameters on the command line, no configuration
  file) is now deprecated.
- Minor debug output corrections
- Clarifications in the `--help` output


## 0.2.0 - 2017-06-02
### Added
- One-shot auth and isuser tests
- Support for running under downloaded ejabberd*.deb (`xmpp-cloud-auth.sh`)

### Fixed
- Allow passwords with colons

### Changed
- Internal cleanup
   - better logging
   - generator functions

## 0.1.0 - 2016-05-02
- Initial release
