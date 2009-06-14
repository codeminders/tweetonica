''' Data layer '''

from google.appengine.ext import db

class User(db.Model):
    screen_name = db.StringProperty(required=True) # primary key
    password = db.StringProperty(required=True)
    auth_token = db.StringProperty()
    auth_token_expires = db.DateTimeProperty()
    id = db.IntegerProperty(required=True) 
    timeline_last_updated = db.DateTimeProperty()

class Group(db.Model):
    name = db.StringProperty(required=True) # primary key
    memberships_last_updated = db.DateTimeProperty()
    # foreing keys
    user = db.ReferenceProperty(User)

class Friend(db.Model):
    id = db.IntegerProperty(required=True) # primary key
    screen_name = db.StringProperty(required=True)
    real_name = db.StringProperty()
    profile_image_url = db.LinkProperty()
    # foreing keys
    user = db.ReferenceProperty(User)
    group = db.ReferenceProperty(Group)

class StatusUpdate(db.Model):
    id = db.IntegerProperty(required=True) # primary key
    text = db.StringProperty(required=True, multiline=True)
    created_at = db.DateTimeProperty()
    truncated = db.BooleanProperty()
    in_reply_to_status_id = db.IntegerProperty()
    in_reply_to_user_id = db.IntegerProperty()
    in_reply_to_screen_name = db.StringProperty()
    # foreing keys
    group = db.ReferenceProperty(Group)
    from_friend = db.ReferenceProperty(Friend)

