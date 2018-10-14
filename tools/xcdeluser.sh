#!/bin/sh
# This will delete most of a user's entries from the database.
# Not purged are group memberships, as they will be auto-updated on the
# next login of another member of that group (and cannot easily be dealt
# with using SQL statements).
#
# Usage: xcdeluser <jid>
# Example: xcdeluser joe@example.org
#
sqlite3 /var/lib/xcauth/xcauth.sqlite3 'DELETE FROM rosterinfo WHERE jid="'"$1"'";'
sqlite3 /var/lib/xcauth/xcauth.sqlite3 'DELETE FROM authcache WHERE jid="'"$1"'";'
