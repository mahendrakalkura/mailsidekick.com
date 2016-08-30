# -*- coding: utf-8 -*-

from collections import defaultdict
from time import time

instances = defaultdict(lambda: defaultdict())


def start(key):
    instances[key]['start'] = time()


def stop(key):
    instances[key]['stop'] = time()


def get_seconds(key):
    return float(instances[key]['stop'] - instances[key]['start'])
