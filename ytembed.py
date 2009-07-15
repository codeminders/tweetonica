import logging
from urllib import urlencode

from google.appengine.api.urlfetch import fetch as urlfetch
from google.appengine.api import memcache

import gdata.youtube.service

YOUTUBE_NAMESPACE='YT'
YOUTUBE_CACHE_EXPIRATION=3600*48

def getEmbed(name):
    v = memcache.get(name, namespace=YOUTUBE_NAMESPACE)
    if v!=None:
        return v
    yt_service = gdata.youtube.service.YouTubeService()
    entry = yt_service.GetYouTubeVideoEntry(video_id=name)
    v = entry.GetSwfUrl()
    memcache.set(name, str(v),
                 time=YOUTUBE_CACHE_EXPIRATION,
                 namespace=YOUTUBE_NAMESPACE)
    return v

    

