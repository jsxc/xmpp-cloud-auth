#!/bin/sh
dir=`mktemp -d`
# `ConfigArgParse` cannot use /dev/null as the config file
# (bogus 'error: File not found: /dev/null' message)

touch $dir/xcauth.conf
(sleep 5; echo quit) | ./xcauth.py --config-file $dir/xcauth.conf -l $dir -t generic &
pid=$!
sleep 1

# Dump threads to error log
kill -USR1 $pid
sleep 1

# Rotate error log
mv $dir/xcauth.err $dir/xcauth.err.1
kill -HUP $pid
sleep 1

# Dump threads to new error log
kill -USR1 $pid

# Test that both have been used
grep MainThread $dir/xcauth.err > /dev/null && \
	grep MainThread $dir/xcauth.err.1 > /dev/null
res=$?
if [ $res -eq 0 ]; then
	echo "OK"
	rm -rf $dir
	exit 0
else
	echo "Signal handling/log rotation problem, see $dir"
	exit $res
fi
