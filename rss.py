
import datetime
import logging
from urllib import unquote

from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext import db

from PyRSS2Gen import RSS2, SyInfo, RSSItem, Guid, Image

import queries
import data
import constants
import misc
from formatting import itemHTML

import timeline
import replies

class ATOMHandler(webapp.RequestHandler):

    def get(self, u, g=None):

        username = unquote(u)
        if g==None:
            group = constants.DEFAULT_GROUP_NAME
        else:
            group = unquote(g)

        logging.debug("Requested group '%s'" % group)

        rss_token = self.request.get(constants.TOKEN_PARAM_NAME,
                                     default_value=None)

        if not rss_token:
            u = misc.HTTP_authenticate()
            if not u:
                self.response.headers['WWW-Authenticate'] = \
                        'Basic realm=%s' % constants.REALM
                self.response.set_status(401)
                return
        else:
            u = queries.getUserByRSSToken(rss_token)
            if not u:
                self.response.set_status(403)
                return

        if group != constants.REPLIES_GROUP_NAME:
            logging.debug("Request for %s group feed" % group)
            timeline.updateTimeLine(u)

            g = queries.getGroupByName(group, u)
            if not g:
                logging.warning("Req. non-existing group '%s' for user '%s'" % \
                                (group, u.screen_name))
                self.response.set_status(404)
                return
            self._generateFeed(u, g)
        else:
            logging.debug("Request for replies feed")
            replies.updateReplies(u)
            self._generateRepliesFeed(u)


    def post(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')

    def put(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')

    def head(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')

    def options(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')

    def delete(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')

    def trace(self):
        self.response.set_status(405)
        self.response.headers.add_header('Allow', 'GET')


    # -- implementation method below  ---

    def _generateFeed(self, u, g):
        timeline = queries.getGroupTimeline(g)

        rssTitle = misc.getGroupRSS_title(u.screen_name, g.name)
        rssLink = misc.getGroupRSS_URL(u.screen_name, u.rss_token, \
                                       g.name, u.use_HTTP_auth)
        rssDescription = "Timeline for user %s group %s" % (u.screen_name, \
                                                            misc.getGroupTitle(g.name))
        rss = RSS2(
            title = rssTitle,
            link = rssLink,
            image = Image(url = "http://www.tweetonica.com/images/rssicon.png",
                          title = rssTitle,
                          link = rssLink,
                          width = 16,
                          height = 16,
                          description = rssDescription),
            description = rssDescription,
            language = 'en-us',
            managingEditor = 'tweetonica@codeminders.com (Tweetonica)',
            lastBuildDate = datetime.datetime.now(),
            syInfo = SyInfo(SyInfo.HOURLY,1,"1901-01-01T00:00+00:00")
            )

        for e in timeline:
            # TODO: nice text formatting with links to @ and #, etc.
            link = "http://twitter.com/%s/status/%d" % \
                   (e.from_friend.screen_name, e.id)

            subj = "%s: %s" % (e.from_friend.screen_name, e.text)
            rss.items.append(RSSItem(title = subj,
                                     link = link,
                                     guid = Guid(link),
                                     description = itemHTML(e),
                                     pubDate = e.created_at))

        self.response.headers['Content-Type'] = 'application/rss+xml'
        rss.write_xml(self.response.out)

    def _generateRepliesFeed(self, user):
        replies = queries.getReplies(user)
        rssTitle = misc.getGroupRSS_title(user.screen_name, constants.REPLIES_GROUP_NAME)
        rssLink = misc.getGroupRSS_URL(user.screen_name, user.rss_token,
                                       constants.REPLIES_GROUP_NAME,
                                       user.use_HTTP_auth)
        rssDescription = "Replies for user %s" % user.screen_name
        rss = RSS2(
            title = rssTitle,
            link = rssLink,
            image = Image(url = "http://www.tweetonica.com/images/rssicon.png",
                          title = rssTitle,
                          link = rssLink,
                          width = 16,
                          height = 16,
                          description = rssDescription),
            description = rssDescription,
            language = 'en-us',
            managingEditor = 'tweetonica@codeminders.com (Tweetonica)',
            lastBuildDate = datetime.datetime.now(),
            syInfo = SyInfo(SyInfo.HOURLY, 1, "1901-01-01T00:00+00:00")
            )

        for reply in replies:
            # TODO: nice text formatting with links to @ and #, etc.
            link = "http://twitter.com/%s/status/%d" % \
                   (reply.author, reply.id)

            subj = "%s: %s" % (reply.author, reply.text)
            rss.items.append(RSSItem(title = subj,
                                     link = link,
                                     guid = Guid(link),
                                     description = itemHTML(reply),
                                     pubDate = reply.created_at))

        self.response.headers['Content-Type'] = 'application/rss+xml'
        rss.write_xml(self.response.out)



def main():
    logging.getLogger().setLevel(logging.DEBUG)
    logging.debug("Starting")
    app = webapp.WSGIApplication([("%s/(.+)/(.+)" % constants.FEED_PATH_PREFIX,
                                   ATOMHandler)], debug=True)
    util.run_wsgi_app(app)


if __name__ == '__main__':
    main()