
import datetime
import logging
from urllib import unquote

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

import queries
import data
import constants
import misc

class OPMLHandler(webapp.RequestHandler):

    def get(self, u):

        username = unquote(u)
        rss_token = self.request.get(constants.TOKEN_PARAM_NAME,
                                    default_value=None)

        if not rss_token:
            u = misc.HTTP_authenticate()
            if not u:
                self.response.headers['WWW-Authenticate'] = \
                        'Basic realm=%s' % constants.REALM
                self.response.set_status(401)
                return
        else:
            u = queries.getUserByRSSToken(rss_token)
            if not u:
                self.response.set_status(403)
                return
        
        self._generateOPML(u)
    
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

    def _generateOPML(self, u):
        self.response.headers['Content-Type'] = 'application/opml+xml'
        self.response.out.write("OPML HERE\n")
        pass
        

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([('%s/(.+)'%constants.OPML_PATH_PREFIX, \
                                   OPMLHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
