#!/bin/sh
unset LD_LIBRARY_PATH
unset DYLD_LIBRARY_PATH
exec `dirname $0`/`basename $0 .sh`.py "$@"
