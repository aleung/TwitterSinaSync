import urllib2;
import logging;
import sys;

from xml.etree import ElementTree;
from google.appengine.ext import db;
from google.appengine.api import urlfetch
from BasicAuthUpdate import SinaWeibo
from weibopy.error import WeibopError
class SinceID(db.Model):
    value = db.StringProperty();

def getXmlInTwitter(username,since_id=""):
    xmlUrl = "http://twitter.com/statuses/user_timeline/"+ username + ".xml";
    if since_id != "":
        xmlUrl = xmlUrl + "?since_id=" + since_id;
    opener = urllib2.build_opener();
    req = urllib2.Request(xmlUrl);
    return opener.open(req).read();


def synchronousMsg(twitterUsername, sinaUsername, sinaPassword):
    sinceID = SinceID.get_or_insert("since_id",value="");
    logging.debug(sinceID.value);
    text = getXmlInTwitter(twitterUsername,sinceID.value);
    root = ElementTree.fromstring(text);
    statusNode = root.getiterator("status");
    initialized = 0;
    weibo = SinaWeibo();     
    for node in reversed(statusNode):
    	tContent = node.find("text");
        tID = node.find("id");
        txt = tContent.text.encode("utf-8");
        logging.debug(txt);
        if txt.find("@") == -1:
            if initialized != 1:
                weibo.basicAuth('<app_key>', sinaUsername, sinaPassword);
                initialized = 1;
            logging.debug(txt);
            try:
                weibo.update(txt);
            except WeibopError:
                reason = sys.exc_info()[1].reason;
                if reason.find("repeated weibo text!") !=-1:
                    pass;
                else:
                    raise;
        sinceID.value = tID.text.encode("utf-8");
        sinceID.put();
#========================================================
logging.getLogger().setLevel(logging.ERROR);
synchronousMsg(twitterUsername="<user>", sinaUsername="<user>", sinaPassword="<pw>");
