""" Misc functions """

import os, logging
from base64 import b64decode
from urllib import urlencode, quote as urlquote

import data
import constants
import queries

def quote(s,safe='/'):
    """ URL-encoding string similar to urllib.quote().
    This version includes workaround for Python bug:

    http://mail.python.org/pipermail/python-dev/2006-July/067248.html
    """
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    return urlquote(s,safe)

def getGroupRSS_URL(screen_name, rss_token, group_name, use_HTTP_auth):
    if use_HTTP_auth:
        return "http://%s%s/%s/%s" % \
               (constants.DOMAIN,
                constants.FEED_PATH_PREFIX,
                quote(screen_name), quote(group_name))
    else:
        return "http://%s%s/%s/%s?%s" % \
               (constants.DOMAIN,
                constants.FEED_PATH_PREFIX,
                quote(screen_name), quote(group_name),
                urlencode({constants.TOKEN_PARAM_NAME : rss_token}))

def getGroupTitle(group_name):
    if group_name == constants.DEFAULT_GROUP_NAME:
        return "Uncategorized"
    return group_name

def getGroupRSS_title(screen_name, group_name):
    return "%s/%s @tweetonica" % (screen_name, getGroupTitle(group_name))


def getOPML_URL(screen_name, rss_token, use_HTTP_auth):
    if use_HTTP_auth:
        return "http://%s%s/%s" % \
               (constants.DOMAIN,
                constants.OPML_PATH_PREFIX,
                quote(screen_name))
    else:
        return "http://%s%s/%s?%s" % \
               (constants.DOMAIN,
                constants.OPML_PATH_PREFIX,
                quote(screen_name),
                urlencode({constants.TOKEN_PARAM_NAME : rss_token}))

def HTTP_authenticate():
    if not os.environ.has_key('HTTP_AUTHORIZATION'):
        return None
    ah = os.environ['HTTP_AUTHORIZATION']
    logging.debug("Auth header: %s" % ah)
    if not ah or len(ah)<6:
        logging.warning("Invalid auth string '%s'" % ah)
        return None
    try:
        ahd = b64decode(ah[6:])
    except TypeError:
        logging.warning("Error decoding auth string '%s'" % ah)
        return None
    ahds = ahd.split(':')
    if len(ahds)!=2:
        logging.warning("Error parsing auth string '%s'" % ahd)
        return None
    (username,password) = ahds
    logging.debug("Authenticating user '%s' with password '%s'" % \
                  (username,password))
    
    return queries.getUserByScreenNameAndRSSTOken(username, password)
