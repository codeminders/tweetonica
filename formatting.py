
import re

URLRX = re.compile(r'((mailto\:|(news|(ht|f)tp(s?))\://){1}\S+)')

def mailtoMapper(m):
    email = m.group(2)
    return '<a href="mailto:%s">%s</a>' % (email, email)

def defaultMapper(m):
    url = m.group(1)
    return '<a href="%s">%s</a>' % (url, url)

def yfrogMapper(m):
    url = m.group(0)
    #domain = m.group(1)
    #media_id = m.group(4)
    return '<a href="%s"><img src="%s.th.jpg"/></a>' % (url, url)

def twitpicMapper(m):
    url = m.group(0)
    media_id = m.group(3)
    return '<a href="%s"><img src="http://twitpic.com/show/thumb/%s"/></a>' % (url, media_id)

MAPPERS = [
    (re.compile(r'(^mailto:([^ ]+))$'), mailtoMapper),
    (re.compile(r'^http://((www\.)?yfrog\.(com|ru|es|fr|us|org|it|pl|eu|com\.pl|com\.tr|co\.uk|co\.il))/([^./\:\?]+)$'), yfrogMapper),
    (re.compile(r'^http://((www\.)?twitpic\.com)/([^/\?]+)$'), twitpicMapper),
    
    (re.compile(r'^(.+)$'), defaultMapper)
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

    # link to sender
    tweet = '<a href="http://twitter.com/%s">%s</a>: %s'  % (
                            e.from_friend.screen_name,
                            e.from_friend.screen_name,
                            tweet)
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
