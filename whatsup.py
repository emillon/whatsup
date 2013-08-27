#!/usr/bin/python3

import argparse
import requests
import netrc

from gi.repository import Gtk


class NewsblurClient:
    def __init__(self, api_root):
        self.api_root = api_root
        self.session = requests.Session()

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


class MockClient:
    """
    A client that is compatible with NewsblurClient, but
    does not connect to the Internet.
    """
    def feeds(self):
        d = {'feeds': {1: {'feed_title': 'Feed 1',
                           'nt': 2,
                           },
                       2: {'feed_title': 'Feed 2',
                           'nt': 1,
                           },
                       3: {'feed_title': 'Feed 3',
                           'nt': 0,
                           },
                       4: {'feed_title': 'Feed 4',
                           'nt': 2,
                           },
                       }
             }
        return d

    def river(self, feeds):
        d = {}
        return d


class FeedListWidget(Gtk.ScrolledWindow):
    def __init__(self, feeds):
        super().__init__()
        store = Gtk.ListStore(str, int)
        total_unread = sum([f['nt'] for f in feeds.values()])
        store.append(['All', total_unread])
        for f in feeds.values():
            title = f['feed_title']
            unread = f['nt']
            row = [title, unread]
            store.append(row)

        view = Gtk.TreeView(store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Feed", renderer, text=0)
        view.append_column(column)
        column = Gtk.TreeViewColumn("Unread", renderer, text=1)
        view.append_column(column)

        self.tree_view = view
        self.add(view)


class StoriesListWidget(Gtk.TreeView):
    def __init__(self):
        store = Gtk.ListStore(str)
        super().__init__(store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Title", renderer, text=0)
        self.append_column(column)


class WhatsupWindow(Gtk.Window):

    def __init__(self, client):
        super().__init__()
        self.client = client

        box = Gtk.Box()

        d = client.feeds()
        wfeeds = FeedListWidget(d['feeds'])
        box.pack_start(wfeeds, False, True, 0)
        wstories = StoriesListWidget()
        box.pack_start(wstories, True, True, 0)

        self.add(box)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-connect',
                        help="Don't actually connect to the API",
                        action='store_true')
    parser.add_argument('--debug',
                        action='store_true')
    args = parser.parse_args()

    c = MockClient()
    if not args.no_connect:
        n = netrc.netrc()
        username, _, password = n.authenticators('newsblur.com')
        c = NewsblurClient('http://api.newsblur.com')
        c.login(username, password)
    d = c.feeds()
    feeds_unread = [k for k, v in d['feeds'].items() if v['nt'] > 0]
    river = c.river(feeds_unread)
    if args.debug:
        from pprint import pprint
        pprint(d)
        pprint(river)
    win = WhatsupWindow(c)
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
