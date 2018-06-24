# *systemd* integration

`xcauth` can also be started from *systemd*. Three modes are supported:

1. Starting in *inetd* compatibility mode: For each connection to that socket, a new `xcauth` process is started. `xcauth` reads from stdin/stdout.
1. Using *systemd* [socket activation](http://0pointer.net/blog/projects/socket-activation.html), single protocol per configuration file: On the first connection, the single `xcauth` process is started for this protocol/port. For each incoming connection, only a thread is spawned. This is more efficient if a new connection is opened for every request (common for *saslauthd* and *postfix* modes, but depends on the requesting application).
1. Using *systemd* socket activation, multiple protocols per configuration file: Similar to the one above, but only a single `xcauth` process is ever started. All protocols are determined by information passed by *systemd* on process start. **This mode is [currently](https://github.com/systemd/python-systemd#60) not supported by [python-systemd](https://github.com/systemd/python-systemd) library** and therefore not available for use. However, it is supported by `xcauth` and future file descriptor names passed by *systemd* will override the command line.

The following ports are used by default:
- TCP port 23662: *ejabberd* protocol support
- TCP port 23663: *prosody* protocol support
- TCP port 23664: *prosody* or *ejabberd* protocol support, depending on configuration in `/etc/xcauth.conf` (DEPRECATED)
- TCP port 23665: *postfix* protocol support
- `/var/run/saslauthd/mux` (stream-based Unix domain socket): *saslauthd* protocol support

## XMPP authentication over *systemd* socket

For some environments, it might be advantageous to use *xcauth* over a network socket. Here is a pair of sample *systemd* configuration files, accepting network connection to `localhost:23664`.

### Installation (as root)

1. Perform the *xcauth* installation as explained in the [parent README](../README.md) or the [installation wiki](https://github.com/jsxc/xcauth/wiki). Especially install source into `/opt/xcauth` and put the configuration in `/etc/xcauth.conf`.
1. Copy `xcauth@.service` and `xcauth.socket` to `/etc/systemd/system` (if no modifications to these files are needed, you may also symlink them manually or using `systemctl link`; beware that some versions of *systemd* have problems with symlinks ([systemd#3010](https://github.com/systemd/systemd/issues/3010))
1. Create the user `xcauth` and the directories: `sudo ../install.sh`
1. Activate the service: `systemctl enable xcauth.socket` and `systemctl start xcauth.socket`

### Testing

If you have set `type=generic` (equivalent to `type=prosody`) in `/etc/xcauth.conf`, then the following should work (`$` indicates the command line prompt, `<` is data received and `>` data sent):

```
$ telnet localhost 23664
< Trying ::1...
< Connected to localhost.
< Escape character is '^]'.
> isuser:admin:example.org
< 1
> auth:admin:example.org:good_password
< 1
> auth:admin:example.org:incorrect_password
< 0
> quit
< Connection closed by foreign host.
$
```

## `saslauthd` mode (authentication)

To use *xcauth.py* as an authentication backend for e.g. mail servers
(successfully tested with *Postfix* and *Cyrus IMAP*), you can activate
that software's authentication against *saslauthd* (see their
respective documentation for how to do this). Then, run the following
commands to have *xcauth.py* pose as *saslauthd*:

1. Install *xcauth* as described above.
1. Copy `xcsaslauth@.service` and `xcsaslauth.socket` to `/etc/systemd/system` (see above for symlink issues)
1. Disable "normal" *saslauthd*: `systemctl disable saslauthd`
1. Enable *xcauth.py* in *saslauthd* mode: `systemctl enable xcsaslauth.socket` and `systemctl start xcsaslauth.socket`

Note that the *xcsaslauth* service listens on the Unix domain socket
`/var/run/saslauthd/mux`. This should be default on Ubuntu, even though
the software configuration files might only mention `/var/run/saslauthd`,
the `/mux` suffix is added internally by the *SASL* library.

## `postfix` mode (existence check)

When a *Postfix* mail server serves multiple realms (=domains), it
needs some way to know whether a
[mailbox](http://www.postfix.org/VIRTUAL_README.html#virtual_mailbox)
exists
([`virtual_mailbox_maps`](http://www.postfix.org/postconf.5.html#virtual_mailbox_maps)
*Postfix* variable). Using *saslauthd* mode alone would require
manually maintaining a *virtual mailbox map*, listing each user/mailbox.

*xcauth* already can provide the information whether a user exists, so
`postfix` mode provides a *Postfix*
[`tcp_table`](http://www.postfix.org/tcp_table.5.html) compatible interface
to query the existance of a user and thereby confirm the availability of the
user's mailbox.

1. Ensure that all *Nextcloud* logins are in `user@domain` format
   (any login name without an `@domain` part would be a valid account
   in all realms/domains, which might not be desirable)
1. Maintain a list of all *realms* in `/etc/postfix/vmdomains`, as a tuple
   with the domain as the left-hand side, and an arbitrary right-hand side
   ("OK" is a common value).

   The users can be determined easily, but not the domains. It is assumed
   that the domain list will not change frequently. (You will need to run
   `postmap /etc/postfix/vmdomains` after every change to that file.)
1. Add the line
   ```Postfix
   virtual_mailbox_maps = hash:/etc/postfix/vmdomains, tcp:localhost:23665
   ```
   to `/etc/postfix/main.cf`. Integrate any existing assignment to
   `virtual_mailbox_maps`.
1. Install *xcauth* as described above.
1. Copy `xcpostfix@.service` and `xcpostfix.socket` to `/etc/systemd/system` (see above for symlink issues)
1. Enable *xcauth.py* in *postfix* mode: `systemctl enable xcpostfix.socket` and `systemctl start xcpostfix.socket`

## Security considerations

:warning: For security reasons, you might want to limit who can use this service over the network. Also, as `xcauth` is meant for local use, it does not support encryption (and therefore, confidentiality) of the commands (including passwords!) and authentication of return values. Therefore, please use it over the *loopback* interface only. If you must use a network connection, wrap it in `stunnel` or similar.
