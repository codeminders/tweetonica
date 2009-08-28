
import re
import logging
from urllib import urlencode
import httplib

from misc import quote
import stock
import yfrog
import ytembed
import flickrembed
import constants

from google.appengine.api import memcache

URLS_NAMESPACE = 'URLS'
URLS_CACHE_EXPIRATION = 3600 * 48

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

def flickrMapper(m):
    url = m.group(0)
    photo_id = m.group(2)
    logging.debug('flickrMapper starting for url %s photoid %s' % (url, photo_id))
    try:
        embed = flickrembed.getEmbed(url, photo_id)
    except:
        logging.exception("Error getting flickr embed for id %s" % photo_id)
    if embed:

        return embed
    else: return '<a href="%s">%s</a>' % (url, url)

def urlResolver(match):
    url = match.group(0)
    site = match.group(2)
    short = match.group(3)
    cached = memcache.get(url, namespace = URLS_NAMESPACE)
    if cached: return cached
    try:
        conn = httplib.HTTPConnection(site)
        conn.request('HEAD', short)
        resp = conn.getresponse()
    except e:
        logging.error('Could not get responce from %s' % site)
    if resp.status >= 300 and resp.status < 400:
        longurl = resp.getheader('Location')
        logging.debug('Resolved %s as %s' % (url, longurl))
        memcache.set(url, str(longurl), time = URLS_CACHE_EXPIRATION,
                     namespace = URLS_NAMESPACE)
        return longurl
    else:
        return None

SHORTLINK_WEBSITES = ['bit.ly',
                     'tinyurl.com',
                     'su.pr',
                     'ow.ly',
                     'is.gd',
                     'tr.im']

# this is good until there is a shortlink website which does not return
# target url in location header
URLSOLVERS = [ (re.compile('http://(www.)?(%s)(/.*)' % site), urlResolver) \
               for site in SHORTLINK_WEBSITES ]

MAPPERS = [
    (re.compile(r'(^mailto:([^ ]+))$'), mailtoMapper),
    (re.compile(r'^http://((www\.)?yfrog\.(com|ru|es|fr|us|org|it|pl|eu|com\.pl|com\.tr|co\.uk|co\.il))/([^./\:\?]+)$'), yfrogMapper),
    (re.compile(r'^http://((www\.)?twitpic\.com)/([^/\?]+)$'), twitpicMapper),
    (re.compile(r'^http://((www\.)?youtube\.com)/v/([^/\?]+)$'), youtubeMapper),
    (re.compile(r'^http://((www\.)?youtube\.com)/watch\?v=([^/\?]+)$'), youtubeMapper),
    (re.compile(r'^http://((www\.)?mobypicture\.com)/\?([^/\?]+)$'), mobypictureMapper),
    (re.compile(r'^http://(www\.)?flickr.com/photos/[\w\@]+/(\d+)'), flickrMapper),

    (re.compile(r'^(.+)$'), defaultMapper)
    ]


def itemHTML(e, decorate = True):
    """ Format tweet as HTML """
    tweet = e.text

    # URLs
    res = ''
    prev = 0

    def urlSolver(match):
        url = match.group(0)
        for (regex, handler) in URLSOLVERS:
            match = regex.match(url)
            if match:
                try:
                    res = handler(match)
                    return res if res else url
                except:
                    return url
        return url

    def urlMapper(match):
        url = match.group(0)
        for (regex, handler) in MAPPERS:
            match = regex.match(url)
            if match:
                try: res = handler(match)
                except: res = None
                if res: return res
                else: return url
        return url

    tweet = URLRX.subn(urlSolver, tweet)[0]
    tweet = URLRX.subn(urlMapper, tweet)[0]

    # This is old function. I don't see any reason not to use re.subn
    #for m in URLRX.finditer(tweet):
        #(fro, to) = m.span()
        #url = m.group(1)
        #res += tweet[prev:fro]
        #prev = to
        #for (regex, handler) in URLSOLVERS:
            #match = regex.match(url)
            #if match:
                #res += handler(match)
                #break
        #for (mo,mf) in MAPPERS:
            #mx = mo.match(url)
            #if mx:
                #res += mf(mx)
                #break
    #tweet = res + tweet[prev:]

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
    if hasattr(e, 'from_friend'):
        name = e.from_friend.screen_name
    elif hasattr(e, 'to'):
        name = e.author

    if decorate:
        tweet = '<a href="http://twitter.com/%s">%s</a>: %s\n<br><hr>%s'  % (
                                name,
                                name,
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
    if hasattr(e, 'from_friend'):
        name = e.from_friend.screen_name
    elif hasattr(e, 'to'):
        name = e.author
    reply_link = "http://twitter.com/home?status=@%s%%20&in_reply_to_status_id=%d&in_reply_to=%s" % \
                 (name, e.id, name)

    rt_link = "http://twitter.com/home?status=RT%%20@%s:%%20%s&in_reply_to_status_id=%d&in_reply_to=%s" %  \
              (name,
               quote(e.text),
               e.id,
               name)

    msg_link = "http://twitter.com/direct_messages/create/%s" % \
               (name)

    return \
           _icon_embed('reply.png',reply_link,"Reply") + \
           "&nbsp;&nbsp;&nbsp;&nbsp;" +\
           _icon_embed('retweet.png',rt_link,"Re-tweet") + \
           "&nbsp;&nbsp;&nbsp;&nbsp;" +\
           _icon_embed('direct_msg.png',msg_link,"Direct message")




