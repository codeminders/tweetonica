
import re

URLRX = re.compile(r'((mailto\:|(news|(ht|f)tp(s?))\://){1}\S+)')

def mailtoMapper(m):
    email = m.group(2)
    return '<a href="mailto:%s">%s</a>' % (email, email)

def defaultMapper(m):
    url = m.group(1)
    return '<a href="%s">%s</a>' % (url, url)
    
MAPPERS = [
    (re.compile(r'(mailto:([^ ]+))'), mailtoMapper),
    (re.compile(r'(.+)'), defaultMapper)
    ]

def itemHTML(e):
    """ Format tweet as HTML """
    tweet = e.text

    # URLs
    res = ''
    prev = 0
    for m in URLRX.finditer(tweet):
        (fro, to) = m.span()
        url = m.group(1)
        res += tweet[prev:fro]
        prev = to
        for (mo,mf) in MAPPERS:
            mx = mo.match(url)
            if mx:
                res += mf(mx)
                break
    tweet = res + tweet[prev:]
    # @usernames
    tweet = re.sub(r'(\A|\s)@(\w+)', r'\1<a href="http://www.twitter.com/\2">@\2</a>', tweet)
    # #hashtags
    tweet = re.sub(r'(\A|\s)#(\w+)', r'\1<a href="http://search.twitter.com/search?q=%23\2">#\2</a>', tweet)
    #tweet = '<a href="http://twitter.com/%s">%s</a>: %s'  % (
    #                        e.from_friend.screen_name,
    #                        e.from_friend.screen_name,
    #                        tweet)
    return tweet


# ------- debug code below ----------


if __name__ == '__main__':
    import sys
    class Fake:
        pass
    e = Fake()
    e.text = sys.argv[1]
    e.from_friend = Fake()
    e.from_friend.screen_name = 'birdowl'
    
    print itemHTML(e)
