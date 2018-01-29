# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## 1.0.0+ - [Unreleased]
### Added
### Fixed
### Changed
- Changed away from multiple `dbm` storages, due to corruption/locking
  problems and the growing number of partially-related databases. The
  database is now `sqlite`.  
  **DEPRECATED** the following (will be removed in 1.2; requires upgrades
  from <=1.0 to >=1.2 to go over an intermediate step for the automatic
  database conversion process to kick in):
  - `xcdbm.py` is no longer needed. Use `sqlite3` to manipulate the
    [database contents](./doc/Database.md)
  - `--domain-db`, `--cache-db`, and `--shared-roster-db` are only used
    for the database upconversion and should be removed afterward.
  - The presence of the above options previously also enabled the use
    of that database. This is now handled as follows:
    - The domain database is always consulted. It will be empty initially.
    - The use of the cache is enabled with the new `--enable-cache` option.
    - The use of the shared roster is enabled with `--enable-shared-roster`.
  - There is a new option `--database`, defaulting to `/var/lib/xcauth/xcauth.sqlite`.

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
