
import re
from misc import quote
import stock
import logging

URLRX = re.compile(r'((mailto\:|(news|(ht|f)tp(s?))\://){1}\S+)')
STOCK_URLX = re.compile(r'\$([A-Z]+(\.[A-Z]+)?)((\s+)|$)')

def stockMapper(m):
    symbol = str(m.group(1))
    ws = str(m.group(3))
    try:
        valid = stock.isStockSymbol(symbol)
    except:
        logging.exception("Error looking up stock symbol '%s'" % symbol)
        valid = False
        
    if valid:
        return '<a href="http://stocktwits.com/t/%s" target="_blank">$%s</a>%s' % \
               (quote(symbol), symbol, ws);
    else:
        # unknown stock symbol. Leave as is.
        return m.group(0)

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

    # stock symbols
    res = ''
    prev = 0
    logging.debug("Examining '%s'" % tweet)
    for m in STOCK_URLX.finditer(tweet):
        (fro, to) = m.span()
        res += tweet[prev:fro]
        prev = to
        res += stockMapper(m)
    tweet = res + tweet[prev:]

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
    tweet = '<a href="http://twitter.com/%s">%s</a>: %s\n<br><hr><br>%s'  % (
                            e.from_friend.screen_name,
                            e.from_friend.screen_name,
                            tweet,
                            footer(e)
                            )
    return tweet

def footer(e):
    reply_link = "http://twitter.com/home?status=@%s%%20&in_reply_to_status_id=%d&in_reply_to=%s" % \
                 (e.from_friend.screen_name, e.id, e.from_friend.screen_name)
    
    rt_link = "http://twitter.com/home?status=RT%%20@%s:%%20%s&in_reply_to_status_id=%d&in_reply_to=%s" %  \
              (e.from_friend.screen_name,
               quote(e.text),
               e.id,
               e.from_friend.screen_name)
    
    msg_link = "http://twitter.com/direct_messages/create/%s" % \
               (e.from_friend.screen_name)

    return ('| <a href="%s">REPLY</a> |' % reply_link)  + \
           ('<a href="%s">RT</a> |' % rt_link)  + \
           ('<a href="%s">DM</a> |' % msg_link)



# ------- debug code below ----------


if __name__ == '__main__':
    import sys
    class Fake:
        pass
    e = Fake()
    e.id = 2606590561
    e.text = sys.argv[1]
    e.from_friend = Fake()
    e.from_friend.screen_name = 'bird_owl'
    
    print itemHTML(e)
