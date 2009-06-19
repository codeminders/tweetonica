""" Misc functions """

import constants

def groupRSS_URL(screen_name, gname):
    #TODO implemnt
    if gname == constants.DEFAULT_GROUP_NAME:
        return "http://example.com/%s/%s" % \
               (constants.FEED_PATH_PREFIX, screen_name)
    else:
        return "http://example.com/%s/%s/%s" % \
               (constants.FEED_PATH_PREFIX, screen_name, gname)
    

