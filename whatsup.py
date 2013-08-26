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
                       }
             }
        return d


class WhatsupWindow(Gtk.Window):

    def __init__(self, client):
        super().__init__()
        self.client = client

        store = Gtk.ListStore(str)
        d = client.feeds()
        for _, f in d['feeds'].items():
            row = [f['feed_title']]
            store.append(row)

        view = Gtk.TreeView(store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Feed", renderer, text=0)
        view.append_column(column)

        self.add(view)


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
    if args.debug:
        from pprint import pprint
        pprint(d)
    win = WhatsupWindow(c)
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
