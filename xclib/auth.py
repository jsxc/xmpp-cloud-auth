import logging
import hashlib
import hmac
import bcrypt
from time import time
from struct import pack, unpack
from base64 import b64decode
from xclib.utf8 import utf8, unutf8

usersafe_encoding = str.maketrans('-$%', 'OIl')

class auth:
    def __init__(self, reqdata):
        self.reqdata = reqdata

    # First try if it is a valid token
    # Failure may just indicate that we were passed a password
    def auth_token(self):
        try:
            token = b64decode(self.password.translate(usersafe_encoding) + '=======')
        except:
            logging.debug('Could not decode token (maybe not a token?)')
            return False

        jid = self.username + '@' + self.domain

        if len(token) != 23:
            logging.debug('Token is too short: %d != 23 (maybe not a token?)' % len(token))
            return False

        (version, mac, header) = unpack('> B 16s 6s', token)
        if version != 0:
            logging.debug('Wrong token version (maybe not a token?)')
            return False;

        (secretID, expiry) = unpack('> H I', header)
        if expiry < self.now:
            logging.debug('Token has expired')
            return False

        challenge = pack('> B 6s %ds' % len(jid), version, header, utf8(jid))
        response = hmac.new(self.secret, challenge, hashlib.sha256).digest()

        return hmac.compare_digest(mac, response[:16])

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

    def try_db_sync(self):
        '''sync() only works on real databases

        Therefore, we allow it to fail, especially in nosetests'''
        try:
            self.ctx.cache_db.sync()
        except AttributeError:
            pass


    def auth_with_cache(self, unreach=False):
        key = self.username + ':' + self.domain
        if key in self.ctx.cache_db:
            now = self.now
            (pwhash, ts1, tsv, tsa, rest) = self.ctx.cache_db[key].split("\t", 4)
            if ((int(tsa) + self.ctx.ttls['query'] > now and int(tsv) + self.ctx.ttls['verify'] > now)
               or (unreach and int(tsv) + self.ctx.ttls['unreach'] > now)):
                if self.checkpw(pwhash):
                    self.ctx.cache_db[key] = "\t".join((pwhash, ts1, tsv, str(now), rest))
                    self.try_db_sync()
                    return True
        return False

    def auth_update_cache(self):
        if '' in self.ctx.cache_db: # Cache disabled?
            return
        key = self.username + ':' + self.domain
        now = self.now # For tests
        snow = str(now)
        try:
            salt = bcrypt.gensalt(rounds=self.ctx.bcrypt_rounds)
        except TypeError:
            # Old versions of bcrypt() apparently do not support the rounds option
            salt = bcrypt.gensalt()
        pwhash = unutf8(bcrypt.hashpw(utf8(self.password), salt))
        if key in self.ctx.cache_db:
            (ignored, ts1, tsv, tsa, rest) = self.ctx.cache_db[key].split("\t", 4)
            self.ctx.cache_db[key] = "\t".join((pwhash, ts1, snow, snow, rest))
        else:
            self.ctx.cache_db[key] = "\t".join((pwhash, snow, snow, snow, ''))
        self.try_db_sync()

    def auth(self):
        if self.auth_token():
            logging.info('SUCCESS: Token for %s@%s is valid' % (self.username, self.domain))
            self.try_roster()
            return True
        if self.auth_with_cache(unreach=False):
            logging.info('SUCCESS: Cache says password for %s@%s is valid' % (self.username, self.domain))
            self.try_roster()
            return True
        r = self.auth_cloud()
        if not r or r == 'error': # Request did not get through (connect, HTTP, signature check)
            cache = self.auth_with_cache(unreach=True)
            logging.info('UNREACHABLE: Cache says password for %s@%s is %r' % (self.username, self.domain, cache))
            # The roster request would be futile
            return cache
        elif r == 'success':
            logging.info('SUCCESS: Cloud says password for %s@%s is valid' % (self.username, self.domain))
            self.auth_update_cache()
            self.try_roster()
            return True
        else: # 'noauth'
            logging.info('FAILURE: Could not authenticate user %s@%s: %s' % (self.username, self.domain, r))
            return False
