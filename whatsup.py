#!/usr/bin/python3

import argparse
import requests
import netrc

from gi.repository import Gtk


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
        l = [s for s in self._cache['stories'] if s['story_feed_id'] == feed]
        return {'stories': l}


class MockClient:
    """
    A client that is compatible with NewsblurClient, but
    does not connect to the Internet.
    """

    def __init__(self):
        self._feeds = {'1': {'feed_title': 'Feed 1',
                             'stories': [{'story_title': 'Feed 1 S1'},
                                         {'story_title': 'Feed 1 S2'},
                                         ]
                             },
                       '2': {'feed_title': 'Feed 2',
                             'stories': [{'story_title': 'Feed 1 S1'},
                                         ]
                             },
                       '3': {'feed_title': 'Feed 3',
                             'stories': []
                             },
                       '4': {'feed_title': 'Feed 4',
                             'stories': [{'story_title': 'Feed 4 S1'},
                                         {'story_title': 'Feed 4 S2'},
                                         ]
                             },
                       }

    def feeds(self):
        return {'feeds': {k: {'feed_title': v['feed_title'],
                              'nt': len(v['stories'])
                              }
                          for k, v in self._feeds.items()
                          }
                }

    def river(self, feeds):
        stories = [s
                   for k, v in self._feeds.items()
                   if k in feeds
                   for s in v['stories']]
        return {'stories': stories}

    def cache_river(self, feeds):
        pass

    def all_stories(self):
        stories = [s
                   for k, v in self._feeds.items()
                   for s in v['stories']]
        return {'stories': stories}

    def stories(self, feed):
        return self.river([feed])


class FeedListWidget(Gtk.ScrolledWindow):
    def __init__(self, feeds):
        super().__init__()
        store = Gtk.ListStore(str, str, int)
        total_unread = sum([f['nt'] for f in feeds.values()])
        store.append(['<all>', 'All', total_unread])
        for k, f in feeds.items():
            title = f['feed_title']
            unread = f['nt']
            if unread == 0:
                continue
            row = [k, title, unread]
            store.append(row)

        view = Gtk.TreeView(store)
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Feed", renderer, text=1)
        view.append_column(column)
        column = Gtk.TreeViewColumn("Unread", renderer, text=2)
        view.append_column(column)

        self.tree_view = view
        self.add(view)


class StoriesListWidget(Gtk.TreeView):
    def __init__(self, client):
        store = Gtk.ListStore(str)
        super().__init__(store)
        self.store = store
        self.client = client
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Title", renderer, text=0)
        self.append_column(column)

    def on_feed_select_changed(self, selection):
        model, treeiter = selection.get_selected()
        row = model[treeiter]
        feed_id = row[0]
        stories = {'stories': []}
        if feed_id == '<all>':
            stories = self.client.all_stories()
        else:
            stories = self.client.stories(feed_id)
        self.store.clear()
        for story in stories['stories']:
            text = story['story_title']
            self.store.append([text])


class WhatsupWindow(Gtk.Window):

    def __init__(self, client):
        super().__init__()
        self.client = client

        box = Gtk.Box()

        d = client.feeds()
        wfeeds = FeedListWidget(d['feeds'])
        box.pack_start(wfeeds, True, True, 0)
        wstories = StoriesListWidget(client)
        box.pack_start(wstories, True, True, 0)

        select = wfeeds.tree_view.get_selection()
        select.connect('changed', wstories.on_feed_select_changed)

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
    river = c.cache_river(feeds_unread)
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
