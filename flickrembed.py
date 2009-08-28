import logging

from google.appengine.api import memcache

import flickr

FLICKR_NAMESPACE = 'FLCKR'
FLICKR_CACHE_EXPIRATION = 3600 * 48

def _getText(pageurl, photoid):
    try:
        url = flickr.Photo(photoid).getURL(size = 'Small', urlType = 'source')
    except:
        try:
            url = flickr.Photo(photoid).getURL(size = 'Large', urlType = 'source')
        except:
            pass
    if url: return '<a href="%s"><img src="%s"></a>' % (pageurl, url)
    else: return None


def getEmbed(url, photoid):
    cached = memcache.get(photoid, namespace = FLICKR_NAMESPACE)
    if cached: return cached
    try: embed = _getText(url, photoid)
    except: return None
    if not embed: return None
    memcache.set(photoid, str(embed),
                 time = FLICKR_CACHE_EXPIRATION, namespace = FLICKR_NAMESPACE)
    return embed
