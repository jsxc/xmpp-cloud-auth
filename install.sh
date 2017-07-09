#!/bin/sh
adduser --system --group --home /var/cache/xcauth --gecos "XMPP Cloud Authentication" xcauth
mkdir --mode 640 /var/log/xcauth
chown xcauth:xcauth /var/log/xcauth
