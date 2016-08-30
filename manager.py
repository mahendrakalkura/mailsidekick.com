# -*- coding: utf-8 -*-

from contextlib import closing
from datetime import datetime
from flask import g
from flask.ext.script import Command, Manager
from logging import getLogger
from time import sleep
from traceback import print_exc
from webassets.script import CommandLineEnvironment

import modules.crontab
import modules.database
import modules.decorators
import modules.log
import modules.mail
import modules.models
import modules.utilities

import server
import settings


def handle(self, application, *args, **kwargs):
    result = None
    with application.app_context():
        context = application.test_request_context()
        context.push()
        application.preprocess_request()
        try:
            result = self.run(*args, **kwargs)
        except:
            print_exc()
        application.process_response(application.response_class())
        context.pop()
    return result

Command.handle = handle

manager = Manager(server.application, with_default_commands=False)


@manager.command
@modules.decorators.profile(0)
def assets():
    CommandLineEnvironment(server.assets, getLogger('flask')).build()


@manager.command
def crontab_accounts():
    modules.crontab.accounts()


@manager.command
def crontab_codes():
    modules.crontab.codes()


@manager.command
def crontab_credits():
    modules.crontab.credits()


@manager.command
def crontab_filters():
    modules.crontab.filters()


@manager.command
def crontab_incoming():
    modules.crontab.incoming()
    if not settings.is_mahendra():
        sleep(60)


@manager.command
def crontab_outgoing_1():
    modules.crontab.outgoing([
        'Premium+',
        'Premium',
        'Advanced+',
        'Advanced',
        'Starter+',
        'Starter',
        'Pay-As-You-Go',
    ])
    if not settings.is_mahendra():
        sleep(60)


@manager.command
def crontab_outgoing_2():
    modules.crontab.outgoing(['Free'])
    if not settings.is_mahendra():
        sleep(60)


@manager.command
def crontab_proxies():
    modules.crontab.proxies()


@manager.command
def crontab_templates():
    modules.crontab.templates()


@manager.command
def crontab_test():
    modules.crontab.test()


@manager.command
@modules.decorators.profile(0)
def database_populate():
    with closing(
        modules.database.engine.connect()
    ) as connection:
        for table in reversed(
            modules.database.base.metadata.sorted_tables
        ):
            if table.name.startswith('wp_'):
                continue
            connection.execute(table.delete())
            connection.execute('ALTER TABLE %(table)s AUTO_INCREMENT = 1' % {
                'table': table,
            })

    for item in [
        {
            'email': 'mahendrakalkura@gmail.com',
            'name': 'Mahendra Kalkura',
            'password': 'password',
        },
        {
            'email': 'ncroan@gmail.com',
            'name': 'Norman Croan',
            'password': 'password',
        },
    ]:
        administrator = modules.models.administrator(**{
            'email': item['email'],
            'name': item['name'],
        })
        administrator.set_password_from_string(item['password'])
        g.mysql.add(administrator)
        g.mysql.commit()

    for item in [
        {
            'contents': '<p>...coming soon...</p>',
            'timestamp': datetime(
                year=2013, month=8, day=11, hour=10, minute=0, second=0
            ),
            'title': 'News #1',
            'type': 'success',
        },
        {
            'contents': '<p>...coming soon...</p>',
            'timestamp': datetime(
                year=2013, month=8, day=12, hour=10, minute=0, second=0
            ),
            'title': 'News #2',
            'type': 'error',
        },
        {
            'contents': '<p>...coming soon...</p>',
            'timestamp': datetime(
                year=2013, month=8, day=13, hour=10, minute=0, second=0
            ),
            'title': 'News #3',
            'type': 'info',
        },
    ]:
        g.mysql.add(modules.models.article(**item))
        g.mysql.commit()


@manager.command
@modules.decorators.profile(0)
def schedule():
    for filter in g.mysql.query(
        modules.models.filter
    ).order_by(
        'id asc'
    ).all():
        if not filter.schedule:
            filter.schedule = modules.models.filter.__table__.schedule.copy()
        g.mysql.add(filter)
        g.mysql.commit()

if __name__ == '__main__':
    manager.run()
