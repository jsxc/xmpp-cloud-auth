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

Download [the latest release](https://github.com/jsxc/xmpp-cloud-auth/releases)
and put it to your desired location (the documentation and several tools assume
`/opt/xmpp-cloud-auth` throughout). Replace `v1.1.0` with the desired version.
```sh
sudo -s
cd /opt
wget https://github.com/jsxc/xmpp-cloud-auth/archive/v1.1.0.tar.gz
tar xvfz v1.1.0.tar.gz
```

Create the `xcauth` user and directories:
```sh
cd xmpp-cloud-auth
./install.sh
```

Install Python3 and all required libraries. On Ubuntu 18.04, this is:
```sh
apt install python3 python3-requests python3-configargparse python3-bcrypt python3-bsddb3
apt install lua-lpty
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
plugin_paths = { "/opt/xmpp-cloud-auth/prosody" }
```

Ready!
