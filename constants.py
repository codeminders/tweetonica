""" Various constants """


import datetime

SPECIAL_GROUP_PREFIX = '__'
DEFAULT_GROUP_NAME = SPECIAL_GROUP_PREFIX + "ALL__"

REPLIES_GROUP_NAME = SPECIAL_GROUP_PREFIX + "REPLIES__"

""" URL path of WSGI app for feed.py. Witout trailing slash! """
FEED_PATH_PREFIX = "/feed"

""" URL path of WSGI app for opml.py. Witout trailing slash! """
OPML_PATH_PREFIX = "/opml"

""" Name of RSS feed URL parameter which holds secret token """
TOKEN_PARAM_NAME = "secret"

""" App domain. Used in generated URLs """
DOMAIN = "www.tweetonica.com"

""" HTTP Basic auth realm """
REALM='tweetonica.com'

OAUTH_APP_SETTINGS = {
    'consumer_key': 'Jfhz20pXgCsg282eIdbg',
    'consumer_secret': 'elCnqrCy2IfGl1KaRde9cOLxjPPpvkFDo2WRNPOzKA',

#    'consumer_key': 'K9qqChOFmpGp7e4LlA1g',
#    'consumer_secret': 'DxcDnyLEeOOSXteiZf0gntHXQMkfeUoCgIiKro',

    'request_token_url': 'http://twitter.com/oauth/request_token',
    'access_token_url': 'http://twitter.com/oauth/access_token',
    'user_auth_url': 'http://twitter.com/oauth/authorize',

    'default_api_prefix': 'http://twitter.com',
    'default_api_suffix': '.json'
}


""" Entries older that this time will be not fetched. If
such entries exist, they would be cleaned from DB
"""
BACK_ENTRIES = datetime.timedelta(days=7)

MOBYPIC_DEV_KEY='7mV3iBuSDu33ERyi'

# web-related
SITE_BASE_URL = 'http://tweetonica.com'
#SITE_BASE_URL = 'http://localhost:8080'
#SITE_BASE_URL = 'http://3.latest.tweetonica.appspot.com'
ICONS_PATH = "/images/"

LAST_MESSAGE_CACHE_TIME = 3600 * 600
LAST_MESSAGE_NAMESPACE = 'LASTMSG'
LAST_REPLY_CACHE_TIME = 3600 * 600
LAST_REPLY_NAMESPACE = 'LASTRMSG'
