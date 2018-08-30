#!/bin/sh
# Without `-H`, `ejabberdctl` will not be able to talk to `ejabberd`
# If your `ejabberdctl` is somewhere else, please do one of the following:
#
# * Change the path in this file (will require you to redo this whenever
#   you update *xcauth*)
# * Create a file with the following contents in `/usr/sbin/ejabberdctl`
#   and `chmod 755 /usr/sbin/ejabberdctl`:
#   ```sh
#   #!/bin/sh
#   exec <real-path-to>/ejabberdctl "$@"
#   ```
#   (of course, replace <real-path-to> with the real path).
#
# (symlinking your real `ejabberdctl` from `/usr/sbin` does not work,
# as the path of from which it was launched is used to determine the
# *ejabberd* installation directory)
exec sudo -H -u ejabberd /usr/sbin/ejabberdctl "$@"
