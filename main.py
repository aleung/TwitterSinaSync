# -*- coding: utf-8 -*-

import wsgiref.handlers, logging, random, string
from google.appengine.ext import webapp
from weibopy.auth import OAuthHandler
from db import SyncBinding, InvititionCode
from TwitterToSina import syncAll

# --- Update following -------------
CONSUMER_KEY = ''
CONSUMER_SECRET = ''
# ----------------------------------

    
page_goto_sina_oauth = """
<html>
<body>
<p>Step 1: <a href="%(url)s" target="_blank">点击这里，获取新浪微博授权码</a></p>
<p>Step 2: 输入授权码 
<form action="register" method="get">
<input type="hidden" name="invitation_code" value="%(invitation)s"/>
<input type="hidden" name="request_token" value="%(token)s"/>
<input type="hidden" name="request_secret" value="%(secret)s"/>
新浪授权码：<input type="text" name="oauth_verifier" />
Twitter ID：<input type="text" name="twitter_id" />
<input type="submit" value="确认" />
</form></p>
</body>
</html>
    """    

def success_output(handler, content, content_type='text/html'):
    handler.response.status = '200 OK'
    handler.response.headers.add_header('Content-Type', content_type)
    handler.response.out.write(content)

def error_output(handler, content, content_type='text/html', status=503):
    handler.response.set_status(503)
    handler.response.headers.add_header('Content-Type', content_type)
    handler.response.out.write("Server Error:<br />")
    return handler.response.out.write(content)

def compress_buf(buf):
    zbuf = StringIO.StringIO()
    zfile = gzip.GzipFile(None, 'wb', 9, zbuf)
    zfile.write(buf)
    zfile.close()
    return zbuf.getvalue()

        
# /register?invitation_code=123456
class RegisterHandler(webapp.RequestHandler):
    def get(self):
        invitationCode = self.request.get('invitation_code')
        if not self.isValidInvitationCode(invitationCode):
            error_output(self, "<html><body>邀请码无效</body></html>", "text/html", 400)
            return
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        
        verifier = self.request.get("oauth_verifier")
        twitterId = self.request.get("twitter_id")
        if verifier == "" or twitterId == "":
            authUrl = auth.get_authorization_url()
            success_output(self, page_goto_sina_oauth % \
                {'url':authUrl, 
                 'invitation':invitationCode.encode('UTF-8'),
                 'token':auth.request_token.key, 
                 'secret':auth.request_token.secret})
        else:
            request_token = self.request.get("request_token")
            request_secret = self.request.get("request_secret")
            auth.set_request_token(request_token, request_secret)
            accessToken = auth.get_access_token(verifier)
            binding = SyncBinding()
            binding.twitterId = twitterId
            binding.invitationCode = invitationCode
            binding.sinaAccessToken = accessToken.key
            binding.sinaAccessSecret = accessToken.secret
            binding.put()
            success_output(self, "<html><body>Twitter与新浪微博同步绑定成功</body></html>")

    def isValidInvitationCode(self, code):
        query = InvititionCode.all()
        query.filter("code =", code)
        return query.count(1) > 0

class BindingListHandler(webapp.RequestHandler):
    def get(self):
        content = """
<html><body><table border="1">
<tr><th>Invatation Code</th><th>Twitter ID</th><th>Last synced tweet</th>
<th>Sina token</th><th>Sina secret</th></tr>
            """
        bindings = SyncBinding.all()
        for binding in bindings:
            content += "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % \
                (binding.invitationCode, binding.twitterId, binding.lastTweetId, 
                 binding.sinaAccessToken, binding.sinaAccessSecret)
        content += "</table></body></html>"
        success_output(self, content)

        
class InvitationHandler(webapp.RequestHandler):
    def get(self):
        code = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(8))
        invitation = InvititionCode(code=code)
        invitation.put()
        success_output(self, 
            "<html><body>邀请链接：%s?invitation_code=%s</body></html>" % \
            (self.request.relative_url('../register'), code))
        
class SyncHandler(webapp.RequestHandler):
    def get(self):
        syncAll(CONSUMER_KEY, CONSUMER_SECRET)
        
def main():
    application = webapp.WSGIApplication( [
        (r'/sync', SyncHandler),
        (r'/register', RegisterHandler),
        (r'/admin/bindings', BindingListHandler),
        (r'/admin/invitation', InvitationHandler),
        ], debug=True)
    wsgiref.handlers.CGIHandler().run(application)
    
if __name__ == "__main__":
  logging.getLogger().setLevel(logging.DEBUG);
  main()
