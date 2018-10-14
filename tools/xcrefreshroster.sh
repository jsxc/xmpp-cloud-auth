#!/bin/sh
# This will cause the roster groups to be rebuilt on the next login of
# one of their users.
# Necessary when the XMPP server's state differs from the cache, e.g.,
# because of manual modifications.
sqlite3 /var/lib/xcauth/xcauth.sqlite3 'UPDATE rosterinfo SET fullname=NULL, grouplist=NULL, responsehash=NULL;'
