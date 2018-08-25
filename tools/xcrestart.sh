#!/bin/sh
echo "Stopping xcauth.service, if running"
systemctl -q stop xcauth.service
echo "(Re-)starting listening sockets"
cd /etc/systemd/system && for i in xc*.socket; do
	systemctl start $i
done
