# New `sqlite` database format

## Domains
```sql
CREATE TABLE domains (xmppdomain TEXT PRIMARY KEY,
                      authsecret TEXT,
                      authurl    TEXT,
                      authdomain TEXT,
                      regcontact TEXT,
                      regfirst   TEXT DEFAULT datetime('now'),
                      reglatest  TEXT DEFAULT datetime('now'));
```
The `xmppdomain` is the part behind the `@` in the XMPP JID
(aka "the XMPP address"). The `authurl` is then contacted with
the users "local part" (the part in front of the `@` and the `authdomain`)
to obtain information about this user. This request is authenticated based
on the `authsecret`.

If your email address on the Nextcloud server is the same as your XMPP domain,
then `xmppdomain` and `authdomain` will match.

`regcontact` (registration contact), `regfirst` (first registration), and
`reglatest` (latest registration) are currently not used by `xcauth` itself.
They may be freely used by configuration-related tools.

## Account cache

```sql
CREATE TABLE authcache (jid        TEXT PRIMARY KEY,
                        pwhash     TEXT,
                        firstauth  TEXT DEFAULT datetime('now'),
                        anyauth    TEXT DEFAULT datetime('now'),
                        remoteauth TEXT DEFAULT datetime('now'));
```

The authentication cache can reduce the load on the remote Nextcloud
server and will gloss over short-term unreachability of that server.
However, it uses more computation power locally to securely encrypt
the password as a `pwhash`. If the Nextcloud server is local and
reliable, it is recommended not to enable the authentication cache.

The lookup is based on the `jid` (the XMPP ID) and stores
- the first time the user authenticated (`firstauth`),
- the most recent authentication accepted by the Nextcloud server
  (`remoteauth`), and
- the most recent authentication by the user, either against the cache
  or against the Nextcloud server (`anyauth`).

## Shared roster cache

```sql
CREATE TABLE rosterinfo   (jid          TEXT PRIMARY KEY,
                           fullname     TEXT,
                           grouplist    TEXT,
                           responsehash TEXT);
CREATE TABLE rostergroups (groupname    TEXT PRIMARY KEY,
                           userlist     TEXT);
```

The `rosterinfo` table contains information about a user
(represented by its `jid`): the full name (`fullname`),
a tab-separated list of groups (`grouplist`),
and the SHA-256 hash of the roster response body (`responsehash`).

The `rostergroups` table contains the tab-separated list of users
(`userlist`) that have been added to a group (identified by `groupname`).

Memberships in `rosterinfo` and `rostergroups` do not necessarily need
to be reciprocal.

## Automatic conversion
When a version of `xcauth` with sqlite support is run, and the `sqlite`
database file does not exist, the database is created and the current values
of the legacy files pointed to by `--domain-db`, `--cache-db`,
and `--shared-roster-db` are imported.


# Legacy database formats (<=1.0)

## Domain DB
Location specified by `--domain-db`, this database is an `andybm`-based key/value storage.

- key: Domainpart of JID
- value: A tab-separated tuple
  1. API secret
  2. API URL
  3. Authentication domain (the one JSXC should check against)
  4. Unused value, can be used by other users of the database (must not contain a tab, as this will interfere with future database field updates)

## User Cache
Location specified by `--cache-db`, this database is an `andydbm`-based key/value storage.

- key: username`:`domain (a bare JID with ':' instead of '@')
- value: A tab-separated tuple
  1. Password hash (for local verification)
  2. Timestamp of first authentication
  3. Timestamp of last successful authentication (possibly local-only)
  4. Timestamp of last successful authentication against the server
  5. Unused value, can be used by other users of the database (must not contain a tab, as this will interfere with future database field updates)

## Shared Roster
Location specified by `--shared-roster-db`, this database is an `anydbm`-based key/value storage.

It contains two types of key/value pairs, differentiated whether the key contains one or two colons (`:`):

### User memberships

This is needed for removing a user from a group (s)he was in earlier. They should not be
deleted unless they become empty

- key: username`:`domain (a bare JID with ':' instead of '@')
- value: A tab-separated list of shared roster group IDs the user was in on the most recent login

### Response cache

This is used to avoid the many expensive `ejabberdctl` calls required otherwise.
They can be deleted without affecting functionality, but affecting performance.

- key: `CACHE:`username`:`domain (a bare JID with ':' instead of '@', prefixed with 'CACHE:')
- value: SHA256(`response body`)
