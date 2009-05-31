''' Data layer '''

from google.appengine.ext import db

class User(db.Model):
    id = db.IntegerProperty(required=True) # primary key
    screen_name = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    timeline_last_updated = db.DateTimeProperty(auto_now_add=True)

class Group(db.Model):
    name = db.StringProperty(required=True) # primary key
    # foreing keys
    user = db.ReferenceProperty(User)

class Friend(db.Model):
    id = db.IntegerProperty(required=True) # primary key
    screen_name = db.StringProperty(required=True)
    real_name = db.StringProperty()
    profile_image_url = db.LinkProperty()
    # foreing keys
    group = db.ReferenceProperty(Group)

class StatusUpdate(db.Model):
    id = db.IntegerProperty(required=True) # primary key
    text = db.StringProperty(required=True, multiline=True)
    created_at = db.DateTimeProperty(auto_now_add=False)
    truncated = db.BooleanProperty()
    in_reply_to_status_id = db.IntegerProperty()
    in_reply_to_user_id = db.IntegerProperty()
    in_reply_to_screen_name = db.StringProperty()
    # foreing keys
    from_friend = db.ReferenceProperty(Friend)

