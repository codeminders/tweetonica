import datetime
import logging
from urllib import unquote
 
import queries
import twitter
import data
import constants
import misc
from formatting import itemHTML
from mclock import MCLock

from oauth import OAuthClient


""" Timeline update frequency. Update no more often than this """
TIMELINE_UPDATE_FREQ = datetime.timedelta(0, 90)

""" How many timeline entries to fetch. No more than 200! """
FETCH_COUNT=100
MAX_PAGES_TO_FETCH=3
TIMELINE_LOCK_TIMEOUT=600

def updateTimeLine(u):
    tl = queries.getUserTimeline(u)
    t = twitter.Api(oauth=OAuthClient(handler=None,token=u))
    if tl.timeline_last_updated==None or \
           (tl.timeline_last_updated+TIMELINE_UPDATE_FREQ) < \
           datetime.datetime.now():
        l = MCLock(u.screen_name, timeout=TIMELINE_LOCK_TIMEOUT)
        if l.lock():
            try:
                _updateTimeLine(u,t,tl)
            finally:
                l.unlock()
        else:
            logging.debug("Timeline for %s is already been updated" % u.screen_name)
            
    else:
        logging.debug("Timeline for %s is up to date" % u.screen_name)


def _updateTimeLine(u,t,tl):
    logging.debug("Updating timeline for user %s" % u.screen_name)

    groups = queries.loadGroups(u)

    ui = {} # friend index index
    page = 1
    done = False
    fetched = 0
    since_id = tl.timeline_max_id
    since = datetime.datetime.now()-constants.BACK_ENTRIES
    while not done and page<=MAX_PAGES_TO_FETCH:
        try:
            logging.debug("Fetching page %d of %s timeline (since id %d)" % \
                          (page, u.screen_name, since_id))
            timeline = t.GetFriendsTimeline(since_id = since_id,\
                                            page=page, count=FETCH_COUNT)
            page = page + 1
        except Exception:
            logging.exception("Error fetching friends timeline for %s" % \
                              u.screen_name)
            raise
        if timeline==None or len(timeline)==0:
            break
        for e in timeline:
            logging.debug("Got timeline entry %d" % e.id)
            if e.id<=since_id:
                done = True
                break

            ts = datetime.datetime.utcfromtimestamp(\
                e.GetCreatedAtInSeconds())

            if ts<=since:
                logging.debug("Stopping, as encountered an entry, " \
                              "which is older than cut off date %s" %  \
                              since.ctime())
                done = True
                break

            if tl.timeline_max_id < e.id:
                tl.timeline_max_id = e.id
            if e.user.screen_name==u.screen_name:
                # skip my own entries
                continue
            eu = ui.get(e.user.screen_name, None)
            if eu == None:
                eu = queries.getFriendByName(e.user.screen_name,u)
                if eu == None:
                    logging.error("Entry from unknown friend %s!" % \
                                  e.user.screen_name)
                    continue
                else:
                     ui[e.user.screen_name]=eu
            _addTimeLineEntry(e,ts,u,eu)
            fetched = fetched+1
        # Save timeline_max_id between page
        tl.put()
        
    tl.timeline_last_updated=datetime.datetime.now()
    tl.put()
    logging.debug("Fetced  %d timeline entries for %s" % \
                  (fetched, u.screen_name))

def _addTimeLineEntry(e,ts,u,friend):
    logging.debug("Adding timeline entry %d" % e.id)
    s = data.StatusUpdate(id = e.id,
                          text = e.text,
                          created_at = ts,
                          truncated = False, #TODO
                          in_reply_to_status_id = -1, #TODO
                          in_reply_to_user_id = -1, #TODO
                          in_reply_to_screen_name = None, #TODO
                          group = friend.group.key(),
                          from_friend = friend.key())
    s.put()
