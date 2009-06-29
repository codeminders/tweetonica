""" Misc functions """

import os, logging
from base64 import b64decode

import data
import constants

def groupRSS_URL(screen_name, rss_token, group_name):
    return "http://example.com/%s/%s/%s?%s=%s" % \
           (constants.FEED_PATH_PREFIX,
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

    q = data.User.gql('WHERE screen_name = :1 and rss_token=:2', \
                      username,password)
    users = q.fetch(1)
    if len(users)==1:
        logging.debug("User '%s' authenticated" % username)
        return users[0]
    else:
        logging.debug("No user of bad pass for %s" % username)
        return None

    return None
