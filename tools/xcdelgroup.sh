#!/bin/sh
# This will delete a particular group from the cache. To make sure it will
# not reappear, you also have to delete it from Nextcloud.
# If your group name contains spaces or other special characters, it will
# not work.
#
# Usage: xcdelgroup <group-jid>
# Example: xcdelgroup employees@example.org
#
sqlite3 /var/lib/xcauth/xcauth.sqlite3 'DELETE FROM rostergroups WHERE groupname="'"$1"'";'
xcejabberdctl srg_delete `echo $1 | tr @ ' '`
