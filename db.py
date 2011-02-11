from google.appengine.ext import db;

class SyncBinding(db.Model):
    lastTweetId = db.StringProperty()
    twitterId = db.StringProperty()
    invitationCode = db.StringProperty()
    sinaAccessToken = db.StringProperty()
    sinaAccessSecret = db.StringProperty()
    nextSyncTime = db.FloatProperty()
    
    @staticmethod
    def getOrInsertByInvitationCode(code):
        query = SyncBinding().all()
        query.filter("invitationCode", code)
        binding = query.get()
        if binding == None:
            binding = SyncBinding(invitationCode = code)
        return binding
    
class InvititionCode(db.Model):
    code = db.StringProperty()
