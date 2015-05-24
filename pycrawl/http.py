import copy

import furl
from pyquery import PyQuery


class Request:

    def __init__(self, url, depth=0, priority=0, referer=None, **meta):
        self.url = url
        self.depth = depth
        self.priority = priority
        self.referer = referer
        self.meta = meta

    @property
    def furl(self):
        return furl.furl(self.url)

    @property
    def _comparand(self):
        return (self.priority, self.depth)

    def __lt__(self, other):
        return self._comparand < other._comparand

    def truncate(self):
        ret = copy.copy(self)
        ret.referer = None
        return ret


class Response:

    def __init__(self, request, response, content):
        self.request = request
        self.response = response
        self.content = content
        self.parsed = PyQuery(content)

    def truncate(self):
        return self.__class__(self.request.truncate(), self.response, self.content)
