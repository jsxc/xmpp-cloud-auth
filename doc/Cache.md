# User caching

To reduce the impact of short outages of the backend authentication servers and reduce the load, username/password caching has been added.

The cache is consulted after token verification fails (there is no use in caching the tokens, as they are dynamic and can be verified locally).
The passwords are hashed with `bcrypt` before storage, so gaining access to the cache should have no security impact.

To invalidate the cache, authenticate with a different password.
The first login with the new password after changing passwords will thus automatically invalidate the old password and prevent anyone knowing the old password from successfully authenticating.

## Cache behavior

1. If a valid token is passed, succeed immediately
   and do not touch the cache.
1. If the last authentication query was less than `cache-query-ttl` ago,
   **and** the last verification against the backend was less than
   `cache-verification-ttl` ago, **and** the password matches the
   stored one: Record the current query time and succeed.
1. Query the backend database
   - If it is successful, update the cache
   - If the request failed for a reason other than "password incorrect",
     **and** the last verification against the backend was less than
     `cache-unreachable-ttl` ago (independent of the other TTLs), **and**
     the password matches, succeed.

## Cache format

- Key: JID in IDN format
- Value: Tab-separated tuple of
  - `bcrypt()`ed password,
  - Unix timestamp of first successful login,
  - Unix timestamp of most recent successful verification, and
  - Unix timestamp of most recent successful authentication query.

# Shared roster caching

To speed up *ejabberd* shared roster updates, another cache is used. Multiple data sets are stored in the same cache, distinguished by their key spaces:

## Roster Hash Cache format

Used to determine whether a roster update thread should be started at all.

- Key: 'RHC:' + JID
- Value: SHA-256 hash of the body returned for the last processed roster request

## Full Name Cache format

Used to determine whether a 'get_vcard' command needs to be sent to *ejabberdctl*.

- Key: 'FNC:' + JID
- Value: Full name

## Roster Group Cache format

Used to determine whether a 'srg_create' command needs to be sent to *ejabberdctl*.

- Key: 'RGC:' + Group + ':' + Domain
- Value: Tab-separated group members

## Login In Group format

Used to record which groups a user (more precisely, the user currently logging in) belongs to.

This is not a cache in the narrow sense, as erasing this entry will not slow down
operation, but will slow down the removal from groups.

If 'Login In Groups' is persistent, users having been removed from a group will be thrown out of that group *when the first still-member of that group logs in*.

If 'Login In Groups' is not persistent, a user will also be removed from the group *when he logs in himself next*.

So this one results in sooner group membership removal.

- Key: 'LIG:' + JID
- Value: Tab-separated groups this user is member of (when last recorded)
