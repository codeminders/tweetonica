import os

import datetime, time
import logging
from urllib2 import HTTPError
from uuid import uuid4

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

import twitter
import json
import data
import queries
import constants
import misc
import timeline
from oauth import OAuthClient
from formatting import itemHTML


""" Timeline update frequency. Update no more often than this """
FRIENDS_SYNC_FREQ = datetime.timedelta(1, 0)

# JSON-RPC Error Codes (101=999)
ERR_TWITTER_AUTH_FAILED = 101
ERR_BAD_AUTH_TOKEN = 102
ERR_TWITTER_COMM_ERROR = 103
ERR_GROUP_ALREADY_EXISTS = 104
ERR_NO_SUCH_GROUP = 105
ERR_NO_SUCH_FRIEND = 106
ERR_SPECIAL_GROUP_MODIFICATION_NOT_PERMITTED = 107
ERR_NO_SUCH_ENTRY = 108


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

    def json_create_friendship(self, auth_token=None, screen_name=None):
        """ Add user as friend (follow).
        It will be also added to default group.
        Args:
        screen_name: screen name of the user to follow
        """
        u = self._verifyAuthToken(auth_token)
        t = twitter.Api(oauth=OAuthClient(handler=None,token=u))
        try:
            f = t.CreateFriendship(screen_name)
        except Exception:
            logging.exception("Error creating friendship for %s" % u.screen_name)
            raise json.JSONRPCError("Error creating friendship",
                                    code=ERR_TWITTER_COMM_ERROR)
        # Add tweetonica as friend, to default group.
        queries.addNewFriend(u,f,queries.getDefaultGroup(u))

    def json_get_prefs(self, auth_token=None):
        """ Get preferences for current user
        """
        logging.debug('Method \'get_prefs\' invoked for cookie %s' % auth_token)
        u = self._verifyAuthToken(auth_token)
        return self._get_user_prefs(u)

    def json_set_prefs(self, auth_token=None, prefs={}):
        """ Set preferences for current user
        """
        logging.debug('Method \'set_prefs\' invoked for cookie %s' % auth_token)
        u = self._verifyAuthToken(auth_token)
        # 'screen_name' and could not be changed
        u.remember_me = prefs['remember_me']
        u.icons_only = prefs['icons_only']
        u.use_HTTP_auth = prefs['use_HTTP_auth']
        u.put()
        return self._get_user_prefs(u)


    def json_logout(self, auth_token=None):
        """ Invalidates user cookie
        """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'logout\' invoked for user %s' % u.screen_name)
        u.cookie = None
        u.put()

    def json_reset_RSS_token(self, auth_token=None):
        """ Reset RSS token.
        """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'reset_RSS_token\' invoked for user %s' % u.screen_name)
        u.rss_token = str(uuid4())
        u.put()

    def json_sync_friends(self, auth_token=None, force=False):
        """ Sync friend list with twitter.
        Args:
        force - ignore TTL and update from twitter now

        Return:
        True if friends have been added or removed. False if friends list
             is unchanged
        """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'sync_fiends\' invoked for user %s' % u.screen_name)
        need_update = False
        if force or u.friendlist_last_updated==None:
            need_update = True
        else:
            need_update = (u.friendlist_last_updated+FRIENDS_SYNC_FREQ)\
                          < datetime.datetime.now()

        if need_update:
            return self._updateFriends(u)
        else:
            return False


    def json_get_friends(self, auth_token=None):
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'get_fiends\' invoked for user %s' % u.screen_name)
        res = queries.loadGroups(u)

        for x in res.keys():
            logging.debug('Threre are %d unread items in %s' % (res[x]['unread'], res[x]['name']))
            del res[x]['memberships_last_updated']
            res[x]['rssurl']=misc.getGroupRSS_URL(u.screen_name,
                                               u.rss_token,
                                               x, u.use_HTTP_auth)
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

        if group_name.startswith(constants.SPECIAL_GROUP_PREFIX):
            raise json.JSONRPCError("User-defined group name could not start with '%s'" % constants.SPECIAL_GROUP_PREFIX,
                                    code=ERR_SPECIAL_GROUP_MODIFICATION_NOT_PERMITTED)

        #TODO: transacton
        if queries.getGroupByName(group_name, u)!=None:
            raise json.JSONRPCError("Group %s already exists" % group_name,
                                    code=ERR_GROUP_ALREADY_EXISTS)

        g = data.Group(name=unicode(group_name),
                       memberships_last_updated=datetime.datetime.now(),
                       user=u,
                       parent=u,
                       viewed=datetime.datetime.fromtimestamp(0))
        g.put()
        return {
            'name': g.name,
            'rssurl': misc.getGroupRSS_URL(u.screen_name,
                                        u.rss_token, g.name,
                                        u.use_HTTP_auth),
            'users': []
        }

    def json_rename_group(self, auth_token=None,
                          old_group_name=None,
                          new_group_name=None):
        """ Create new group """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'rename_group(%s,%s)\' invoked for user %s' % (old_group_name, new_group_name, u.screen_name))

        if old_group_name.startswith(constants.SPECIAL_GROUP_PREFIX) or \
           new_group_name.startswith(constants.SPECIAL_GROUP_PREFIX):
            raise json.JSONRPCError("Could not modify special group",
                                    code=ERR_SPECIAL_GROUP_MODIFICATION_NOT_PERMITTED)
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
        return {
            'name': g.name,
            'rssurl': misc.getGroupRSS_URL(u.screen_name,
                                        u.rss_token, g.name,
                                        u.use_HTTP_auth)
        }

    def json_delete_group(self, auth_token=None, group_name=None):
        """ Delete group """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'delete_group(%s)\' invoked for user %s' % (group_name, u.screen_name))

        if group_name.startswith(constants.SPECIAL_GROUP_PREFIX):
            raise json.JSONRPCError("Could not modify special group",
                                    code=ERR_SPECIAL_GROUP_MODIFICATION_NOT_PERMITTED)
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

    def json_get_feed(self, auth_token=None, group_name=None, offset = 0):
        """ Feed entries for a given group """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'get_feed(%s, %d)\' invoked for user %s' % (group_name, offset, u.screen_name))

        timeline.updateTimeLine(u)

        g = queries.getGroupByName(group_name, u)
        if not g:
            logging.warning("Req. non-existing group '%s' for user '%s'" % \
                            (group, u.screen_name))
            raise json.JSONRPCError("Group %s does not exists" % group_name,
                                    code=ERR_NO_SUCH_GROUP)

        tl = queries.getGroupTimeline(g, 20, offset)

        ret = []
        for e in tl:
            ret.append({'id' : e.id,
                        'html' : itemHTML(e, False),
                        'from' : {'screen_name' : e.from_friend.screen_name,
                                  'real_name' : e.from_friend.real_name,
                                  'profile_image_url' : e.from_friend.profile_image_url},
                        'created_at': long(time.mktime(e.created_at.timetuple()))})
 
        g.viewed = queries.getUserTimeline(u).timeline_last_updated
        #datetime.datetime.now()
        g.put()

        return ret

    def json_get_feed_by_id(self, auth_token=None, id = None):
        """ Feed entries with specified ID """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'get_feed_by_id(%s)\' invoked for user %s' % (id, u.screen_name))

        e = queries.getTimelineById(id, u)
        if not e:
            logging.warning("Req. non-existing feed '%s' for user '%s'" % \
                            (id, u.screen_name))
            raise json.JSONRPCError("Feed entry %s does not exist" % id,
                                    code=ERR_NO_SUCH_ENTRY)

        return {'id' : e.id,
                'text' : e.text,
                'html' : itemHTML(e, False),
                'from' : {'screen_name' : e.from_friend.screen_name,
                          'real_name' : e.from_friend.real_name,
                          'profile_image_url' : e.from_friend.profile_image_url},
                'created_at': long(time.mktime(e.created_at.timetuple()))}

    def json_post_tweet(self, auth_token=None, message=None, in_reply_to=None):
        """ Posts a tweet """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'post_tweet()\' invoked for user %s' % (u.screen_name))

        t = twitter.Api(oauth=OAuthClient(handler=None,token=u))
        try:
            if in_reply_to == '':
                in_reply_to = None
            f = t.PostUpdate(message, in_reply_to)
        except Exception:
            logging.exception("Post failed")
            raise json.JSONRPCError("Post failed",
                                    code=ERR_TWITTER_COMM_ERROR)

    def json_post_direct_tweet(self, auth_token=None, to=None, message=None):
        """ Posts a tweet """
        u = self._verifyAuthToken(auth_token)
        logging.debug('Method \'post_direct_tweet(%s)\' invoked for user %s' % (to, u.screen_name))

        t = twitter.Api(oauth=OAuthClient(handler=None,token=u))
        try:
            f = t.PostDirectMessage(to, message)
        except Exception:
            logging.exception("Direct post failed")
            raise json.JSONRPCError("Direct post failed",
                                    code=ERR_TWITTER_COMM_ERROR)


    # -- implementation method below  ---

    def _get_user_prefs(self, u):

        return {'screen_name' : u.screen_name,
                'remember_me' : u.remember_me,
                'icons_only': u.icons_only,
                'use_HTTP_auth' : u.use_HTTP_auth,
                'OPML_feed_url' : misc.getOPML_URL(u.screen_name,
                                                   u.rss_token,
                                                   u.use_HTTP_auth),
                'OPML_download_url' : misc.getOPML_URL(u.screen_name,
                                                       u.rss_token,
                                                       False)
                }

    def _verifyAuthToken(self, auth_token):
        """ Verify user, returns screen name or None for invalid token"""
        u = queries.getUserByCookie(auth_token)
        if u:
            return u
        else:
            raise json.JSONRPCError("Invalid auth token",
                                    code=ERR_BAD_AUTH_TOKEN)

    def _updateFriends(self, u):
        logging.debug('Synchronizing friends for user %s' % u.screen_name)

        t = twitter.Api(oauth=OAuthClient(handler=None,token=u))
        try:
            friends = t.GetFriends()
        except Exception:
            logging.exception("Error fetching friends for %s" % u.screen_name)
            raise json.JSONRPCError("Error fetching friends",
                                    code=ERR_TWITTER_COMM_ERROR)
        changed = False
        fnames = []
        for f in friends:
            fnames.append(f.screen_name)
            xf=queries.getFriendByName(f.screen_name, u)
            if xf==None:
                changed = True
                queries.addNewFriend(u,f,queries.getDefaultGroup(u))
            else:
                if queries.updateFriend(u,f,xf):
                    changed = True

        q = data.Friend.gql('WHERE user = :1', u.key())
        n = 0
        for f in q:
            if f.screen_name not in fnames:
                logging.debug("%s is no longer friend." % f.screen_name)
                # remove all his status updates
                changed = True
                q1 = data.StatusUpdate.gql('WHERE from_friend = :1', f.key())
                for s in q1:
                    s.delete()
                f.delete()
            else:
                n = n+1
        u.friendlist_last_updated=datetime.datetime.now()
        u.put()
        logging.debug("User %s have %d friends" % (u.screen_name, n))

        timeline.updateTimeLine(u)

        return changed

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([('/api', JSONHandler)], debug=True)
    util.run_wsgi_app(app)

if __name__ == '__main__':
    main()
