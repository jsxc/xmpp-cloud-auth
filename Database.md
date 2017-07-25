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
