# Tools

## `xcauth.logrotate`

To regularily rotate the logs, copy `xcauth.logrotate` to
`/etc/logrotate.d/xcauth`.

`make install` already does this for you.

## `xcauth.sudo` and `xcejabberdctl.sh`

If you want to enable shared roster groups support for *ejabberd*.

- Copy `xcauth.sudo` as `/etc/sudoers.d/xcauth`,
- Copy `xcejabberd.sh` as `/usr/sbin/xcejabberdctl`
- Remove the `#` in the `ejabberdctl=/usr/sbin/xcejabberdctl` line
  of `/etc/xcauth.conf`
- If your `ejabberdctl` does not live in `/usr/sbin`, please create
  a symlink from `/usr/sbin/ejabberdctl`.

`make install` already does *the first two steps* for you.

## `xcrestart.sh`

Restarts the sockets and services for systemd. The service does
not need to be explicitely started, it will be on the first connection
to one of the sockets. It also fixes the permissions of the database
and log files, if `xcauth` was first manually started as root and
created the files with the wrong permissions.

`make install` installs this as `/usr/bin/xcrestart`

## `dhparam.pem` and `ejabberd.yml`

These are the sample configuration files from our
[Debian and/or Raspberry Pi setup](https://github.com/jsxc/xmpp-cloud-auth/wiki/raspberry-pi-en).

`make install` installs them in `/etc/ejabberd` as `*-xcauth-example`.
