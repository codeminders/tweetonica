''' Data layer '''

from google.appengine.ext import db


class User(db.Model):
    twitter_username = db.StringProperty(required=True)
    twitter_password = db.StringProperty(required=True)
    last_updated = db.DateTimeProperty(auto_now_add=True)

class Group(db.Model):
    name = db.StringProperty(required=True)
    puser = db.ReferenceProperty(User)

class Friend(db.Model):
    twitter_username = db.StringProperty(required=True)
    group = db.ReferenceProperty(Group)

class StatusUpdate(db.Model):
    from_friend = db.ReferenceProperty(Friend)

