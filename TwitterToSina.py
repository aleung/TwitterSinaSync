import urllib2;
import logging;
import sys;

from xml.etree import ElementTree;
from google.appengine.ext import db;
from google.appengine.api import urlfetch
from OAuthUpdate import SinaWeibo
from weibopy.error import WeibopError
from db import SyncBinding


def getXmlInTwitter(username,since_id=""):
    xmlUrl = "http://twitter.com/statuses/user_timeline/"+ username + ".xml";
    if since_id != "" and since_id != None:
        xmlUrl += "?since_id=" + since_id;
    opener = urllib2.build_opener();
    req = urllib2.Request(xmlUrl);
    return opener.open(req).read();

    
def filterMsg(message):
    return message.find("@") != 0;

    
def synchronousMsg(CONSUMER_KEY, CONSUMER_SECRET, binding, limit=5):
    weibo = SinaWeibo();  
    text = getXmlInTwitter(binding.twitterId, binding.lastTweetId);
    root = ElementTree.fromstring(text);
    statusNode = root.getiterator("status");
    count = 0
    for node in reversed(statusNode):
    	txt = node.find("text").text.encode("utf-8");
        tID = node.find("id").text.encode("utf-8");
        if filterMsg(txt):
            logging.info("Sync tweet [%s]: %s" % (tID, txt));
            if not hasattr(weibo, "api"):
                weibo.auth(CONSUMER_KEY, CONSUMER_SECRET, binding.sinaAccessToken, binding.sinaAccessSecret);
            try:
                weibo.update(txt);
                count += 1
            except WeibopError, e:
                # ignore "repeated weibo text" error
                if e.reason.find("40025") == -1 or e.reason.find("40028") == -1:
                    raise;
        binding.lastTweetId = tID;
        binding.put();
        if count >= limit:
            return

def syncAll(CONSUMER_KEY, CONSUMER_SECRET):
    bindings = SyncBinding.all()
    bindings.order("nextSyncTime")
    for binding in bindings:
        if binding.nextSyncTime > time():
            return
        logging.debug("Synchronous tweets from @" + binding.twitterId);
        synchronousMsg(CONSUMER_KEY, CONSUMER_SECRET, binding);
        binding.nextSyncTime = time() + 60*10 + random()*60*5 # set next sync to 10~15 minutes later
        binding.put()
