import urllib.request, urllib.parse, urllib.error
import requests
import hashlib
import hmac
import logging
from time import time
from xclib.isuser import isuser
from xclib.auth import auth
from xclib.roster import roster
from xclib.utf8 import utf8

class sigcloud(isuser, auth, roster):
    def __init__(self, ctx, username, domain, password=None, now=time()):
        self.ctx = ctx
        self.username = username
        self.domain = domain
        self.password = password
        self.secret, self.url, self.authDomain = ctx.per_domain(domain)
        self.now = int(now)

    def cloud_request(self, data):
        '''Performs a signed cloud request on data.
        
        Return values:
        - False: Connection problem
        - JSON: The successful JSON reply
        - int: The HTTP error
        '''
        success, code, message, text = self.verbose_cloud_request(data)
        if success:
            if code is not None and code != requests.codes.ok:
                return code
            else:
                return message
        else:
            return False

    def verbose_cloud_request(self, data):
        '''Perform a signed cloud request on data with detailed result.
        
        Return tuple:
        - (True, None, json, body): Remote side answered with HTTP 200 and JSON body
        - (False, 200, None, None): Remote side answered with HTTP 200, but no JSON
        - (False, int, json, body): Remote side answered != 200, with JSON body
        - (False, int, None, None): Remote side answered != 200, without JSON
        - (False, None, err, None): Connection problem, described in err
        '''
        # logging.debug("Sending %s to %s" % (data, url))
        payload = utf8(urllib.parse.urlencode(data))
        signature = hmac.new(self.secret, msg=payload, digestmod=hashlib.sha1).hexdigest()
        headers = {
            'X-JSXC-SIGNATURE': 'sha1=' + signature,
            'content-type':     'application/x-www-form-urlencoded'
        }
        try:
            r = self.ctx.session.post(self.url, data=payload, headers=headers,
                                  allow_redirects=False, timeout=self.ctx.timeout)
        except requests.exceptions.HTTPError as err:
            logging.warn(err)
            return False, None, err, None
        except requests.exceptions.RequestException as err:
            try:
                logging.warn('An error occured during the request to %s for domain %s: %s' % (self.url, data['domain'], err))
            except TypeError as err:
                logging.warn('An unknown error occured during the request to %s, probably an SSL error. Try updating your "requests" and "urllib" libraries.' % url)
            return False, None, err, None
        if r.status_code != requests.codes.ok:
            try:
                return False, r.status_code, r.json(), r.text
            except ValueError: # Not a valid JSON response
                return False, r.status_code, None, None
        try:
            # Return True only for HTTP 200 with JSON body, False for everything else
            return True, None, r.json(), r.text
        except ValueError: # Not a valid JSON response
            return False, r.status_code, None, None
