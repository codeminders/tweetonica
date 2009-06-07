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

    def json_login(self, login=None, password=None):
        logging.debug('login invoked for user %s' % login)
        t = twitter.Api(login, password)
        me =  t.verifyCredentials()
        q = data.User.gql('WHERE screen_name = :1', login)
        users = q.fetch(1)
        if len(users)!=1:
            u = self._newUser(me, password)
        else:
            u = users[0]
            self._updateUser(me, password, u)
        self._updateFriends(t,u)
        return self._buildAuthToken(me)


    # -- implementation method below  ---

    def _buildAuthToken(self, me):
        # TODO
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
        # TODO: update firends list
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
        q = data.Group.gql('WHERE name = :1', DEFAULT_GROUP_NAME)
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
