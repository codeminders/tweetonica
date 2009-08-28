import logging

import data

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

class AdminPanel(webapp.RequestHandler):

    def get(self):

        self.response.out.write("""<html>
                                   <head>
                                       <title>Admin panel</title>
                                   </head>
                                   <body>
                                   <h3>Tweetonica statistics:</h3>""");
        tweetcount = data.StatusUpdate.all().count()
        self.response.out.write('Status update count: %d<br>' % tweetcount)

        replycount = data.Reply.all().count()
        self.response.out.write('Reply count: %d<br>' % replycount)

        groupcount = data.Group.all().count()
        self.response.out.write('Group count: %d<br>' % groupcount)

        usercount = data.User.all().count()
        self.response.out.write('User count: %d<br>' % usercount)

        self.response.out.write("</body></html>")


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