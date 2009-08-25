
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
import xe
from feed.opml import *

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

        tstamp = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")
        logging.debug(tstamp)
        xmldoc, opml = new_xmldoc_opml()
        opml.head.title = "Tweetonica feeds of %s" % u.screen_name
        opml.head.date_created = tstamp
        opml.head.owner_name = u.screen_name
        opml.head.owner_id = "http://twitter.com/%s" % u.screen_name

        opml.head._element_names.remove('owner_email')
        del(opml.head.__dict__['owner_email'])

        lastupdated = datetime.datetime(2009, 1, 1)

        for x in res.keys():
            rssurl = misc.getGroupRSS_URL(u.screen_name,
                                          u.rss_token,
                                          x,
                                          u.use_HTTP_auth)
            outline = Outline("", created=0.0)
            outline.attrs["description"] = misc.getGroupRSS_title(u.screen_name, x)
            outline.attrs["xmlUrl"] = rssurl
            outline.attrs["type"] = "rss"
            outline.attrs["version"] = "RSS"
            opml.body.append(outline)

            if res[x]['memberships_last_updated'] > lastupdated:
                lastupdated = res[x]['memberships_last_updated']
        opml.head.date_modified = lastupdated.strftime("%a, %d %b %Y %H:%M:%S GMT")
        self.response.out.write(str(xmldoc))


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([('%s/(.+)'%constants.OPML_PATH_PREFIX, \
                                   OPMLHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
