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


class WhatsupWindow(Gtk.Window):

    def __init__(self, client):
        super().__init__()
        self.client = client

        box = Gtk.Box()

        d = client.feeds()
        box.pack_start(self.feed_list_widget(d['feeds']), False, True, 0)
        box.pack_start(self.stories_widget(), True, True, 0)

        self.add(box)

    @staticmethod
    def feed_list_widget(feeds):
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

        scroll = Gtk.ScrolledWindow()
        scroll.add(view)
        return scroll

    @staticmethod
    def stories_widget():
        store = Gtk.ListStore(str)
        view = Gtk.TreeView(store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Title", renderer, text=0)
        view.append_column(column)
        return view


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
