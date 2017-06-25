# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## 0.2.2+ - [Unreleased]
### Added
- "quit" and "exit" commands (useful, when used behind a socket)
### Fixed
### Changed

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
