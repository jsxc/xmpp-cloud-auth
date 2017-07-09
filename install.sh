#!/bin/sh
adduser --system --group --home-dir /var/cache/xcauth --gecos "XMPP Cloud Authentication" xcauth
mkdir --mode 640 /var/log/xcauth
chown xcauth:xcauth /var/log/xcauth
