import os

import datetime
import logging
from uuid import uuid1
from base64 import b64decode

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

import twitter
import data

REALM='phanalgesfeed'

class ATOMHandler(webapp.RequestHandler):

    def get(self):
        u = self._HTTP_authenticate()
        if not u:
            self.response.headers['WWW-Authenticate'] = 'Basic realm=%s' % REALM
            self.response.set_status(401)
    
    def post(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')

    def put(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')

    def head(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')

    def options(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')

    def delete(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')

    def trace(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')


    # -- implementation method below  ---

    def _HTTP_authenticate(self):
        if not os.environ.has_key('HTTP_AUTHORIZATION'):
            return None
        ah = os.environ['HTTP_AUTHORIZATION']
        logging.debug("Auth header: %s" % ah)
        if not ah or len(ah)<6:
            logging.warning("Invalid auth string '%s'" % ah)
            return None
        try:
            ahd = b64decode(ah[6:])
        except TypeError:
            logging.warning("Error decoding auth string '%s'" % ah)
            return None
        ahds = ahd.split(':')
        if len(ahds)!=2:
            logging.warning("Error parsing auth string '%s'" % ahd)
            return None
        (username,password) = ahds
        logging.debug("Authenticatin user '%s' with password '%s'" % \
                      (username,password))

        q = data.User.gql('WHERE screen_name = :1 and password=:2', \
                          username,password)
        users = q.fetch(1)
        if len(users)==1:
            logging.debug("User '%s' authenticated" % username)
            return users[0]
        else:
            return None
        
        return None

    def _updateTimeLine(self,u,t):
        # TODO: since
        # TODO: paging back
        try:
            timeline = t.GetFriendsTimeline()
        except Exception:
            logging.exception("Error fetching friends timeline for %s" % u.screen_name)
            raise json.JSONRPCError("Error fetching friends timeline",
                                    code=ERR_TWITTER_COMM_ERROR)
        for t in timeline:
            logging.debug("Got timeline entry %s" % t)
            pass



def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([('/feed', ATOMHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
