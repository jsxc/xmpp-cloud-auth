#!/bin/sh
# Without `-H`, `ejabberdctl` will not be able to talk to `ejabberd`
# If your `ejabberdctl` is somewhere else, please symlink it from `/usr/sbin`
exec sudo -H -u ejabberd /usr/sbin/ejabberdctl "$@"
