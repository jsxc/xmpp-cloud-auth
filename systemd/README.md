# *systemd* socket configuration support

For some environments, it might be advantageous to use *xmpp-cloud-auth* over a network socket. Here is a pair of sample *systemd* configuration files, accepting network connection to `localhost:23664`.

## Installation (as root)

1. Perform the *xmpp-cloud-auth* installation as explained in the [parent README](../README.md) or the [installation wiki](https://github.com/jsxc/xmpp-cloud-auth/wiki). Especially install source into `/opt/xmpp-cloud-auth` and put the configuration in `/etc/xcauth.conf`.
1. Copy `xmpp-cloud-auth@.service` and `xmpp-cloud-auth.socket` to `/etc/systemd/system` (if no modifications to these files are needed, you may also symlink them)
1. Modify the `User=prosody` line in `xmpp-cloud-auth@.service` if you do not have a `prosody` user or want to run as an even less privileged user (does not require file I/O besides Python and libraries, and the configuration file; network connection to your Nextcloud web server only).
1. Activate the service: `systemctl enable xmpp-cloud-auth.socket` and `systemctl start xmpp-cloud-auth.socket`

## Testing

When you have set `type=ejabberd` in `/etc/xcauth.conf`, then the following should work (`$` indicates the command line prompt, `<` is data received and `>` data sent):

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


## Security considerations

:warning: For security reasons, you might want to limit who can use this service over the network. Also, as `xmpp-cloud-auth` is meant for local use, it does not support encryption (and therefore, confidentiality) of the commands (including passwords!) and authentication of return values. Therefore, please use it over the *loopback* interface only. If you must use a network connection, wrap it in `stunnel` or similar.
