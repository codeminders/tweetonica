import logging
from urllib import urlencode

from google.appengine.api.urlfetch import fetch as urlfetch
from google.appengine.api import memcache

import gdata.youtube
import gdata.youtube.service

YOUTUBE_NAMESPACE='YT'
YOUTUBE_CACHE_EXPIRATION=3600*48

def getEmbed(name):
    v = memcache.get(name, namespace=YOUTUBE_NAMESPACE)
    if v!=None:
        return v
    yt_service = gdata.youtube.service.YouTubeService()
    entry = yt_service.GetYouTubeVideoEntry(video_id=name)
    logging.debug(dir(entry))
    u = entry.GetSwfUrl()
    if not entry.noembed and u:
        # embed player
        v=('<object width="425" height="350">'
           '<param name="movie" value="' + u + '"></param>'
           '<embed src="' + u + 
           '" type="application/x-shockwave-flash" '
           'width="425" height="350"></embed></object>')
    elif entry.media.thumbnail and len(entry.media.thumbnail)>1:
        # embed thumb
        th = entry.media.thumbnail[0]
        v='<a href="%s"><img src="%s" width="%s" height="%s"></a>' % \
           (entry.media.player.url,
            th.url,
            th.width,
            th.height)
    else:
        # all fails!
        v = None

    if v!=None:
        memcache.set(name, str(v),
                     time=YOUTUBE_CACHE_EXPIRATION,
                     namespace=YOUTUBE_NAMESPACE)
    return v

    

