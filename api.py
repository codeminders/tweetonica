import os

import datetime
import logging
from urllib2 import HTTPError
from uuid import uuid1

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext import db

import twitter
import json
import data

DEFAULT_GROUP_NAME="__ALL__"

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
        try:
            me =  t.verifyCredentials()
        except HTTPError, e:
            if e.code==401:
                raise json.JSONRPCError("Twitter authentication failed",
                                    code=ERR_TWITTER_AUTH_FAILED)
            else:
                logging.exception("Error talking to twitter %s" % screen_name)
                raise json.JSONRPCError("Error talking to twiter",
                                    code=ERR_TWITTER_COMM_ERROR)
                

        u = self._getUserByScreenName(screen_name)
        if u:
            self._updateUser(me, password, u)
        else:
            u = self._newUser(me, password)
        self._updateFriends(t,u)
        (auth_token, auth_token_expires)  = self._buildAuthToken(me)
        u.auth_token = auth_token
        u.auth_token_expires = auth_token_expires
        u.put()
        return { 'auth_token' : auth_token,
                 'auth_token_expires' : auth_token_expires.isoformat() }

    def json_get_friends(self, auth_token=None):
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'get_fiends\' invoked for user %s' % u.screen_name)
        q = data.Group.gql('WHERE user = :1', u.key())
        res = {}
        for g in q:
            res[g.name]={
                'name': g.name,
                'rssurl': self._groupRSS_URL(g),
                "users": [{'screen_name':f.screen_name,
                           'real_name':f.real_name,
                           'profile_image_url': f.profile_image_url} \
                          for f in self._groupMembers(g)]
                };
        return res

    def json_move_friend(self, auth_token=None, screen_name=None, group_name=None):
        """ Moves friend to new group """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'move_friend(%s,%s)\' invoked for user %s' % (screen_name, group_name, u.screen_name))
        g = self._getGroupByName(group_name, u)
        if g==None:
            raise json.JSONRPCError("Group %s does not exists" % group_name,
                                    code=ERR_NO_SUCH_GROUP)
        f = self._getFriendByName(screen_name, u)
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
        if self._getGroupByName(group_name, u)!=None:
            raise json.JSONRPCError("Group %s already exists" % group_name,
                                    code=ERR_GROUP_ALREADY_EXISTS)
            
        g = data.Group(name=group_name,
                       memberships_last_updated=datetime.datetime.now(),
                       user=u,
                       parent=u)
        g.put()
        
    def json_rename_group(self, auth_token=None,
                          old_group_name=None,
                          new_group_name=None):
        """ Create new group """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'rename_group(%s,%s)\' invoked for user %s' % (old_group_name, new_group_name, u.screen_name))

        if old_group_name==DEFAULT_GROUP_NAME or \
           new_group_name==DEFAULT_GROUP_NAME:
            raise json.JSONRPCError("Could not modify default group",
                                    code=ERR_DEFAULT_GROUP_MODIFICATION_NOT_PERMITTED)
        #TODO: transacton
        g = self._getGroupByName(old_group_name, u)
        if g==None:
            raise json.JSONRPCError("Group %s does not exists" % old_group_name,
                                    code=ERR_NO_SUCH_GROUP)
        
        if self._getGroupByName(new_group_name, u)!=None:
            raise json.JSONRPCError("Group %s already exists" % new_group_name,
                                    code=ERR_GROUP_ALREADY_EXISTS)

        g.name = new_group_name
        g.put()
    
    def json_delete_group(self, auth_token=None, group_name=None):
        """ Delete group """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'delete_group(%s)\' invoked for user %s' % (group_name, u.screen_name))

        if group_name==DEFAULT_GROUP_NAME:
            raise json.JSONRPCError("Could not modify default group",
                                    code=ERR_DEFAULT_GROUP_MODIFICATION_NOT_PERMITTED)
        #TODO: transacton
        g = self._getGroupByName(group_name, u)
        if g==None:
            raise json.JSONRPCError("Group %s does not exists" % group_name,
                                    code=ERR_NO_SUCH_GROUP)

        d = self._getDefaultGroup(u)

        # Move all friends to default group
        for f in self._groupMembers(g):
            f.group = d
            f.put()
            # update status updates with new group
            q = data.StatusUpdate.gql('WHERE from_friend = :1', f.key())
            for s in q:
                s.group = d
                s.put()
        g.delete()
        

    def json_get_user_info(self, auth_token=None, screen_name=None):
        """ Get user info """
        pass

    # -- implementation method below  ---

    def _updateTimeLine(self,u,t):
        # TODO: since
        # TODO: paging back
        try:
            timeline = t.GetFriendsTimeline()
        except Exception:
            logging.exception("Error fetching friends timeline for %s" % u.screen_name)
            raise json.JSONRPCError("Error fetching friends timeline",
                                    code=ERR_TWITTER_COMM_ERROR)
        for t in timeline:
            logging.debug("Got timeline entry %s" % t)
            pass

    def _groupMembers(self,g):
        q = data.Friend.gql('WHERE  group = :1', g.key())
        return q
    
    def _groupRSS_URL(self,g):
        #TODO implemnt
        return "http://example.com/%s/%s" % (g.user.screen_name, g.name)
    
    def _getUserByScreenName(self, screen_name):
        q = data.User.gql('WHERE screen_name = :1', screen_name)
        users = q.fetch(1)
        if len(users)==1:
            return users[0]
        else:
            return None

    def _verifyAuthToken(self, token):
        """ Verify user, returns screen name or None for invalid token"""

        q = data.User.gql('WHERE auth_token = :1', token)
        users = q.fetch(1)
        if len(users)!=1:
            logging.warning("Bad auth token %s" % token)
            raise json.JSONRPCError("Invalid auth token",
                                    code=ERR_BAD_AUTH_TOKEN)
        else:
            if users[0].auth_token_expires < datetime.datetime.now():
                logging.warning("Expired auth token %s" % token)
                raise json.JSONRPCError("Expired auth token",
                                        code=ERR_BAD_AUTH_TOKEN)
            else:
                return users[0]

    def _buildAuthToken(self, me):
        return (str(uuid1()),
                datetime.datetime.now()+AUTH_TOKEN_LIFESPAN)
    
    def _newUser(self, me, password):
        """ Creates new user record with empty default group """
        logging.debug('creating user %s' % me.screen_name)
        u = data.User(screen_name = me.screen_name,
                      password = password,
                      id = me.id,
                      timeline_last_updated = None)
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
        try:
            friends = t.GetFriends()
        except Exception:
            logging.exception("Error fetching friends for %s" % u.screen_name)
            raise json.JSONRPCError("Error fetching friends",
                                    code=ERR_TWITTER_COMM_ERROR)
        fnames = []
        for f in friends:
            fnames.append(f.screen_name)
            if self._getFriendByName(f.screen_name, u)==None:
                self._addNewFriend(u,f,self._getDefaultGroup(u))

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
                


    def _getDefaultGroup(self, u):
        q = data.Group.gql('WHERE name = :1 and user=:2', DEFAULT_GROUP_NAME,
                           u.key())
        groups = q.fetch(1)
        return groups[0]

    def _getGroupByName(self, group_name, u):
        q = data.Group.gql('WHERE name = :1 and user=:2', group_name, u.key())
        groups = q.fetch(1)
        if len(groups)==1:
            return groups[0]
        else:
            return None

    def _getFriendByName(self, screen_name, u):
        q = data.Friend.gql('WHERE screen_name = :1 and user=:2',
                            screen_name, u.key())
        
        friends = q.fetch(1)
        if len(friends)==1:
            return friends[0]
        else:
            return None
    

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
