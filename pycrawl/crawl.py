import re
import abc
import asyncio
import contextlib
import urllib.parse as urlparse

import aiohttp
import pyquery

from pycrawl.utils import Queue

from pycrawl.http import Request
from pycrawl.http import Response
from pycrawl.middleware import CrawlerMiddlewareManager


class Spider(metaclass=abc.ABCMeta):

    def __init__(self, middlewares=None, loop=None, **config):
        self.config = config
        self._context = {}
        self._loop = loop or asyncio.get_event_loop()
        self._connector = aiohttp.TCPConnector(loop=self._loop)
        self._middlewares = CrawlerMiddlewareManager(self, middlewares)

    def enqueue_request(self, **kwargs):
        context = self._context[self.task]
        max_depth = self.config.get('max_depth')
        if max_depth and context['request'].depth > max_depth:
            return
        request = Request(referer=context['response'], **kwargs)
        if request.url in self._seen:
            return
        if not self._url_allowed(request):
            return
        request.depth = context['response'].request.depth + 1
        self._queue.put_nowait(request)

    def _url_allowed(self, request):
        return next(
            (
                True for domain in self.config['domains']
                if request.furl.host.endswith(domain)
            ),
            False,
        )

    @asyncio.coroutine
    def start(self):
        self._seen = set()
        self._queue = Queue(loop=self._loop)
        for url in self.config['urls']:
            self._queue.put_nowait(Request(url))
        workers = [asyncio.Task(self._work()) for _ in range(self.config['concurrency'])]
        yield from self._queue.join()
        for worker in workers:
            worker.cancel()

    @asyncio.coroutine
    def _work(self):
        while True:
            request = yield from self._queue.get()
            yield from self._fetch(request)
            self._queue.task_done()

    @asyncio.coroutine
    def _fetch(self, request):
        for callback in self._middlewares['before_request']:
            request = callback(request)
        resp = yield from aiohttp.request('GET', request.url, loop=self._loop)
        body = yield from resp.read_and_close()
        response = Response(request, resp, body)
        for callback in self._middlewares['after_response']:
            response = callback(response)
        with self._request_context(self._loop, request, response):
            self.parse(response)

    @property
    def _task(self):
        return asyncio.get_current_task(loop=self._loop)

    @contextlib.contextmanager
    def _request_context(self, request, response):
        self._context[self.task] = {'request': request, 'response': response}
        try:
            yield
        finally:
            del self._context[self.task]

    @abc.abstractmethod
    def parse(self, response):
        pass


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
            self._routes.append(Route(callback, pattern))
            return callback
        return wrapper

    def parse(self, response):
        route = response.request.meta.get('route')
        if route:
            route.callback(self, response)
        parsed = pyquery.PyQuery(response.content)
        elms = parsed('a[href]')
        hrefs = elms.map(lambda: urlparse.urljoin(response.request.url, pyquery.PyQuery(this).attr('href')))
        for route in self._routes:
            for url in route.filter_urls(hrefs):
                self.enqueue_request(url=url, route=route)
