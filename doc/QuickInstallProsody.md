# Quick installation for *Prosody*

This documentation assumes that you:
1. already have a working *Prosody* configuration,
1. it works with together *JSXC*, and
1. you have a simple, single-domain, single-purpose installation.

If you need to start from scratch, look at our
[step-by-step tutorial](https://github.com/jsxc/xmpp-cloud-auth/wiki/raspberry-pi-en).
If you have advanced requirements, would like to know background,
or run into trouble with this setup, read the
[full installation instructions](./Installation.md).

## Software installation

Currently, only nightlies are supported, which you get by
```
sudo -s
echo deb https://dl.jsxc.org nightly main > /etc/apt/sources.list.d/jsxc.list
wget -qO - http://dl.jsxc.org/archive.key | sudo apt-key add -
apt update
apt install xcauth
```

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

## Adapt *Prosody* configuration to use `xcauth`

Add the following to your *Prosody* config (probably `/etc/prosody/prosody.cfg.lua`):
```lua
authentication = "external"
external_auth_command = "/opt/xmpp-cloud-auth/xcauth.py"
plugin_paths = { "/opt/xmpp-cloud-auth/prosody-modules/" }
```

Ready!
