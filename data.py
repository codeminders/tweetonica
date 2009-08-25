''' Data layer '''

from google.appengine.ext import db

class User(db.Model):
    screen_name = db.StringProperty(required=True) # primary key
    # OAuth 'access_token'
    oauth_token = db.StringProperty()
    oauth_token_secret = db.StringProperty()
    # our auth cookie
    cookie = db.StringProperty()
    # our token used to authenticate RSS users
    rss_token = db.StringProperty()
    use_HTTP_auth =  db.BooleanProperty()
    user_created = db.DateTimeProperty(auto_now_add=True)
    friendlist_last_updated = db.DateTimeProperty()
    id = db.IntegerProperty(required=True)
    # Misc user preferences.
    remember_me =  db.BooleanProperty()
    icons_only =  db.BooleanProperty()

class Timeline(db.Model):
    """ To avoid DB contention (see Ticket #25),
    this sub-object holds
    timeline-related properties of User
    """
    user = db.ReferenceProperty(User)
    timeline_last_updated = db.DateTimeProperty()
    timeline_max_id = db.IntegerProperty()

class Replies(db.Model):
    user = db.ReferenceProperty(User)
    replies_last_updated = db.DateTimeProperty()
    replies_max_id = db.IntegerProperty()

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

class Reply(db.Model):
    id = db.IntegerProperty(required=True) # primary key
    to = db.ReferenceProperty(User)
    text = db.StringProperty(required=True, multiline=True)
    created_at = db.DateTimeProperty()
    truncated = db.BooleanProperty()
    in_reply_to_status_id = db.IntegerProperty()
    in_reply_to_user_id = db.IntegerProperty()
    in_reply_to_screen_name = db.StringProperty()
    author = db.StringProperty(required=True, multiline=False)

class OAuthRequestToken(db.Model):
    """OAuth Request Token."""
    oauth_token = db.StringProperty()
    oauth_token_secret = db.StringProperty()
    created = db.DateTimeProperty(auto_now_add=True)

