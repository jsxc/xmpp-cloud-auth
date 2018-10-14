#!/bin/sh
# This will delete a particular group from the cache. To make sure it will
# not reappear, you also have to delete it from Nextcloud.
# If your group name contains spaces or other special characters, it will
# not work.
#
# Usage: xcdelhost <vhost>
# Example: xcdelgroup example.org
#
sqlite3 /var/lib/xcauth/xcauth.sqlite3 'DELETE FROM rostergroups WHERE groupname LIKE "%@'"$1"'";'
sqlite3 /var/lib/xcauth/xcauth.sqlite3 'DELETE FROM rosterinfo WHERE jid LIKE "%@'"$1"'";'
sqlite3 /var/lib/xcauth/xcauth.sqlite3 'DELETE FROM authcache WHERE jid LIKE "%@'"$1"'";'
sqlite3 /var/lib/xcauth/xcauth.sqlite3 'DELETE FROM domains WHERE xmppdomain="'"$1"'";'
