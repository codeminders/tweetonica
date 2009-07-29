
import re
import logging
from urllib import urlencode

from misc import quote
import stock
import yfrog
import ytembed
import constants

URLRX = re.compile(r'((mailto\:|(news|(ht|f)tp(s?))\://){1}\S+)')
STOCK_URLX = re.compile(r'\$([A-Z]+(\.[A-Z]+)?)(([\s,\.!\?\-\:]+)|$)')

def mobypictureMapper(m):
    url = m.group(0)
    th_url = "http://api.mobypicture.com?%s" % \
             (urlencode([('t', url),
                          ('s', 'small'),
                          ('k',constants.MOBYPIC_DEV_KEY),
                          ('format','plain')]))
    return '<a href="%s"><img src="%s"/></a>' % (url, th_url)

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

def youtubeMapper(m):
    media_id = m.group(3)
    embed = None
    try:
        embed = ytembed.getEmbed(media_id)
    except:
        logging.exception("Error getting youtube embed for id '%s'" % media_id)
    if embed:
        return embed
    else:
        url = m.group(0)
        return '<a href="%s">%s</a>' % (url, url)

def mailtoMapper(m):
    email = m.group(2)
    return '<a href="mailto:%s">%s</a>' % (email, email)

def defaultMapper(m):
    url = m.group(1)
    return '<a href="%s">%s</a>' % (url, url)

def yfrogMapper(m):
    url = m.group(0)
    domain = m.group(1)
    media_id = m.group(4)
    if domain=="us" or \
       media_id.endswith('z') or \
       media_id.endswith('f'):
        # Video file, try to get embed
        try:
            embed = yfrog.getEmbed(media_id)
            if embed!=None:
                return embed
        except:
            logging.exception("Error getting emebed for yfrog media '%s'" % media_id)
    return '<a href="%s"><img src="%s.th.jpg"/></a>' % (url, url)

def twitpicMapper(m):
    url = m.group(0)
    media_id = m.group(3)
    return '<a href="%s"><img src="http://twitpic.com/show/thumb/%s"/></a>' % (url, media_id)

MAPPERS = [
    (re.compile(r'(^mailto:([^ ]+))$'), mailtoMapper),
    (re.compile(r'^http://((www\.)?yfrog\.(com|ru|es|fr|us|org|it|pl|eu|com\.pl|com\.tr|co\.uk|co\.il))/([^./\:\?]+)$'), yfrogMapper),
    (re.compile(r'^http://((www\.)?twitpic\.com)/([^/\?]+)$'), twitpicMapper),
    (re.compile(r'^http://((www\.)?youtube\.com)/v/([^/\?]+)$'), youtubeMapper),
    (re.compile(r'^http://((www\.)?youtube\.com)/watch\?v=([^/\?]+)$'), youtubeMapper),
    (re.compile(r'^http://((www\.)?mobypicture\.com)/\?([^/\?]+)$'), mobypictureMapper),
    
    (re.compile(r'^(.+)$'), defaultMapper)
    ]


def itemHTML(e, decorate = True):
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

    # stock symbols
    res = ''
    prev = 0
    for m in STOCK_URLX.finditer(tweet):
        logging.debug("Found stock ")
        (fro, to) = m.span()
        res += tweet[prev:fro]
        prev = to
        res += stockMapper(m)
    tweet = res + tweet[prev:]
    
    # @usernames
    tweet = re.sub(r'(\A|\s)@(\w+)', r'\1<a href="http://www.twitter.com/\2">@\2</a>', tweet)
    # #hashtags
    tweet = re.sub(r'(\A|\s)#(\w+)', r'\1<a href="http://search.twitter.com/search?q=%23\2">#\2</a>', tweet)

    # link to sender
    if decorate:
        tweet = '<a href="http://twitter.com/%s">%s</a>: %s\n<br><hr>%s'  % (
                                e.from_friend.screen_name,
                                e.from_friend.screen_name,
                                tweet,
                                footer(e)
                                )
    return tweet

def _icon_embed(name, link, alt):
    return '<a href="%s"><img src="%s%s%s?ver=1" alt="%s" title="%s"/></a>' % \
           (link,
            constants.SITE_BASE_URL,
            constants.ICONS_PATH,
            name,
            alt,alt)

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

    return \
           _icon_embed('reply.png',reply_link,"Reply") + \
           "&nbsp;&nbsp;&nbsp;&nbsp;" +\
           _icon_embed('retweet.png',rt_link,"Re-tweet") + \
           "&nbsp;&nbsp;&nbsp;&nbsp;" +\
           _icon_embed('direct_msg.png',msg_link,"Direct message")
    



