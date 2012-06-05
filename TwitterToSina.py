import urllib2
import logging
import sys, time, random
import tweet

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
    try:
        return opener.open(req).read()
    except urllib2.HTTPError, error:
        logging.error("Got error response from twitter:\n" + error.read())
        logging.debug("RateLimit-Limit=" + error.info()['X-RateLimit-Limit'])
        logging.debug("RateLimit-Remaining=" + error.info()['X-RateLimit-Remaining'])
        logging.debug("RateLimit-Reset=" + error.info()['X-RateLimit-Reset'])
        raise

    
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
            txt = tweet.expand_url_in_tweet(txt)
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
                # 40028: the tweet is duplicated or user is in black list
                # 40092: link contains illegal website
                if e.reason.find("40028") != -1 or e.reason.find("40092") != -1:
                    logging.info("Tweet is censored. Skip this tweet and temporary disable sync for 1 hour. " + e.reason)
                    binding.nextSyncTime = time.time() + 3600
                    binding.lastTweetId = tID
                    binding.put()
                    return
                # ignore "repeated weibo text" error
                if e.reason.find("40025") != -1:
                    logging.info("Error ignored: " + e.reason)
                else:
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
