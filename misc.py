""" Misc functions """

import os, logging
from base64 import b64decode

import data
import constants
import queries

def groupRSS_URL(screen_name, rss_token, group_name, use_HTTP_auth):
    if use_HTTP_auth:
        return "http://%s%s/%s/%s" % \
               (constants.DOMAIN,
                constants.FEED_PATH_PREFIX,
                screen_name, group_name)
    else:
        return "http://%s%s/%s/%s?%s=%s" % \
               (constants.DOMAIN,
                constants.FEED_PATH_PREFIX,
                screen_name, group_name,
                constants.TOKEN_PARAM_NAME, rss_token)

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
    
    u = queries.getUserByScreenNameAndRSSTOken(username, password)
    return u
