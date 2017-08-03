# Database formats

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
Location specified by `--shared-roster-db`, this database is an `andydbm`-based key/value storage.

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
