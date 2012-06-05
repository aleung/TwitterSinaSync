import re
import urllib2
import logging


def expand_url_in_tweet(tweet):
    return re.sub('https?://t\.co/\w*', lambda matchObj: resolve_shorten_url(matchObj.group(0)), tweet)


def resolve_shorten_url(url):
    """ Try to resolve an URL """
    logging.debug("Try to resolve URL " + url)
    opener = urllib2.OpenerDirector()
    opener.add_handler(urllib2.HTTPHandler())
    opener.add_handler(urllib2.HTTPSHandler())
    opener.add_handler(urllib2.HTTPDefaultErrorHandler())
    urllib2.install_opener(opener) 
    f = urllib2.urlopen(url)
    return f.info().getheader('Location')

