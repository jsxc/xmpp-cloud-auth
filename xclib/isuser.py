import logging

class isuser:
    def __init__(self, reqdata):
        self.reqdata = reqdata

    def isuser_cloud(self):
        response = self.cloud_request({
            'operation': 'isuser',
            'username':  self.username,
            'domain':    self.authDomain
        })
        try:
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
