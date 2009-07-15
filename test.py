import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import formatting
import yfrog

class TESTHandler(webapp.RequestHandler):

    def get(self):
        self._testFormat()
        #self._testYfrog()

    def _testYfrog(self):
        self.response.out.write(yfrog.getEmbed('elp28z'))

    def _testFormat(self):
        class Fake:
            pass
        e = Fake()
        e.id = 2606590561
        e.text = 'http://yfrog.us/elp28z Luis Armando Rivera-Hero (3 days after surgery,bloated & in pain,I decided 2 butcher Mariah Carey\'s "Hero".Be kind:P)'
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
    
