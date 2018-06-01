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
            if isinstance(response, dict):
                if response['result'] == 'success':
                    return bool(response['data']['isUser'])
                else:
                    return None
            else:
                return None
        except KeyError:
            logging.error('Request for %s@%s returned malformed response: %s'
                % (self.username, self.domain, str(response)))
            return None

    def isuser(self):
        result = self.isuser_cloud()
        if result == None:
            logging.info('Cloud unreachable testing user %s@%s' % (self.username, self.domain))
        elif result == True:
            logging.info('Cloud says user %s@%s exists' % (self.username, self.domain))
        else:
            logging.info('Cloud says user %s@%s does not exist' % (self.username, self.domain))
        return result
