from google.appengine.ext import db;

class SyncBinding(db.Model):
    lastTweetId = db.StringProperty()
    twitterId = db.StringProperty()
    invitationCode = db.StringProperty()
    sinaAccessToken = db.StringProperty()
    sinaAccessSecret = db.StringProperty()
    
class InvititionCode(db.Model):
    code = db.StringProperty()
