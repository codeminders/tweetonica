import logging
from urllib import urlencode
from xml.dom.minidom import parseString

from google.appengine.api.urlfetch import fetch as urlfetch
from google.appengine.api import memcache

YFROG_NAMESPACE='YFR'
API_URL='http://yfrog.com/api/xmlInfo?%s'
YFROG_CACHE_EXPIRATION=3600*48

class YfrogException(Exception):
    def __init__(self, message, id, httpStatus=500):
        self.message = message
        self.id = id
        self.httpStatus = httpStatus

    def __str__(self):
        return "YfrogException: %s for '%s'. Code %d" % \
               (self.message, self.id, self.httpStatus)

def _getText(n):
    rc = ""
    for node in n.childNodes:
        if node.nodeType == node.TEXT_NODE:
            rc = rc + node.data
    return rc

def getEmbed(name):
    v = memcache.get(name, namespace=YFROG_NAMESPACE)
    if v!=None:
        return v
    fetch = urlfetch(API_URL % urlencode([('path',name)]))
    if fetch.status_code != 200:
        raise YfrogException("Error getting media info",
                             name,
                             fetch.status_code)

    dom = parseString(fetch.content)
    try:
        v = _getText(dom.getElementsByTagName("video_embed")[0])
        memcache.set(name, str(v),
                     time=YFROG_CACHE_EXPIRATION,
                     namespace=YFROG_NAMESPACE)
        return v
    finally:
        dom.unlink()

    

