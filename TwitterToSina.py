import urllib2;
import logging;
import sys, time, random

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
    logging.debug("Synchronous tweets from @" + binding.twitterId);
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
                # handle error: user has revoked access privilege to this application
                if e.reason.find("40072") != -1:
                    logging.info("Delete binding, because user has revoked access privilege for this application from Sina: " + e.reason);
                    binding.delete()
                    return
                # 40028 indicates that the tweet is duplicated or user is in black list
                if e.reason.find("40028") != -1:
                    logging.info("User is in black list? Skip this tweet and temporary disable sync for 1 hour. " + e.reason)
                    binding.nextSyncTime = time.time() + 3600
                    binding.lastTweetId = tID
                    binding.put()
                    return
                # ignore "repeated weibo text" error
                if e.reason.find("40025") != -1:
                    logging.info("Error ignored: " + e.reason)
                    break
                # other error
                raise
        binding.lastTweetId = tID;
        binding.put();
        if count >= limit:
            break
    binding.nextSyncTime = time.time() + 60*(10+5*random.random()) - count*60*2
    binding.put();
    logging.info("Twitter ID: %s, next sync: %f" % (binding.twitterId, binding.nextSyncTime))

def syncAll(CONSUMER_KEY, CONSUMER_SECRET):
    bindings = SyncBinding.all()
    bindings.order("nextSyncTime")
    for binding in bindings:
        if binding.nextSyncTime > time.time():
            return
        synchronousMsg(CONSUMER_KEY, CONSUMER_SECRET, binding);
