# xmpp-cloud-auth

This authentication script for [ejabberd](https://www.ejabberd.im) and [prosody](https://prosody.im) allows to authenticate against a
[Nextcloud](https://nextcloud.com)/[Owncloud](https://owncloud.org) instance running [OJSXC](https://www.jsxc.org) (>= 3.2.0).


## Installation
Download [external_cloud.py](https://raw.githubusercontent.com/jsxc/xmpp-cloud-auth/master/external_cloud.py) and
put it to your desired location or clone this repository to simplify updates:
```
cd /opt
git clone https://github.com/jsxc/xmpp-cloud-auth
```

Make the script executable and give your ejabberd/prosody user sufficient rights:
```
chmod u+x xmpp-cloud-auth/external_cloud.py
chown USER:GROUP -R xmpp-cloud-auth
```

Install python and all desired libraries.
```
sudo apt-get install python python-requests python-configargparse
```
OR
```
sudo apt-get install python python-pip
sudo -u USER -H pip install requests ConfigArgParse
```

## Configuration

1. Copy `external_cloud.conf` to `/etc` as root and restrict the access rights
   (e.g., `chown ejabberd /etc/external_cloud.conf; chmod 600 /etc/external_cloud.conf`)
1. Modify `/etc/external_cloud.conf` according to your environment. The values for 
   API URL and API SECRET can be found in your Nextcloud/ownCloud JSXC admin page.
1. Adapt your ejabberd/prosody configuration to use this authentication script:

### ejabberd
Adjust your configuration as described in the [admin manual](https://docs.ejabberd.im/admin/configuration/#external-script).
```
vim /etc/ejabberd/ejabberd.yml

auth_method: external
extauth_program: "/opt/xmpp-cloud-auth/external_cloud.sh"
```
:warning: On Ubuntu, `ejabberd` will come with an **apparmor** profile which will block the external authentication script.
See also the related issue [ejabberd#1598](https://github.com/processone/ejabberd/issues/1598).

:warning: This starts `external_cloud.sh`, as some **ejabberd** installations will lead to shared library conflicts,
preventing HTTPS access from within Python. The shell wrapper prevents this conflict.

### Prosody
Add the following to your config:
```
authentication = "external"
external_auth_command = "/opt/ejabberd-cloud-auth/external_cloud.py"
```
:warning: The Prosody `mod_auth_external.lua` only accepts a command name, no parameters
([xmpp-cloud-auth#2](https://github.com/jsxc/xmpp-cloud-auth/issues/2), [Prosody#841](https://prosody.im/issues/issue/841)).
All parameters must therefore be set in the configuration file.

## Options
```
$ ./external_cloud.py --help
usage: external_cloud.py [-h] [-c CONFIG_FILE] -u URL -s SECRET [-l LOG] [-d]
                         [-t {prosody,ejabberd}] [-A USER DOMAIN PASSWORD]
                         [-I USER DOMAIN] [--version]

XMPP server authentication against JSXC>=3.2.0 on Nextcloud. See
https://jsxc.org or https://github.com/jsxc/xmpp-cloud-auth. Args that start
with '--' (eg. -u) can also be set in a config file (/etc/external_cloud.conf
or ./external_cloud.conf or specified via -c). Config file syntax allows:
key=value, flag=true, stuff=[a,b,c] (for details, see syntax at
https://goo.gl/R74nmi). If an arg is specified in more than one place, then
commandline values override config file values which override defaults.

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        config file path
  -u URL, --url URL     base URL
  -s SECRET, --secret SECRET
                        secure api token
  -l LOG, --log LOG     log directory (default: /var/log/ejabberd)
  -d, --debug           enable debug mode
  -t {prosody,ejabberd}, --type {prosody,ejabberd}
                        XMPP server type; implies reading requests from stdin
                        until EOF
  -A USER DOMAIN PASSWORD, --auth-test USER DOMAIN PASSWORD
                        single, one-shot query of the user, domain, and
                        password triple
  -I USER DOMAIN, --isuser-test USER DOMAIN
                        single, one-shot query of the user and domain tuple
  --version             show program's version number and exit

One of -A, -I, and -t is required. If more than one is given, -A takes
precedence over -I over -t. -A and -I imply -d.
```


## Troubleshooting
In case you are need some additional debugging, you can try and run `external_cloud.py` from the command line with the usual options and then add '-A jane.doe example.com p4ssw0rd' to test the connection to the ownCloud/Nextcloud server.

If Conversations cannot connect and complains about "Downgrade attack", see the following issue:
[No (obvious?) way to accept SASL downgrade (Conversations#2498)](https://github.com/siacs/Conversations/issues/2498).
Current workaround: Delete the account in Conversations and then add it again.


## How does it work?
Your XMPP server sends the authentication data in a [special format](https://www.ejabberd.im/files/doc/dev.html#htoc9) on the standard input to the authentication script. The script will first try to verify the given password as time-limited token and if this fails, it will send a HTTP request to your cloud installation to verify this data. To protect your Nextcloud/Owncloud against different attacks, every request has a signature similar to the  [github webhook signature]( https://developer.github.com/webhooks/securing/).

### Time-limited token
The time-limited token has the following structure:
```
# Definitions
version := 'protocol version'
id := 'key id'
expiry := 'end of lifetime as unix timestamp'
user := 'user identifier'
secret := 'shared secret'
name[x] := 'first x bit of name'
, := 'concatenation'

# Calculation
version = hexToBin(0x00)
id = sha256(secret)
challenge = version[8],id[16],expiry[32],user
mac = sha256_mac(challenge, secret)
token = version[8],mac[128],id[16],expiry[32]

# Improve readability
token = base64_encode(token)
token = replace('=', '', token)
token = replace('O', '-', token)
token = replace('I', '$', token)
token = replace('l', '%', token)
```

### Request signature
Every request to the API URL needs a `HTTP_X_JSXC_SIGNATURE` header:
```
body := 'request body'
secret := 'shared secret'

MAC = sha1_hmac(body, secret)

HTTP_X_JSXC_SIGNATURE: sha1=MAC
```
