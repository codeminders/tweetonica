""" Various DB queries """

import logging
import datetime

from google.appengine.ext import db

import data
import constants

def loadGroups(u):
    q = data.Group.gql('WHERE user = :1', u.key())
    res = {}
    for g in q:
        res[g.name]={
            'name': g.name,
            "users": [{'screen_name':f.screen_name,
                       'real_name':f.real_name,
                       'profile_image_url': f.profile_image_url} \
                      for f in groupMembers(g)]
            };
    return res

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


def newUser(me, password):
    """ Creates new user record with empty default group """
    logging.debug('creating user %s' % me.screen_name)
    u = data.User(screen_name = me.screen_name,
                  password = password,
                  id = me.id,
                  timeline_last_updated = None,
                  timeline_max_id=-1)
    u.put()
    g = data.Group(name=constants.DEFAULT_GROUP_NAME,
                   memberships_last_updated=datetime.datetime.now(),
                   user=u,
                   parent=u)
    g.put()
    return u


def getDefaultGroup(u):
    q = data.Group.gql('WHERE name = :1 and user=:2',
                       constants.DEFAULT_GROUP_NAME,
                       u.key())
    groups = q.fetch(1)
    return groups[0]

def getGroupByName(group_name, u):
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
