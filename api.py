import os

import datetime
import logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext import db

import twitter
import json
import data

DEFAULT_GROUP_NAME="__ALL__"

class JSONHandler(webapp.RequestHandler, json.JSONRPC):

    def get(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'POST')
        
    def post(self):
        response, code = self.handleRequest(self.request.body, self.HTTP_POST)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.set_status(code)
        self.response.out.write(response)

    # -- API methods delegates below --

    def json_login(self, screen_name=None, password=None):
        logging.debug('Method \'login\' invoked for user %s' % screen_name)
        t = twitter.Api(screen_name, password)
        me =  t.verifyCredentials()
        u = self._getUserByScreenName(screen_name)
        if u:
            self._updateUser(me, password, u)
        else:
            u = self._newUser(me, password)
        self._updateFriends(t,u)
        return self._buildAuthToken(me)

    def json_get_users(self, auth_token=None, screen_name=None):
        logging.debug('Method \'get_users\' invoked for user %s' % screen_name)
        u = self._getUserByScreenName(screen_name)
        if not u:
            raise Exception("Unknown user '%s'" % screen_name)
        self._verifyAuthToken(auth_token, screen_name, u)

        q = data.Group.gql('WHERE user = :1', u.key())
        res = []
        for g in q:
            res.append({
                'name': g.name,
                'rssurl': self._groupRSS_URL(g),
                "users": [f.screen_name for f in self._groupMembers(g)]
                });
        return res
    
    # -- implementation method below  ---

    def _groupMembers(self,g):
        q = data.Friend.gql('WHERE  group = :1', g.key())
        return q

    

    def _groupRSS_URL(self,g):
        #TODO imeplemnt
        return "http://example.com/%s/%s" % (g.user.screen_name, g.name)
    
    def _getUserByScreenName(self, screen_name):
        q = data.User.gql('WHERE screen_name = :1', screen_name)
        users = q.fetch(1)
        if len(users)==1:
            return users[0]
        else:
            return None

    def _verifyAuthToken(self, token, screen_name, u):
        #TODO imeplemnt
        pass

    def _buildAuthToken(self, me):
        #TODO imeplemnt
        return "BLAH"
    
    def _newUser(self, me, password):
        """ Creates new user record with empty default group """
        logging.debug('creating user %s' % me.screen_name)
        u = data.User(screen_name = me.screen_name,
                      password = password,
                      id = me.id,
                      timeline_last_updated = None)
        # TODO fetch friends and put them into default group
        u.put()
        g = data.Group(name=DEFAULT_GROUP_NAME,
                       memberships_last_updated=datetime.datetime.now(),
                       user=u,
                       parent=u)
        g.put()
        return u

    
    def _updateUser(self, me, password, u):
        logging.debug('updating user %s' % me.screen_name)
        changed = False
        if u.password != password:
            u.password = password
            changed = True
        if changed:
            u.put()

    def _updateFriends(self, t, u):
        friends = t.GetFriends()
        for f in friends:
            if self._isKnownFriend(u,f):
                logging.debug("Friend %s is already known" % f.screen_name)
            else:
                self._addNewFriend(u,f,self._getDefaultGroup(u))


    def _getDefaultGroup(self, u):
        q = data.Group.gql('WHERE name = :1 and user=:2', DEFAULT_GROUP_NAME,
                           u.key())
        groups = q.fetch(1)
        return groups[0]
        
    def _isKnownFriend(self,u,f):
        q = data.Friend.gql('WHERE screen_name = :1 and user=:2',
                            f.screen_name, u.key())
        
        friends = q.fetch(1)
        return len(friends)==1
    

    def _addNewFriend(self,u,f,g):
        logging.debug("Adding friend %s to %s" % (f.screen_name, u.screen_name))
        fo = data.Friend(id = f.id,
                         screen_name = f.screen_name,
                         real_name = f.name,
                         profile_image_url = f.profile_image_url,
                         user = u,
                         group = g,
                        parent=u)
        fo.put()

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([('/api', JSONHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
