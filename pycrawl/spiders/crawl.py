import re
import urllib.parse as urlparse

from pyquery import PyQuery

from pycrawl.spiders.core import Spider


class Route:

    def __init__(self, pattern, callback):
        self.pattern = re.compile(pattern)
        self.callback = callback

    def filter_urls(self, urls):
        return (url for url in urls if self.pattern.search(url))


class RouteSpider(Spider):

    def __init__(self, middlewares=None, routes=None, **config):
        super().__init__(middlewares=middlewares, **config)
        self._routes = routes or []

    def route(self, pattern):
        def wrapper(callback):
            self._routes.append(Route(pattern, callback))
            return callback
        return wrapper

    def parse(self, response):
        route = response.request.meta.get('route')
        if route:
            route.callback(self, response)
        elms = response.parsed('a[href]')
        hrefs = elms.map(lambda: urlparse.urljoin(response.request.url, PyQuery(this).attr('href')))
        for route in self._routes:
            for url in route.filter_urls(hrefs):
                self.enqueue_request(url=url, route=route)
