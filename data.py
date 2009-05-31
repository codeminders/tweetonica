''' Data layer '''

from google.appengine.ext import db


class PUser(db.Model):
    twitter_username = db.StringProperty(required=True)
    twitter_password = db.StringProperty(required=True)
    last_updated = db.DateTimeProperty(auto_now_add=True)

class Friend(db.Model):
    pass

class Group(db.Model):
    pass

class Timeline(db.Model):
    pass
