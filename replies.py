import datetime
import logging
from urllib import unquote

import queries
import twitter as tw
import data
import constants
import misc
from formatting import itemHTML
from mclock import MCLock

from oauth import OAuthClient


""" Timeline update frequency. Update no more often than this """
REPLIES_UPDATE_FREQ = datetime.timedelta(0, 90)

""" How many timeline entries to fetch. No more than 200! """
FETCH_COUNT=100
REPLIES_LOCK_TIMEOUT=600

def updateReplies(user):
    replies = queries.getUserReplies(user)
    twitter = tw.Api(oauth = OAuthClient(handler = None, token = user))
    if replies.replies_last_updated == None or \
           (replies.replies_last_updated + REPLIES_UPDATE_FREQ) < \
           datetime.datetime.now():
        lock = MCLock(user.screen_name, timeout = REPLIES_LOCK_TIMEOUT)
        if lock.lock():
            try:
                _updateReplies(user, twitter, replies)
            finally:
                lock.unlock()
        else:
            logging.debug("Replies for %s is already been updated" % user.screen_name)

    else:
        logging.debug("Replies for %s is up to date" % user.screen_name)


def _updateReplies(user, twitter, replies):
    logging.debug("Updating replies for user %s" % user.screen_name)

    fetched = 0
    since_id = replies.replies_max_id
    since = datetime.datetime.now() - constants.BACK_ENTRIES
    try:
        logging.debug("Fetching replies for user%s " % user.screen_name)
        reply_list = twitter.GetReplies()
    except Exception:
        logging.exception("Error fetching replies for %s" %  user.screen_name)
        raise
    if not reply_list: return
    for reply in reply_list:
        logging.debug("Got reply entry %d" % reply.id)
        if reply.id <= since_id:
            logging.debug("Got reply with id older than since_id")
            break

        reply_created = datetime.datetime.utcfromtimestamp( \
                                                 reply.GetCreatedAtInSeconds())

        if reply_created <= since:
            logging.debug("Stopping, as encountered an entry, " \
                          "which is older than cut off date %s" %  \
                          since.ctime())
            break

        if replies.replies_max_id < reply.id:
            replies.replies_max_id = reply.id
        if reply.user.screen_name == user.screen_name:
            # skip own entries
            continue

        reply_author = reply.user.screen_name
        _addReplyEntry(reply, reply_created, user, reply_author)
        fetched += 1

    replies.put()
    replies.replies_last_updated = datetime.datetime.now()
    replies.put()
    logging.debug("Fetced  %d reply for %s" %  (fetched, user.screen_name))

def _addReplyEntry(reply, ts, user, friend):
    logging.debug("Adding reply entry %d" % reply.id)
    new_reply = data.Reply(id = reply.id,
                           to = user,
                           text = reply.text,
                           created_at = ts,
                           truncated = False, #TODO
                           in_reply_to_status_id = -1, #TODO
                           in_reply_to_user_id = -1, #TODO
                           in_reply_to_screen_name = None, #TODO
                           author = unicode(friend))
    new_reply.put()
