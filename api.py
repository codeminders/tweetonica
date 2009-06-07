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
            self._newUser(me, password)
        else:
            self._updateUser(me, password, users[0])
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

    
    def _updateUser(self, me, password, u):
        logging.debug('updating user %s' % me.screen_name)
        changed = False
        if u.password != password:
            u.password = password
            changed = True
        # TODO: update firends list
        if changed:
            u.put()


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([('/api', JSONHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
