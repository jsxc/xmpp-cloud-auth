import logging
import hashlib
import hmac
import bcrypt
from datetime import datetime, timedelta
from struct import pack, unpack
from base64 import b64decode
from xclib.utf8 import utf8, unutf8

usersafe_encoding = str.maketrans('-$%', 'OIl')

# Is merged into sigcloud
class auth:
    # First try if it is a valid token
    # Failure may just indicate that we were passed a password
    def auth_token(self):
        try:
            token = b64decode(self.password.translate(usersafe_encoding) + '=======')
        except:
            logging.debug('Not a token (not base64)')
            return False

        jid = self.username + '@' + self.domain

        if len(token) != 23:
            logging.debug('Not a token (len: %d != 23)' % len(token))
            return False

        (version, mac, header) = unpack('> B 16s 6s', token)
        if version != 0:
            logging.debug('Not a token (version: %d != 0)' % version)
            return False;

        (secretID, expiry) = unpack('> H I', header)
        expiry = datetime.utcfromtimestamp(expiry)
        if expiry < self.now:
            logging.debug('Token has expired')
            return False

        challenge = pack('> B 6s %ds' % len(jid), version, header, utf8(jid))
        response = hmac.new(self.secret, challenge, hashlib.sha256).digest()
        if hmac.compare_digest(mac, response[:16]):
            return True
        else:
            logging.warning('Token for %s has invalid signature (possible attack attempt!)' % jid)
            return False

    def auth_cloud(self):
        response = self.cloud_request({
            'operation':'auth',
            'username': self.username,
            'domain':   self.authDomain,
            'password': self.password
        })
        if response and 'result' in response:
            return response['result'] # 'error', 'success', 'noauth'
        return False

    def checkpw(self, pwhash):
        '''Compare self.password with pwhash.
        
        Try to be resistant to timing attacks and use `checkpw` if available.'''
        pw = utf8(self.password)
        pwhash = utf8(pwhash)
        if 'checkpw' in dir(bcrypt):
            return bcrypt.checkpw(pw, pwhash)
        else:
            ret = bcrypt.hashpw(pw, pwhash)
            return ret == pwhash

    def auth_with_cache(self, unreach=False):
        if self.ctx.db.cache_storage == 'none':
            return False
        jid = self.username + '@' + self.domain
        now = self.now # For tests
        for row in self.ctx.db.cache.execute('SELECT pwhash, remoteauth, anyauth FROM authcache WHERE jid = ?', (jid,)):
            (pwhash, tsv, tsa) = row
            if ((tsa + timedelta(seconds=self.ctx.ttls['query']) > now
                and tsv + timedelta(seconds=self.ctx.ttls['verify']) > now)
              or (unreach and tsv + timedelta(seconds=self.ctx.ttls['unreach']) > now)):
                if self.checkpw(pwhash):
                    # Update does not need to be atomic
                    self.ctx.db.cache.execute('UPDATE authcache SET anyauth = ? WHERE jid = ?', (now, jid))
                    return True
        return False

    def auth_update_cache(self):
        if self.ctx.db.cache_storage == 'none':
            return False
        jid = self.username + '@' + self.domain
        now = self.now
        try:
            if self.ctx.db.cache_storage == 'memory':
                rounds = self.ctx.bcrypt_rounds[1]
            else:
                rounds = self.ctx.bcrypt_rounds[0]
            salt = bcrypt.gensalt(rounds=rounds)
        except TypeError:
            # Old versions of bcrypt() apparently do not support the rounds option
            salt = bcrypt.gensalt()
        pwhash = unutf8(bcrypt.hashpw(utf8(self.password), salt))
        # Upsert in SQLite is too new to rely on:
        # https://www.sqlite.org/draft/lang_UPSERT.html
        #
        # INSERT OR REPLACE cannot be used, as it will inherit
        # the DEFAULT values instead of the existing values.
        self.ctx.db.cache.begin()
        self.ctx.db.cache.execute(
                '''INSERT OR IGNORE INTO authcache (jid, firstauth)
                VALUES (?, ?)''',
                (jid, now))
        self.ctx.db.cache.execute(
                '''UPDATE authcache
                SET pwhash = ?, remoteauth = ?, anyauth = ?
                WHERE jid = ?''', (pwhash, now, now, jid))
        self.ctx.db.cache.commit()

    def auth(self):
        if self.auth_token():
            logging.info('SUCCESS: Token for %s@%s is valid'
                    % (self.username, self.domain))
            self.try_roster()
            return True
        if self.auth_with_cache(unreach=False):
            logging.info('SUCCESS: Cache says password for %s@%s is valid'
                    % (self.username, self.domain))
            self.try_roster()
            return True
        r = self.auth_cloud()
        if not r or r == 'error': # Request did not get through (connect, HTTP, signature check)
            cache = self.auth_with_cache(unreach=True)
            logging.info('UNREACHABLE: Cache says password for %s@%s is %r'
                    % (self.username, self.domain, cache))
            # The roster request would be futile
            return cache
        elif r == 'success':
            logging.info('SUCCESS: Cloud says password for %s@%s is valid'
                    % (self.username, self.domain))
            self.auth_update_cache()
            self.try_roster()
            return True
        else: # 'noauth'
            logging.info('FAILURE: Could not authenticate user %s@%s: %s'
                    % (self.username, self.domain, r))
            return False
