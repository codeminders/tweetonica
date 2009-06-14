import os

import datetime
import logging
from urllib2 import HTTPError
from uuid import uuid1

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

import twitter
import data


class ATOMHandler(webapp.RequestHandler):

    def get(self):
        pass
    
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
