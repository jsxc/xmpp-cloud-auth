# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## 0.2.2+ - [Unreleased]
### Added
- Can now authenticate against multiple cloud instances
  as defined by a static text file or a dynamic database
- Experimental support for talking over a socket
- Experimental support for saslauthd protocol
- *systemd* configuration files for sending the XMPP authentication requests/responses over a socket
  with `multi-user.target` depending on it
- *systemd* configuration files for posing as `saslauthd`
- "quit" and "exit" commands (useful, when used behind a socket)
### Fixed
### Changed
- `external_cloud.*` has been renamed to `xcauth.*` everywhere. :warning: You will need to rename your configuration file, the old name will only be supported for a short period of time.
- Running under user `xcauth`
- Now requires "configargparse"
- Use HTTP/1.1 persistent connections for higher throughput
- The new `-t generic` (equivalent to `-t prosody`) is now default
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
