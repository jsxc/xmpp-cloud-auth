# *systemd* socket configuration support

For some environments, it might be advantageous to use *xcauth* over a network socket. Here is a pair of sample *systemd* configuration files, accepting network connection to `localhost:23664`.

## Installation (as root)

1. Perform the *xcauth* installation as explained in the [parent README](../README.md) or the [installation wiki](https://github.com/jsxc/xcauth/wiki). Especially install source into `/opt/xcauth` and put the configuration in `/etc/xcauth.conf`.
1. Copy `xcauth@.service` and `xcauth.socket` to `/etc/systemd/system` (if no modifications to these files are needed, you may also symlink them manually or using `systemctl link`; beware that some versions of *systemd* have problems with symlinks ([systemd#3010](https://github.com/systemd/systemd/issues/3010))
1. Create the user `xcauth`: `adduser --system --group xcauth`
1. Activate the service: `systemctl enable xcauth.socket` and `systemctl start xcauth.socket`

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

:warning: For security reasons, you might want to limit who can use this service over the network. Also, as `xcauth` is meant for local use, it does not support encryption (and therefore, confidentiality) of the commands (including passwords!) and authentication of return values. Therefore, please use it over the *loopback* interface only. If you must use a network connection, wrap it in `stunnel` or similar.
