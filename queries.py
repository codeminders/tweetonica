""" Various DB queries """

import logging
import datetime
from uuid import uuid4

from google.appengine.ext import db

import data
import constants

def loadGroups(u):
    q = data.Group.gql('WHERE user = :1', u.key())
    last = data.Group.gql('WHERE user = :1 ORDER BY viewed DESC LIMIT 1', u.key())
    lastgr = last[0].name
    res = {}
    for g in q:
        if not g.viewed:
            g.viewed = datetime.datetime.fromtimestamp(0)
            g.put()
        logging.debug('Group %s viewed at %s' % (g.name, g.viewed.strftime("%a, %d %b %Y %H:%M:%S GMT")))
        #unread = data.StatusUpdate.gql('WHERE group = :1', g)
        #group = :1 and
        unread = unreadForGroup(g)
        #data.StatusUpdate.gql('WHERE created_at>:1 and group=:2', g.viewed, g)
        #logging.debug('Got %d new items for %s' % (unread.count(), g.name))
        res[g.name]={
            'name': g.name,
            'memberships_last_updated': g.memberships_last_updated,
            "users": [{'screen_name':f.screen_name,
                       'real_name':f.real_name,
                       'profile_image_url': f.profile_image_url} \
                      for f in groupMembers(g)],
            'unread': unread,
            'last': g.name == lastgr
            };
    return res

def unreadForGroup(group):
    #this is bad, but GQL does not work as it should
    count = 0;
    q = data.StatusUpdate.gql('WHERE group = :1', group)
    for status in q:
        if status.created_at > group.viewed:
            count += 1
    return count

def groupMembers(g):
    q = data.Friend.gql('WHERE  group = :1', g.key())
    return q

def getUserByScreenName(screen_name):
    q = data.User.gql('WHERE screen_name = :1', screen_name)
    users = q.fetch(1)
    if len(users)==1:
        return users[0]
    else:
        return None

def getUserByCookie(cookie):
    q = data.User.gql('WHERE cookie = :1', cookie)
    users = q.fetch(1)
    if len(users)==1:
        return users[0]
    else:
        return None

def getUserByRSSToken(rss_token):
    q = data.User.gql('WHERE rss_token = :1', rss_token)
    users = q.fetch(1)
    if len(users)==1:
        return users[0]
    else:
        return None

def getUserByScreenNameAndRSSTOken(screen_name, rss_token):
    q = data.User.gql('WHERE screen_name = :1 and rss_token = :2', \
                      screen_name, rss_token)
    users = q.fetch(1)
    if len(users)==1:
        return users[0]
    else:
        return None

def logout(cookie):
    if cookie:
        u = getUserByCookie(cookie)
        if u:
            u.cookie = None
            u.put()

def createOrUpdateUser(screen_name,
                       id,
                       oauth_token,
                       oauth_token_secret,
                       cookie):
    u = getUserByScreenName(screen_name)
    if u:
        u.id = id
        u.oauth_token = oauth_token
        u.oauth_token_secret = oauth_token_secret
        u.cookie = cookie
        u.put()
        return u
    else:
        logging.debug('Creating new user %s' % screen_name)
        u = data.User(screen_name = screen_name,
                      id = id,
                      oauth_token = oauth_token,
                      oauth_token_secret = oauth_token_secret,
                      cookie = cookie,
                      rss_token = str(uuid4()),
                      use_HTTP_auth = False,
                      friendlist_last_updated = None,
                      remember_me =  True,
                      icons_only =  False)

        u.put()
        # Create default group
        g = data.Group(name=constants.DEFAULT_GROUP_NAME,
                       memberships_last_updated=datetime.datetime.now(),
                       user=u,
                       parent=u)
        g.put()
        # Create user timeline object
        tl = data.Timeline(user=u,
                           timeline_last_updated = None,
                           timeline_max_id=-1,
                           parent=u)
        tl.put()

        return u

def getDefaultGroup(u):
    q = data.Group.gql('WHERE name = :1 and user=:2',
                       constants.DEFAULT_GROUP_NAME,
                       u.key())
    groups = q.fetch(1)
    return groups[0]


def getGroupByName(group_name, u):
    if isinstance(group_name, str):
        group_name = unicode(group_name, 'utf-8')
    q = data.Group.gql('WHERE name = :1 and user=:2', group_name, u.key())
    groups = q.fetch(1)
    if len(groups)==1:
        return groups[0]
    else:
        return None


def getFriendByName(screen_name, u):
    q = data.Friend.gql('WHERE screen_name = :1 and user=:2',
                        screen_name, u.key())

    friends = q.fetch(1)
    if len(friends)==1:
        return friends[0]
    else:
        return None

def updateFriend(u,f,xf):
    changed = False
    if xf.real_name != f.name:
        xf.real_name = f.name
        changed = True

    if xf.profile_image_url != f.profile_image_url:
        xf.profile_image_url = f.profile_image_url
        changed = True

    if changed:
        xf.put()

def addNewFriend(u,f,g):
    logging.debug("Adding friend %s to %s" % (f.screen_name, u.screen_name))
    fo = data.Friend(id = f.id,
                     screen_name = f.screen_name,
                     real_name = f.name,
                     profile_image_url = f.profile_image_url,
                     user = u,
                     group = g,
                     parent=u)
    fo.put()


def getGroupTimeline(g, howmany=20, offset = 0):
    q = data.StatusUpdate.gql("WHERE group = :1 ORDER BY id DESC LIMIT %d OFFSET %d" % (howmany, offset),\
                              g.key())
    return q

def getTimelineById(uid, u):
    ''' TODO: does not work '''
    q = data.StatusUpdate.gql('WHERE id =:1 ', int(uid))
    tl = q.fetch(1)
    logging.debug("Got %d items" % len(tl))
    if len(tl)==1:
        if  tl[0].from_friend.user.key() == u.key():
            return tl[0]
        else:
            return None
    else:
        return None

def getUserTimeline(u):
    q = data.Timeline.gql('WHERE user=:1', u.key())
    tl = q.fetch(1)
    if len(tl)==1:
        return tl[0]
    else:
        # Temp. workaround for old users, before Timeline
        # object was introduced. To be removed later.
        tl = data.Timeline(user=u,
                           timeline_last_updated = None,
                           timeline_max_id=-1,
                           parent=u)
        tl.put()
        return tl

def getUserReplies(user):
    query = data.Replies.gql('WHERE user=:1', user.key())
    replies = query.fetch(1)
    if len(replies):
        return replies[0]
    else:
        tl = data.Replies(user=user,
                          replies_last_updated = None,
                          replies_max_id=-1,
                          parent=user)
        tl.put()
        return tl

def getReplies(user):
    query = data.Reply.gql('WHERE to=:1', user.key())
    replies = query.fetch(100)
    return replies
