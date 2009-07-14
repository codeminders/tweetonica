""" Various constants """

DEFAULT_GROUP_NAME = "__ALL__"

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
    
    'request_token_url': 'http://twitter.com/oauth/request_token',
    'access_token_url': 'http://twitter.com/oauth/access_token',
    'user_auth_url': 'http://twitter.com/oauth/authorize',

    'default_api_prefix': 'http://twitter.com',
    'default_api_suffix': '.json'
}
