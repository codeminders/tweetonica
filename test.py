import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import formatting

class TESTHandler(webapp.RequestHandler):

    def get(self):
        class Fake:
            pass
        e = Fake()
        e.id = 2606590561
        e.text = 'Last one: $AAPL, $MSFT1 and $AVSR. All for $nothing or $1'
        e.from_friend = Fake()
        e.from_friend.screen_name = 'bird_owl'

        self.response.out.write(formatting.itemHTML(e))




def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([("/test", \
                                   TESTHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
    
