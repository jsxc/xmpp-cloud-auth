# Protocol descriptions

Protocols can be separated into two categories:
- Frontend protocols, requests coming in from the XMPP (or other) server: [prosody aka generic](#prosody), [ejabberd](#ejabberd), and [saslauthd](#saslauthd).
- Backend protocols, requests going out to a [JSXC-enabled Nextcloud](#jsxc)

# Frontend protocols

## Prosody

[A line-based, colon-separated protocol](https://modules.prosody.im/mod_auth_external.html#protocol). Requests are newline-terminated, fields in the request colon-separated (variables are in all-caps):

- `isuser:USER:DOMAIN`: Does USER exist at DOMAIN?
- `auth:USER:DOMAIN:PASSWORD`: Is PASSWORD (may include colons!) correct for USER@DOMAIN?
- Any other request receives a failure response

Responses are (newline-terminated):

- `1`: success
- `0`: failure

## ejabberd

A length-prefixed, colon-separated protocol. Requests are prefixed by a two-byte network byte order (big endian) length, fields are colon-separated.

Requests contents are the same as for [Prosody](#prosody) above.

Responses are again length-prefixed, but are themselves a network byte order two-byte value ("short") of

- 1: success
- 0: failure

## saslauthd

The request consists of four fields (USER, PASSWORD, SERVICE, REALM), each prefixed by a two-byte network byte order length. There is no request type, it always corresponds to `auth` above, ignoring SERVICE.

Responses are length-prefixed strings:

- `OK ` + (optional) reason
- `NO ` + (optional) reason

## Postfix

Similar to SMTP. [A line-based, space-separated protocol](http://www.postfix.org/tcp_table.5.html). Requests are of the format `get <user>@<domain>`, newline-terminated. This maps to the `isuser` command; the other commands are not supported.

Responses start with `200 ` (user exists), `400 ` (problem processing the request, try again), or `500 ` (user does not exist), followed by a newline-terminated human-readable explanation.

# Backend protocol

## JSXC
Your XMPP server sends the authentication data in a [special format](https://www.ejabberd.im/files/doc/dev.html#htoc9) on the standard input to the authentication script, length-prefixed (`-t ejabberd`) for *ejabberd*, newline-terminated (`-t prosody` aka `-t generic`) for *Prosody* (and maybe others). The script will first try to verify the given password as time-limited token and if this fails, it will send a HTTP request to your cloud installation to verify this data. To protect your Nextcloud/Owncloud against different attacks, every request has a signature similar to the  [github webhook signature]( https://developer.github.com/webhooks/securing/).

### Time-limited token
The time-limited token has the following structure:
```
# Definitions
version := 'protocol version'
id := 'key id'
expiry := 'end of lifetime as unix timestamp'
user := 'user identifier'
secret := 'shared secret'
name[x] := 'first x bit of name'
. := 'concatenation'

# Calculation
version = hexToBin(0x00)
id = sha256(secret)
challenge = version[8] . id[16] . expiry[32] . user
mac = sha256_mac(challenge, secret)
token = version[8] . mac[128] . id[16] . expiry[32]

# Improve readability
token = base64_encode(token)
token = replace('=', '', token)
token = replace('O', '-', token)
token = replace('I', '$', token)
token = replace('l', '%', token)
```

### Request signature
Every request to the API URL needs a `HTTP_X_JSXC_SIGNATURE` header:
```
body := 'request body'
secret := 'shared secret'

MAC = sha1_hmac(body, secret)

HTTP_X_JSXC_SIGNATURE: sha1=MAC
```
