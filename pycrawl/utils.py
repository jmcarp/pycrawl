import asyncio
import functools


def extend(*dicts):
    ret = {}
    for each in dicts:
        ret.update(each)
    return ret


class agnosticmethod:

    def __init__(self, method):
        self.method = method
        self.partials = {}

    def __get__(self, instance, owner):
        this = instance if instance else owner
        key = id(this)
        if key not in self.partials:
            self.partials[key] = functools.partial(self.method, this)
        return self.partials[key]


class Queue(asyncio.JoinableQueue, asyncio.PriorityQueue):
    pass
