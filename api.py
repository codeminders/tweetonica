import os

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util

import twitter
import json
import data

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
        t = twitter.Api(login, password)
        me =  t.verifyCredentials()
        q = data.User.gql('WHERE __key__ == :1', login)
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
        u = data.User()
        u.screen_name = me.screen_name
        u.password = password
        u.id = me.id
        u.timeline_last_updated = None
        # TODO fetch friends and put them into default group
        u.put()
    
    def _updateUser(self, me, password, u):
        changed = False
        if u.password != password:
            u.password = password
            changed = True
        # TODO: update firends list
        if changed:
            u.put()
            



def main():
    app = webapp.WSGIApplication([('/api', JSONHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
