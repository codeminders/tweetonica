"""
Twitter OAuth Support for Google App Engine Apps.
"""

import sys
import logging

from datetime import datetime, timedelta
from hashlib import sha1
from hmac import new as hmac
from random import getrandbits
from time import time
from urllib import urlencode
from uuid import uuid4
from wsgiref.handlers import CGIHandler

from simplejson import loads as decode_json

from google.appengine.api.urlfetch import fetch as urlfetch
from google.appengine.ext import db
from google.appengine.ext.webapp import RequestHandler, WSGIApplication

from misc import quote

CLEANUP_BATCH_SIZE = 100
EXPIRATION_WINDOW = timedelta(seconds=60*60*1) # 1 hour

from constants import OAUTH_APP_SETTINGS
from constants import SITE_BASE_URL
from data import OAuthRequestToken
import queries

STATIC_OAUTH_TIMESTAMP = 12345 # a workaround for clock skew/network lag

def get_service_key(cache={}):
    return "%s&" % encode(OAUTH_APP_SETTINGS['consumer_secret'])

def create_uuid():
    return 'id-%s' % uuid4()

def encode(text):
    return quote(str(text), '')

class FakeToken(object):
    oauth_token = None
    oauth_token_secret = None

class OAuthClient(object):

    __public__ = ('callback', 'cleanup', 'login', 'logout')

    def __init__(self, handler, oauth_callback=None, token=None, **request_params):
        self.service_info = OAUTH_APP_SETTINGS
        self.service_key = None
        self.handler = handler
        self.request_params = request_params
        self.oauth_callback = oauth_callback
        self.token = token

    # public methods

    def get(self, api_method, http_method='GET', expected_status=(200,), raw=False, **extra_params):

        if not (api_method.startswith('http://') or api_method.startswith('https://')):
            api_method = '%s%s%s' % (
                self.service_info['default_api_prefix'], api_method,
                self.service_info['default_api_suffix']
                )

        if self.token is None:
            self.token = queries.getUserByCookie(self.get_cookie())

        fetch = urlfetch(self.get_signed_url(
            api_method, self.token, http_method, **extra_params
            ))

        if fetch.status_code not in expected_status:
            raise ValueError(
                "Error calling... Got return status: %i [%r]" %
                (fetch.status_code, fetch.content)
                )

        if raw:
            return fetch.content
        else:
            return decode_json(fetch.content)

    def post(self, api_method, http_method='POST', expected_status=(200,), raw=False, **extra_params):

        if not (api_method.startswith('http://') or api_method.startswith('https://')):
            api_method = '%s%s%s' % (
                self.service_info['default_api_prefix'], api_method,
                self.service_info['default_api_suffix']
                )

        if self.token is None:
            self.token = queries.getUserByCookie(self.get_cookie())

        fetch = urlfetch(url=api_method, payload=self.get_signed_body(
            api_method, self.token, http_method, **extra_params
            ), method=http_method)

        if fetch.status_code not in expected_status:
            raise ValueError(
                "Error calling... Got return status: %i [%r]" %
                (fetch.status_code, fetch.content)
                )

        if raw:
            return fetch.content
        else:
            return decode_json(fetch.content)

    def login(self):

        proxy_id = self.get_cookie()

        if proxy_id:
            return 'LOGGED_IN'
            #self.expire_cookie()
            #return "FOO%rFF" % proxy_id

        return self.get_request_token()

    def logout(self, return_to='/'):
        queries.logout(self.get_cookie())
        self.expire_cookie()
        self.handler.redirect(self.handler.request.get("return_to", return_to))

    # oauth workflow

    def get_request_token(self):

        token_info = self.get_data_from_signed_url(
            self.service_info['request_token_url'], **self.request_params
            )

        token = OAuthRequestToken(
            **dict(token.split('=') for token in token_info.split('&'))
            )

        token.put()

        if self.oauth_callback:
            oauth_callback = {'oauth_callback': self.oauth_callback}
        else:
            oauth_callback = {}

        self.handler.redirect(self.get_signed_url(
            self.service_info['user_auth_url'], token, **oauth_callback
            ))

    def callback(self, return_to='/'):

        oauth_token = self.handler.request.get("oauth_token")

        if not oauth_token:
            return get_request_token()

        oauth_token = OAuthRequestToken.all().filter(
            'oauth_token =', oauth_token).fetch(1)[0]

        token_info = self.get_data_from_signed_url(
            self.service_info['access_token_url'], oauth_token
            )

        cookie = create_uuid()

        try:
            p = dict(token.split('=') for token in token_info.split('&'))
        except:
            logging.exception("Error parsing twitter response token '%s'" % \
                              (token_info))
            raise

        self.token = FakeToken()
        self.token.oauth_token = p['oauth_token']
        self.token.oauth_token_secret = p['oauth_token_secret']

        cred = self.get('/account/verify_credentials')

        queries.createOrUpdateUser(cred['screen_name'],
                                   cred['id'],
                                   p['oauth_token'],
                                   p['oauth_token_secret'],
                                   cookie)

        oauth_token.delete()
        self.set_cookie(cookie)
        self.handler.redirect(return_to)

    def cleanup(self):
        query = OAuthRequestToken.all().filter(
            'created <', datetime.now() - EXPIRATION_WINDOW
            )
        count = query.count(CLEANUP_BATCH_SIZE)
        db.delete(query.fetch(CLEANUP_BATCH_SIZE))
        return "Cleaned %i entries" % count

    # request marshalling

    def get_data_from_signed_url(self, __url, __token=None, __meth='GET', **extra_params):
        return urlfetch(self.get_signed_url(
            __url, __token, __meth, **extra_params
            )).content

    def get_signed_url(self, __url, __token=None, __meth='GET',**extra_params):
        return '%s?%s'%(__url, self.get_signed_body(__url, __token, __meth, **extra_params))

    def get_signed_body(self, __url, __token=None, __meth='GET', **extra_params):

        service_info = self.service_info

        kwargs = {
            'oauth_consumer_key': service_info['consumer_key'],
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_version': '1.0',
            'oauth_timestamp': int(time()),
            'oauth_nonce': getrandbits(64),
            }

        kwargs.update(extra_params)

        if self.service_key is None:
            self.service_key = get_service_key()

        if __token is not None:
            kwargs['oauth_token'] = __token.oauth_token
            key = self.service_key + encode(__token.oauth_token_secret)
        else:
            key = self.service_key

        message = '&'.join(map(encode, [
            __meth.upper(), __url, '&'.join(
                '%s=%s' % (encode(k), encode(kwargs[k])) for k in sorted(kwargs)
                )
            ]))

        kwargs['oauth_signature'] = hmac(
            key, message, sha1
            ).digest().encode('base64')[:-1]

        return urlencode(kwargs)

    # who stole the cookie from the cookie jar?

    def get_cookie(self):
        return self.handler.request.cookies.get(
            'oauth.twitter', ''
            )

    def set_cookie(self, value, path='/'):
        self.handler.response.headers.add_header(
            'Set-Cookie',
            '%s=%s; path=%s; expires="Fri, 31-Dec-2021 23:59:59 GMT"' %
            ('oauth.twitter', value, path)
            )

    def expire_cookie(self, path='/'):
        self.handler.response.headers.add_header(
            'Set-Cookie',
            '%s=; path=%s; expires="Fri, 31-Dec-1999 23:59:59 GMT"' %
            ('oauth.twitter', path)
            )
        self.handler.response.headers.add_header(
            'Set-Cookie',
            '%s=; path=%s; expires="Fri, 31-Dec-1999 23:59:59 GMT"' %
            ('t.uname', path)
            )

class OAuthHandler(RequestHandler):

    def get(self, action=''):
        try:
            client = OAuthClient(self)
            if action in client.__public__:
                resp = getattr(client, action)()
                if resp and resp == 'LOGGED_IN':
                    self.redirect(SITE_BASE_URL)
                    return
                else:
                    self.response.out.write(resp)
            else:
                #self.response.out.write(client.get_cookie())
                self.response.out.write(client.login())
        except:
            logging.exception("An error occured while talking to Twitter")
            self.redirect('/error.html')


def main():

    application = WSGIApplication([
       ('/oauth/(.*)', OAuthHandler)
       ], debug=True)

    CGIHandler().run(application)

if __name__ == '__main__':
    main()
