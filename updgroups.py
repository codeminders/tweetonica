import logging

import data

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

class AdminPanel(webapp.RequestHandler):

    def get(self):

        for g in data.Group.all():
            self.response.out.write('Updating group %s<br>' % g.name)
            g.viewed = datetime.datetime.fromtimestamp(0)
            g.put()


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

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([('/report', AdminPanel)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()