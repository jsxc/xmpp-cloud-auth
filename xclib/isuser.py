import logging

class isuser:
    def __init__(self, reqdata):
        self.reqdata = reqdata

    def isuser_verbose(self):
        success, code, response, text = self.verbose_cloud_request({
            'operation': 'isuser',
            'username':  self.username,
            'domain':    self.authDomain
        })
        return success, code, response

    def isuser_cloud(self):
        '''Returns:
- True when user exists
- False when user does not exist
- None when there is a problem (connection failure or HTTP error code)'''
        response = self.cloud_request({
            'operation': 'isuser',
            'username':  self.username,
            'domain':    self.authDomain
        })
        try:
            if response == False or isinstance(response, int):
                return None
            return response and response['result'] == 'success' and response['data']['isUser']
        except KeyError:
            logging.error('Request for %s@%s returned malformed response: %s'
                % (self.username, self.domain, str(response)))
            return False

    def isuser(self):
        if self.isuser_cloud():
            logging.info('Cloud says user %s@%s exists' % (self.username, self.domain))
            return True
        return False
