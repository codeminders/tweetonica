import logging
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import data
import constants

class CleanupHandler(webapp.RequestHandler):

    def get(self):
        self._removeOldStatusRecords()

    def _removeOldStatusRecords(self):
        logging.info("Removing old status updates")
        since = datetime.datetime.now()-constants.BACK_ENTRIES
        rs = data.StatusUpdate.gql("WHERE created_at < :1",\
                                   since.strftime('DATETIME(%Y-%m-%d %H:%M:%S)')
                                   )
        n = 0
        for r in rs:
            logging.debug("Removing entry %d" %r.id)
            r.delete()
            n = n + 1
        logging.info("%d entries deleted" % n)
        self.response.out.write("%d entries deleted" % n)

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([("/cleanup", \
                                   CleanupHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
    
