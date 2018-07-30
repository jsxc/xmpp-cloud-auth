#!/bin/sh
cd /etc/systemd/system && for i in xc*.socket; do
	systemctl start $i
done
