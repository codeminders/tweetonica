import os

import datetime
import logging
import random

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext import db

import json

DEFAULT_GROUP_NAME="__ALL__"

# for how long auth token is valid ( 1day+1sec)
AUTH_TOKEN_LIFESPAN = datetime.timedelta(1,1)

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
        auth_token_expires = datetime.datetime.now()+AUTH_TOKEN_LIFESPAN
        return { 'auth_token' : 1234567890,
                 'auth_token_expires' : auth_token_expires.isoformat() }

    def json_logout(self, auth_token=None):
        """"""

    def json_get_friends(self, auth_token=None):
        """"""
        res = {}
        numgroups = random.randint(1, 20)

        group = {
            'name': DEFAULT_GROUP_NAME,
            'rssurl': 'http://www.codeminders.com',
            'users': []
            }
        res[DEFAULT_GROUP_NAME] = group

        for g in range(1, numgroups):
            name = 'Group ' + str(g)

            group = {
                'name': name,
                'rssurl': 'http://www.codeminders.com',
                }

            numusers = random.randint(0, 100)
            users = []
            for u in range(0, numusers):
                user = {
                    'screen_name': 'user_' + str(g) + '_' + str(u),
                    'real_name': 'First ' + str(u) + ' Last ' + str(u),
                    'profile_image_url': 'http://s3.amazonaws.com/twitter_production/profile_images/256569959/logo_big_normal.jpg'
                    }
                users.append(user)
            group['users'] = users
            res[name] = group
        return res

    def json_move_friend(self, auth_token=None, screen_name=None, group_name=None):
        """"""
        

    def json_new_group(self, auth_token=None, group_name=None):
        """"""
        
    def json_rename_group(self, auth_token=None,
                          old_group_name=None,
                          new_group_name=None):
        """"""                          
    
    def json_delete_group(self, auth_token=None, group_name=None):
        """"""        

    # -- implementation method below  ---


def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([('/mockapi', JSONHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
