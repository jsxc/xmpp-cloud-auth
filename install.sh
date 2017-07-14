#!/bin/bash
adduser --system --group --home /var/cache/xcauth --gecos "XMPP Cloud Authentication" xcauth
# Add group xcauth to users prosody, ejabberd, if they exist
groups prosody > /dev/null 2>&1 && adduser prosody xcauth
groups ejabberd > /dev/null 2>&1 && adduser ejabberd xcauth
mkdir /var/log/xcauth
chmod 770 /var/{log,cache}/xcauth
chown xcauth:xcauth /var/log/xcauth
