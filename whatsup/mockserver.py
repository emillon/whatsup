import httpretty
import json


class MockServer:
    def __init__(self, api_root):
        self.api_root = api_root
        self._routes = [(httpretty.POST, '/api/login', self.post_login),
                        (httpretty.GET, '/reader/feeds', self.get_feeds),
                        (httpretty.GET, '/reader/river_stories',
                            self.get_river),
                        ]
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

    def post_login(self, meth, uri, headers):
        return (200, headers, '')

    def get_feeds(self, meth, uri, headers):
        r = {'authenticated': True,
             'feeds': {k: {'feed_title': v['feed_title'],
                           'nt': len(v['stories'])
                           }
                       for k, v in self._feeds.items()
                       }
             }
        return (200, headers, json.dumps(r))

    def get_river(self, meth, uri, headers):
        def fix_story(s, k):
            r = s.copy()
            r['story_feed_id'] = k
            r['story_content'] = 'Content of ' + r['story_title']
            return r
        stories = [fix_story(s, k)
                   for k, v in self._feeds.items()
                   for s in v['stories']]
        # FIXME 'feeds' query string parameter is ignored
        r = {'stories': stories}
        return (200, headers, json.dumps(r))

    def enable(self):
        httpretty.enable()
        for meth, route, cb in self._routes:
            httpretty.register_uri(meth, self.api_root + route, cb)

    def disable(self):
        httpretty.disable()
