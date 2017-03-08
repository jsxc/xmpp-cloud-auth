# ejabberd-cloud-auth

This authentication script for [ejabberd]() (and also [prosody]()) allows to authenticate against a
[Nextcloud]()/[Owncloud]() instance running [OJSXC]() (>= 3.2.0).

## Installation
Download [external_cloud.py]() and put it to your desired location or clone this repository to simplify updates:
```
cd /opt
git clone https://github.com/jsxc/ejabberd-cloud-auth
```

Make the script executable and give your ejabberd/prosody user sufficient rights:
```
chmod u+x ejabberd-cloud-auth/external_cloud.py
chown USER:GROUP -R ejabberd-cloud-auth
```

Install python and all desired libraries.
```
sudo apt-get install python python-pip
sudo -u USER -H pip install requests
```

### Ejabberd
Adjust your configuration as described in the [admin manual](https://docs.ejabberd.im/admin/configuration/#external-script).

```
vim /etc/ejabberd/ejabberd.yml

auth_method: external
extauth_program: "/opt/ejabberd-cloud-auth/external_cloud.py --url=APIURL --secret=APISECRET"
```
You will find the values for `APIURL` and `APISECRET` on your Nextcloud/Owncloud admin page.

:warning: On Ubuntu ejabberd will come with an **apparmor** profile which will block the external authentication script.
 See also the related [issue](https://github.com/processone/ejabberd/issues/1598).

### Prosody
Install [mod_auth_external](https://modules.prosody.im/mod_auth_external.html) and add the following to your config:
```
authentication = "external"
external_auth_protocol = "ejabberd"
external_auth_command = "/opt/ejabberd-cloud-auth/external_cloud.py --url=APIURL --secret=APISECRET --log=/var/log/prosody"
```
You will find the values for `APIURL` and `APISECRET` on your Nextcloud/Owncloud admin page.

:warning: The current module has some issue, see also [#1](https://github.com/jsxc/ejabberd-cloud-auth/issues/1) and [#2](https://github.com/jsxc/ejabberd-cloud-auth/issues/2).

## Options
```
$ ./external_cloud.py --help
usage: external_cloud.py [-h] -u URL -s SECRET [-l LOG] [-d]

ejabberd authentication script

optional arguments:
  -h, --help            show this help message and exit
  -u URL, --url URL     base URL
  -s SECRET, --secret SECRET
                        secure api token
  -l LOG, --log LOG     log directory (default: /var/log/ejabberd)
  -d, --debug           toggle debug mode
```

## How does it work?
Your XMPP server sends the authentication data in a [special format](https://www.ejabberd.im/files/doc/dev.html#htoc9) on the standard input to the authentication script. The script will send a HTTP request to your cloud installation to verify this data. To protect your Nextcloud/Owncloud against different attacks, every request has a signature similar to the  [github webhook signature]( https://developer.github.com/webhooks/securing/).
