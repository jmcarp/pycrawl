import copy
import collections

from pycrawl.utils import extend
from pycrawl.utils import agnosticmethod


class MiddlewareManager:

    _middlewares = collections.defaultdict(list)

    def __init__(self, target, middlewares):
        middlewares = extend(self.clone(), middlewares or {})
        self._middlewares = collections.defaultdict(list, middlewares)
        self.augment(target)

    def __getitem__(self, key):
        return self._middlewares[key]

    def __setitem__(self, key, value):
        self._middlewares[key] = value

    @classmethod
    def clone(cls):
        return {
            key: copy.copy(value)
            for key, value in cls._middlewares.items()
        }

    def augment(self, target):
        target.callback = self.callback
        target.middleware = self.middleware

    @agnosticmethod
    def callback(this, label):
        def wrapper(target):
            this._add_callback(label, target)
            return target
        return wrapper

    @agnosticmethod
    def middleware(this, target):
        for label, target in target.__dict__.items():
            this._add_callback(label, target)
        return target

    @agnosticmethod
    def _add_callback(this, label, target):
        this._middlewares[label].append(target)


class SpiderMiddlewareManager(MiddlewareManager):
    pass


@SpiderMiddlewareManager.callback('after_error')
def retry_errors(spider, request, error):
    pass
