from weibopy.auth import OAuthHandler, BasicAuthHandler
from weibopy.api import API

class SinaWeibo:
        
    def __init__(self):
            """ constructor """
    
    def getAtt(self, key):
        try:
            return self.obj.__getattribute__(key)
        except Exception, e:
            print e
            return ''
        
    def getAttValue(self, obj, key):
        try:
            return obj.__getattribute__(key)
        except Exception, e:
            print e
            return ''
               
    def auth(self, consumer_key, consumer_secret, access_key, access_secret):
        self.auth = OAuthHandler(consumer_key, consumer_secret)
        self.auth.set_access_token(access_key, access_secret)
        self.api = API(self.auth)
    
    def update(self, message):
        status = self.api.update_status(status=message)
        self.obj = status
        id = self.getAtt("id")
        text = self.getAtt("text")
        
    def destroy_status(self, id):
        status = self.api.destroy_status(id)
        self.obj = status
        id = self.getAtt("id")
        text = self.getAtt("text")

