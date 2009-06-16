import os

import datetime
import logging
from uuid import uuid1
from base64 import b64decode
from cgi import parse_qs

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

import queries
import twitter
import data

REALM='phanalgesfeed'

""" How many timeline entries to fetch. No more than 200! """
FETCH_COUNT=100

class ATOMHandler(webapp.RequestHandler):

    def get(self):
        params = parse_qs(self.request.query_string)

        if params.has_key('group'):
            group = params['group'][0]
        else:
            group = constants.DEFAULT_GROUP_NAME
        
        u = self._HTTP_authenticate()
        if not u:
            self.response.headers['WWW-Authenticate'] = 'Basic realm=%s' % REALM
            self.response.set_status(401)
            return

        t = twitter.Api(u.screen_name, u.password)
        # TODO: update frequency check
        if True:
            groups = queries.loadGroups(u)
            self._updateTimeLine(u,t,groups)

        g = getGroupByName(group, u)
        if not g:
            logging.warning("Request for non-existing group '%s' for user '%s'" % \
                            (g.name, u.screen_name))
            self.response.set_status(404)
            return
            
        self._generateFeed(u,g)
    
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
        
    def _updateTimeLine(self,u,t,groups):
        logging.debug("Updating timeline for user %s" % u.screen_name)

        # build user->group index
        gi = {}
        for g in groups:
            for gu in g['users']:
                gi[gu['screen_name']]=g
        # user index
        ui = {}
        page = 1
        done = False
        while not done:
            try:
                timeline = t.GetFriendsTimeline(since_id = u.timeline_max_id,\
                                                page=page, count=FETCH_COUNT)
                page = page + 1
            except Exception:
                logging.exception("Error fetching friends timeline for %s" % \
                                  u.screen_name)
                raise json.JSONRPCError("Error fetching friends timeline",
                                        code=ERR_TWITTER_COMM_ERROR)
            if timeline==None or len(timeline)==0:
                break
            for e in timeline:
                logging.debug("Got timeline entry %s" % e)
                if e.id==u.timeline_max_id:
                    done = True
                    break
                if e.id>u.timeline_max_id:
                    u.timeline_max_id = e.id
                    eg = gi.get(e.user.screen_name, None)
                    if eg == None:
                        logging.error("Timeline entry from non-friend %s!" % \
                                      e.user.screen_name)
                        continue
                    eu = ui.get(e.user.screen_name, None)
                    if eu == None:
                        eu = queries.getUserByScreenName(e.user.screen_name)
                        if eu == None:
                            logging.error("Timeline entry from unknown friend %s!" % \
                                          e.user.screen_name)
                            continue
                    self._addTimeLineEntry(e,u,eg,eu)
        u.timeline_last_updated=datetime.datetime.now()
        u.update()

    def _addTimeLineEntry(self,e,u,group,friend):
        s = data.StatusUpdate(id = e.id,
                              text = e.text,
                              created_at = e.created_at,
                              truncated = False, #TODO
                              in_reply_to_status_id = -1, #TODO
                              in_reply_to_user_id = -1, #TODO
                              in_reply_to_screen_name = None, #TODO
                              group = group.key(),
                              from_friend = friend.key())
        s.put()

    def _generateFeed(self,u,g):
        # TODO:
        pass


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([('/feed', ATOMHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
