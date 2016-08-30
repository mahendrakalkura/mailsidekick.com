# -*- coding: utf-8 -*-

from bcrypt import gensalt, hashpw
from boto.s3.connection import S3Connection
from flask import request, session
from HTMLParser import HTMLParser
from locale import LC_ALL, format, setlocale
from random import choice
from simplejson import dumps
from string import ascii_lowercase, digits

import settings

setlocale(LC_ALL, 'en_US.UTF-8')


def get_alphabets(number):
    return ''.join(choice(ascii_lowercase) for _ in range(number))


def get_numbers(number):
    return ''.join(choice(digits) for _ in range(number))


def get_class(class_):
    classes = {
        'csv': 'file-txt',
        'doc': 'file-txt',
        'docx': 'file-txt',
        'gif': 'file-txt',
        'jpg': 'file-txt',
        'pdf': 'file-txt',
        'png': 'file-txt',
        'txt': 'file-txt',
        'xls': 'file-txt',
        'xlsx': 'file-txt',
    }
    try:
        return classes[class_.lower()]
    except:
        pass
    return 'file'


def get_date(value):
    return value.strftime('%e %B, %Y')


def get_date_and_time(value):
    return value.strftime('%l:%M %p On %e %B, %Y')


def get_dumps(value):
    return dumps(value)


def get_filtered_list(list):
    return sorted(set(filter(len, map(lambda item: item.strip(), list))))


def get_filters_order_by_limit_page(table, filters, order_by, limit, page):
    if not table in session:
        session[table] = {}
    if 'filters' in session[table]:
        filters = session[table]['filters']
    if 'order_by' in session[table]:
        order_by = session[table]['order_by']
    if 'limit' in session[table]:
        limit = session[table]['limit']
    if 'page' in session[table]:
        page = session[table]['page']
    return filters, order_by, limit, page


def get_float(value):
    return format('%.2f', value, grouping=True)


def get_greetings(datetime):
    if datetime.hour < 12:
        return 'morning'
    if datetime.hour < 18:
        return 'afternoon'
    return 'evening'


def get_integer(value):
    return format('%d', value, grouping=True)


def get_password(password):
    return hashpw(password, gensalt(10))


def get_s3():
    return S3Connection(
        settings.S3_ACCESS_KEY, settings.S3_SECRET_KEY
    ).get_bucket(settings.S3_BUCKET, validate=False)


def get_tuples(items, empty):
    tuples = []
    if empty:
        tuples.append(empty)
    for item in items:
        tuples.append((item, item))
    return tuples


def get_unescaped_string(string):
    return HTMLParser().unescape(string)


def set_filters(table, form):
    if not table in session:
        session[table] = {}
    if request.form.get('submit', default='') == 'set':
        session[table]['filters'] = form(request.form).data
        session[table]['page'] = 1
    if request.form.get('submit', default='') == 'unset':
        session[table]['filters'] = {}
        session[table]['page'] = 1


def set_order_by_limit_page(table):
    if not table in session:
        session[table] = {}
    if(
        'order_by_column' in request.args
        and
        'order_by_direction' in request.args
    ):
        session[table]['order_by'] = {
            'column': request.args['order_by_column'],
            'direction': request.args['order_by_direction'],
        }
    if 'limit' in request.args:
        session[table]['limit'] = int(request.args['limit'] or 0)
    if 'page' in request.args:
        session[table]['page'] = int(request.args['page'] or 0)
