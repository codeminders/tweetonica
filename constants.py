""" Various constants """

DEFAULT_GROUP_NAME = "__ALL__"

""" URL path of WSGI app for feed.py. Witout trailing slash! """
FEED_PATH_PREFIX = "/feed"

""" URL path of WSGI app for opml.py. Witout trailing slash! """
OPML_PATH_PREFIX = "/opml"


OAUTH_APP_SETTINGS =
{
    'twitter': {
        'consumer_key': '',
        'consumer_secret': '',

        'request_token_url': 'https://twitter.com/oauth/request_token',
        'access_token_url': 'https://twitter.com/oauth/access_token',
        'user_auth_url': 'http://twitter.com/oauth/authorize',

        'default_api_prefix': 'http://twitter.com',
        'default_api_suffix': '.json',
        }
}
