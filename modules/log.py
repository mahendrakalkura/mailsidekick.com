# -*- coding: utf-8 -*-

from logging import DEBUG, Formatter, StreamHandler, getLogger
from types import NoneType

formatter = Formatter('%(asctime)s [%(levelname)8s] %(message)s')

stream_handler = StreamHandler()
stream_handler.setLevel(DEBUG)
stream_handler.setFormatter(formatter)

logger = getLogger('root')
logger.setLevel(DEBUG)
logger.addHandler(stream_handler)


def pprint(level, string, indent):
    if isinstance(string, dict):
        keys = sorted(string.keys())
        if keys:
            for key in keys:
                value = string[key]
                if is_leaf(value):
                    write(level, '%(key)s: %(value)s' % {
                        'key': unicode(key),
                        'value': unicode(value),
                    }, indent)
                else:
                    write(level, unicode(key), indent)
                    pprint(level, value, indent + 1)
        else:
            write(level, '{}', indent)
    elif isinstance(string, tuple):
        if string:
            write(level, unicode(string), indent)
        else:
            write(level, '()', indent)
    elif isinstance(string, set):
        if string:
            string = sorted(string)
            for item in string:
                pprint(level, item, indent)
        else:
            write(level, '[]', indent)
    elif isinstance(string, list):
        if string:
            string = sorted(string)
            for item in string:
                pprint(level, item, indent)
        else:
            write(level, '[]', indent)
    else:
        write(level, unicode(string), indent)


def write(level, message, indent):
    if isinstance(message, basestring):
        message = message.rstrip()
    logger.log(level, '%(spacer)s%(message)s' % {
        'spacer': ' ' * 4 * indent,
        'message': message,
    })


def is_leaf(string):
    if isinstance(string, basestring):
        return True
    if isinstance(string, complex):
        return True
    if isinstance(string, float):
        return True
    if isinstance(string, int):
        return True
    if isinstance(string, long):
        return True
    if isinstance(string, NoneType):
        return True
