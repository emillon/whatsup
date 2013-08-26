#!/usr/bin/python3

import requests
import netrc


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
        print(r.request.headers)
        print(r.headers)
        d = r.json()
        assert(d['authenticated'])
        return d


def main():
    n = netrc.netrc()
    username, _, password = n.authenticators('newsblur.com')
    c = NewsblurClient('http://api.newsblur.com')
    c.login(username, password)
    print(c.feeds())


if __name__ == '__main__':
    main()
