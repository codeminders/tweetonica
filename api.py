import os

import datetime
import logging
from urllib2 import HTTPError
from uuid import uuid1

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

import twitter
import json
import data
import queries
import constants
import misc
from oauth import OAuthClient


# for how long auth token is valid ( 1day+1sec)
AUTH_TOKEN_LIFESPAN = datetime.timedelta(1,1)

# JSON-RPC Error Codes (101=999)
ERR_TWITTER_AUTH_FAILED = 101
ERR_BAD_AUTH_TOKEN = 102
ERR_TWITTER_COMM_ERROR = 103
ERR_GROUP_ALREADY_EXISTS = 104
ERR_NO_SUCH_GROUP = 105
ERR_NO_SUCH_FRIEND = 106
ERR_DEFAULT_GROUP_MODIFICATION_NOT_PERMITTED = 107

class JSONHandler(webapp.RequestHandler, json.JSONRPC):

    def post(self):
        response, code = self.handleRequest(self.request.body, self.HTTP_POST)
        self.response.headers['Content-Type'] = 'application/json'
        self.response.set_status(code)
        self.response.out.write(response)

    def get(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'POST')

    def put(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'POST')

    def head(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'POST')

    def options(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'POST')

    def delete(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'POST')

    def trace(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'POST')
        

    # -- response methods delegates below --

    def json_logout(self, auth_token=None):
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'logout\' invoked for user %s' % u.screen_name)
        u.cookie = None
        u.put()

    def json_get_friends(self, auth_token=None):
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'get_fiends\' invoked for user %s' % u.screen_name)
        res = queries.loadGroups(u)
        for x in res.keys():
            res[x]['rssurl']=misc.groupRSS_URL(u.screen_name, x)
        return res

    def json_move_friend(self, auth_token=None, screen_name=None, group_name=None):
        """ Moves friend to new group """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'move_friend(%s,%s)\' invoked for user %s' % (screen_name, group_name, u.screen_name))
        g = queries.getGroupByName(group_name, u)
        if g==None:
            raise json.JSONRPCError("Group %s does not exists" % group_name,
                                    code=ERR_NO_SUCH_GROUP)
        f = queries.getFriendByName(screen_name, u)
        if f==None:
            raise json.JSONRPCError("%s is not your friend" % screen_name,
                                    code=ERR_NO_SUCH_FRIEND)
        # TODO: transaction
        f.group = g
        f.put()
        # update status updates with new group
        q = data.StatusUpdate.gql('WHERE from_friend = :1', f.key())
        for s in q:
            s.group = g
            s.put()
        

    def json_new_group(self, auth_token=None, group_name=None):
        """ Create new group """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'new_group(%s)\' invoked for user %s' % (group_name, u.screen_name))

        #TODO: transacton
        if queries.getGroupByName(group_name, u)!=None:
            raise json.JSONRPCError("Group %s already exists" % group_name,
                                    code=ERR_GROUP_ALREADY_EXISTS)
            
        g = data.Group(name=group_name,
                       memberships_last_updated=datetime.datetime.now(),
                       user=u,
                       parent=u)
        g.put()
        return {
            'name': g.name,
            'rssurl': misc.groupRSS_URL(u.screen_name, g.name),
            'users': []
        }               
        
    def json_rename_group(self, auth_token=None,
                          old_group_name=None,
                          new_group_name=None):
        """ Create new group """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'rename_group(%s,%s)\' invoked for user %s' % (old_group_name, new_group_name, u.screen_name))

        if old_group_name==constants.DEFAULT_GROUP_NAME or \
           new_group_name==constants.DEFAULT_GROUP_NAME:
            raise json.JSONRPCError("Could not modify default group",
                                    code=ERR_DEFAULT_GROUP_MODIFICATION_NOT_PERMITTED)
        #TODO: transacton
        g = queries.getGroupByName(old_group_name, u)
        if g==None:
            raise json.JSONRPCError("Group %s does not exists" % old_group_name,
                                    code=ERR_NO_SUCH_GROUP)
        
        if queries.getGroupByName(new_group_name, u)!=None:
            raise json.JSONRPCError("Group %s already exists" % new_group_name,
                                    code=ERR_GROUP_ALREADY_EXISTS)

        g.name = new_group_name
        g.put()
    
    def json_delete_group(self, auth_token=None, group_name=None):
        """ Delete group """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'delete_group(%s)\' invoked for user %s' % (group_name, u.screen_name))

        if group_name==constants.DEFAULT_GROUP_NAME:
            raise json.JSONRPCError("Could not modify default group",
                                    code=ERR_DEFAULT_GROUP_MODIFICATION_NOT_PERMITTED)
        #TODO: transacton
        g = queries.getGroupByName(group_name, u)
        if g==None:
            raise json.JSONRPCError("Group %s does not exists" % group_name,
                                    code=ERR_NO_SUCH_GROUP)

        d = queries.getDefaultGroup(u)

        # Move all friends to default group
        for f in queries.groupMembers(g):
            f.group = d
            f.put()
            # update status updates with new group
            q = data.StatusUpdate.gql('WHERE from_friend = :1', f.key())
            for s in q:
                s.group = d
                s.put()
        g.delete()
        

    # -- implementation method below  ---


    def _verifyAuthToken(self, token):
        """ Verify user, returns screen name or None for invalid token"""

        q = data.User.gql('WHERE auth_token = :1', token)
        users = q.fetch(1)
        if len(users)!=1:
            logging.warning("Bad auth token %s" % token)
            raise json.JSONRPCError("Invalid auth token",
                                    code=ERR_BAD_AUTH_TOKEN)
        else:
            return users[0]

    def _buildAuthToken(self, me):
        return (str(uuid1()),
                datetime.datetime.now()+AUTH_TOKEN_LIFESPAN)
    
    
    def _updateUser(self, me, password, u):
        logging.debug('updating user %s' % me.screen_name)
        changed = False
        if u.password != password:
            u.password = password
            changed = True
        if changed:
            u.put()

    def _updateFriends(self, t, u):
        try:
            friends = t.GetFriends()
        except Exception:
            logging.exception("Error fetching friends for %s" % u.screen_name)
            raise json.JSONRPCError("Error fetching friends",
                                    code=ERR_TWITTER_COMM_ERROR)
        fnames = []
        for f in friends:
            fnames.append(f.screen_name)
            if queries.getFriendByName(f.screen_name, u)==None:
                queries.addNewFriend(u,f,queries.getDefaultGroup(u))

        q = data.Friend.gql('WHERE user = :1', u.key())
        n = 0
        for f in q:
            if f.screen_name not in fnames:
                logging.debug("%s is no longer friend." % f.screen_name)
                # remove all his status updates
                q1 = data.StatusUpdate.gql('WHERE from_friend = :1', f.key())
                for s in q1:
                    s.delete()
                f.delete()
            else:
                n = n+1
        logging.debug("User %s have %d friends" % (u.screen_name, n))
                

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([('/api', JSONHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
