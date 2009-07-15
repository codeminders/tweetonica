
import logging
from urllib import urlencode

from google.appengine.api.urlfetch import fetch as urlfetch
from google.appengine.api import memcache

STOCK_NAMESPACE='STK'
API_URL='http://download.finance.yahoo.com/d/quotes.csv?%s'
OK_ANSWER='"N/A"'

class StockCheckException(Exception):
    def __init__(self, message, symbol, httpStatus=500):
        self.message = message
        self.symbol = symbol
        self.httpStatus = httpStatus

    def __str__(self):
        return "StockCheckException: %s for '%s'. Code %d" % \
               (self.message, self.symbol, self.httpStatus)

def isStockSymbol(name):
    """ Check if stock symbol name is valid.
    
    Args:
    name - stock symbol name
    """
    v = memcache.get(name, namespace=STOCK_NAMESPACE)
    if v!=None:
        return bool(v)
    
    fetch = urlfetch(API_URL % urlencode([('s',name), ('f','e1')]))
    if fetch.status_code != 200:
        raise StockCheckException("Error checking stock status",
                                  name,
                                  fetch.status_code)
    v = (fetch.content == OK_ANSWER)
    memcache.set(name, str(v), namespace=STOCK_NAMESPACE)
    return v

