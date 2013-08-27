#!/usr/bin/python3

import argparse
import requests
import netrc

from gi.repository import Gtk

from whatsup.mockserver import MockServer
from whatsup.widgets import WhatsupWindow


class NewsblurClient:
    def __init__(self, api_root):
        self.api_root = api_root
        self.session = requests.Session()
        self._cache = {}

    def login(self, username, password):
        url = self.api_root + '/api/login'
        payload = {'username': username, 'password': password}
        r = self.session.post(url, data=payload)

    def feeds(self):
        url = self.api_root + '/reader/feeds'
        r = self.session.get(url)
        d = r.json()
        assert(d['authenticated'])
        return d

    def river(self, feeds):
        url = self.api_root + '/reader/river_stories'
        payload = {'feeds': feeds}
        r = self.session.get(url, data=payload)
        return r.json()

    def cache_river(self, feeds):
        river = self.river(feeds)
        self._cache = river
        return river

    def all_stories(self):
        assert(self._cache)
        return self._cache

    def stories(self, feed):
        assert(self._cache)
        l = [s
             for s in self._cache['stories']
             if str(s['story_feed_id']) == feed
             ]
        return {'stories': l}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-connect',
                        help="Don't actually connect to the API",
                        action='store_true')
    parser.add_argument('--debug',
                        action='store_true')
    args = parser.parse_args()

    api_root = 'http://api.newsblur.com'
    if args.no_connect:
        s = MockServer(api_root)
        s.enable()

    n = netrc.netrc()
    username, _, password = n.authenticators('newsblur.com')
    c = NewsblurClient(api_root)
    c.login(username, password)
    d = c.feeds()
    feeds_unread = [k for k, v in d['feeds'].items() if v['nt'] > 0]
    river = c.cache_river(feeds_unread)
    if args.debug:
        from pprint import pprint
        pprint(d)
        pprint(river)
    win = WhatsupWindow(c)
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()
    if args.no_connect:
        s.disable()


if __name__ == '__main__':
    main()
