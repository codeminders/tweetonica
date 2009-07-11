
import re

def itemHTML(e):
    """ Format tweet as HTML """
    tweet = e.text
    # URLs
    tweet = re.sub(r'(http(s)?://[^ ]+)', r'<a href="\1">\1</a>', tweet)
    # @usernames
    tweet = re.sub(r'(\A|\s)@(\w+)', r'\1<a href="http://www.twitter.com/\2">@\2</a>', tweet)
    # #hashtags
    tweet = re.sub(r'(\A|\s)#(\w+)', r'\1<a href="http://search.twitter.com/search?q=%23\2">#\2</a>', tweet)
    tweet = '<a href="http://twitter.com/%s">%s</a>: %s'  % (
                            e.from_friend.screen_name,
                            e.from_friend.screen_name,
                            tweet)
    return tweet
