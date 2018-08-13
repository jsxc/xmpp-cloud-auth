# Quick installation for *ejabberd*

This documentation assumes that you:
1. already have a working *ejabberd* configuration,
1. it works with together *JSXC*, and
1. you have a simple, single-domain, single-purpose installation.

If you need to start from scratch, look at our
[step-by-step tutorial](https://github.com/jsxc/xmpp-cloud-auth/wiki/raspberry-pi-en).
If you have advanced requirements, would like to know background,
or run into trouble with this setup, read the
[full installation instructions](./Installation.md).

## Software installation

Download [the latest `xcauth*.deb` package](https://github.com/jsxc/xmpp-cloud-auth/releases)
and install it.

## `xcauth` configuration

:warning: The API secret must not fall into the wrong hands!
Anyone knowing it can authenticate as any user to the XMPP server
(and create arbitrary new users on the XMPP server).

```sh
cp xcauth.conf /etc
chown xcauth:xcauth /etc/xcauth.conf
chmod 660 /etc/xcauth.conf
```
Modify `/etc/xcauth.conf` according to your environment. The values for
API URL and API SECRET can be found in your Nextcloud JSXC admin page.

### Adapt *ejabberd* configuration to use `xcauth`

Add the following to your *ejabberd* config (probably `/etc/ejabberd/ejabberd.yml`):
```YaML
auth_method: external
extauth_program: "/opt/xmpp-cloud-auth/xcauth.py"
auth_use_cache: false
```

Ready!
