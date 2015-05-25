import abc
import asyncio
import contextlib

import aiohttp
from flask.config import Config
from flask.helpers import get_root_path

from pycrawl.utils import Queue

from pycrawl.http import Request
from pycrawl.http import Response
from pycrawl.middleware import SpiderMiddlewareManager


default_config = {
    'CONCURRENCY': 5,
    'MAX_DEPTH': None,
    'MAX_RETRIES': 5,
}


class Spider(metaclass=abc.ABCMeta):

    def __init__(self, import_name, middlewares=None, loop=None, session=None):
        self.import_name = import_name
        self.root_path = get_root_path(import_name)
        self.config = Config(self.root_path, default_config)

        self._context = {}
        self._loop = loop or asyncio.get_event_loop()
        self._middlewares = SpiderMiddlewareManager(self, middlewares)
        self._session = session or aiohttp.ClientSession(loop=self._loop)

    def enqueue_request(self, **kwargs):
        context = self._context[self._task]
        max_depth = self.config.get('MAX_DEPTH')
        if max_depth and context['request'].depth > max_depth:
            return
        request = Request(referer=context['response'], **kwargs)
        if request.url in self._seen:
            return
        if not self._url_allowed(request):
            return
        request.depth = context['response'].request.depth + 1
        self._queue.put_nowait(request)

    def run(self):
        self._loop.run_until_complete(self.start())

    @asyncio.coroutine
    def start(self):
        self._seen = set()
        self._queue = Queue(loop=self._loop)
        for url in self.config['URLS']:
            self._queue.put_nowait(Request(url))
        workers = [asyncio.Task(self._work()) for _ in range(self.config['CONCURRENCY'])]
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
            request = callback(self, request)
        resp = yield from self._session.request('get', **request.params)
        body = yield from resp.read_and_close()
        response = Response(request, resp, body)
        for callback in self._middlewares['after_response']:
            response = callback(self, response)
        with self._request_context(request, response):
            self.parse(response)

    @property
    def _task(self):
        return asyncio.Task.current_task(loop=self._loop)

    @contextlib.contextmanager
    def _request_context(self, request, response):
        self._context[self._task] = {'request': request, 'response': response}
        try:
            yield
        finally:
            del self._context[self._task]

    def _url_allowed(self, request):
        return next(
            (
                True for domain in self.config['DOMAINS']
                if request.furl.host.endswith(domain)
            ),
            False,
        )

    @abc.abstractmethod
    def parse(self, response):
        pass
