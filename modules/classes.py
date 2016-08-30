# -*- coding: utf-8 -*-

from math import ceil


class pager(object):

    @property
    def pages(self):
        return int(ceil(self.count / float(self.limit)))

    @property
    def prefix(self):
        return (self.page - 1) * self.limit

    @property
    def suffix(self):
        return self.prefix + self.limit

    @property
    def previous(self):
        if self.page > 1:
            return self.page - 1
        return 1

    @property
    def first(self):
        return ((self.page - 1) * self.limit) + 1

    @property
    def last(self):
        return min(self.first + self.limit - 1, self.count)

    @property
    def next(self):
        if self.page < self.pages:
            return self.page + 1
        return self.pages

    def __init__(self, count, limit, page):
        self.count = count
        self.limit = limit
        self.page = page
        if self.page > self.pages:
            self.page = self.pages

    def get_pages(self, pages):
        start = max(self.page - pages, 1)
        stop = min(self.page + pages, self.pages)
        return range(start, stop + 1)
