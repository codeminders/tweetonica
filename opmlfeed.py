
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

import xml.sax.saxutils

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
        self.response.headers['Content-Disposition'] = 'inline; filename=%s.opml' % u.screen_name
        res = queries.loadGroups(u)

        tstamp = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

        self.response.out.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n")
        self.response.out.write("<opml version=\"2.0\">\n")
        self.response.out.write("    <head>\n")
        self.response.out.write("        <title>Tweetonica feeds of %s</title>\n" % xml.sax.saxutils.escape(u.screen_name))
        self.response.out.write("        <dateCreated>%s</dateCreated>\n" % tstamp)
        self.response.out.write("        <dateModified>%s</dateModified>\n" % tstamp)
        self.response.out.write("        <ownerName>%s</ownerName>\n" % xml.sax.saxutils.escape(u.screen_name))
        self.response.out.write("        <ownerId>http://twitter.com/%s</ownerId>\n" % xml.sax.saxutils.escape(u.screen_name))
        self.response.out.write("        <docs>http://www.opml.org/spec2/</docs>\n")
        self.response.out.write("    </head>\n")
        self.response.out.write("    <body>\n")
        
        for x in res.keys():
            rssurl = misc.getGroupRSS_URL(u.screen_name,
                                          u.rss_token,
                                          x, 
                                          u.use_HTTP_auth)
            if x == constants.DEFAULT_GROUP_NAME:
                name = "Uncategorized"
            else:
                name = xml.sax.saxutils.escape(x)
            self.response.out.write("        <outline text=\"%s\" description=\"Tweets in group %s\" xmlUrl=\"%s\" type=\"rss\" version=\"RSS\"/>\n" % (name, name, rssurl))
        
        self.response.out.write("    </body>\n")
        self.response.out.write("</opml>\n")
        

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([('%s/(.+)'%constants.OPML_PATH_PREFIX, \
                                   OPMLHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
