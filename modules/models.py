# -*- coding: utf-8 -*-

from bcrypt import hashpw
from csv import QUOTE_ALL, DictReader
from datetime import datetime, timedelta
from flask import g, request
from hashlib import md5
from os import listdir, makedirs, remove
from os.path import dirname, getsize, isdir, isfile, join, splitext
from pytz import timezone
from random import choice, randint
from re import compile, findall, IGNORECASE, match
from requesocks import get
from requests.auth import HTTPProxyAuth
from shutil import copy2, rmtree
from signal import alarm, SIGALRM, signal
from simplejson import dumps, loads
from sqlalchemy import Column
from sqlalchemy.event import listen
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.orm import backref, mapper, relationship
from sqlalchemy.sql import func
from sqlalchemy.types import TEXT, TypeDecorator
from werkzeug import secure_filename

import modules.database
import modules.system
import modules.utilities

import vendors.socks

import settings


class Timeout(Exception):

    def __str__(self):
        return 'Timeout'


def handler(signal_number, frame):
    raise Timeout()


class mutators_dict(Mutable, dict):

    @classmethod
    def coerce(class_, key, value):
        if not isinstance(value, mutators_dict):
            if isinstance(value, dict):
                return mutators_dict(value)
            return Mutable.coerce(key, value)
        return value

    def __delitem__(self, key):
        dict.__delitem__(self, key)
        self.changed()

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)
        self.changed()


class mutators_list(Mutable, list):

    @classmethod
    def coerce(class_, key, value):
        if not isinstance(value, mutators_list):
            if isinstance(value, list):
                return mutators_list(value)
            return Mutable.coerce(key, value)
        return value

    def append(self, value):
        list.append(self, value)
        self.changed()

    def __add__(self, value):
        list.__add__(self, value)
        self.changed()

    def __delitem__(self, index):
        list.__delitem__(self, index)
        self.changed()

    def __setitem__(self, key, value):
        list.__setitem__(self, key, value)
        self.changed()


class json(TypeDecorator):
    impl = TEXT

    def process_bind_param(self, value, dialect):
        return dumps(value)

    def process_result_value(self, value, dialect):
        return loads(value)


class administrator(modules.database.base):
    __tablename__ = 'administrators'
    __table_args__ = {
        'autoload': True,
    }

    def before_insert(self):
        if not self.status or not self.status in self.__table__.choices[
            'status'
        ]:
            self.status = self.__table__.choices['status'][0]

    def set_password_from_string(self, string):
        if string:
            self.password = modules.utilities.get_password(string)

    def toggle_status(self):
        self.status = 'Off' if self.status == 'On' else 'On'
        g.mysql.add(self)
        g.mysql.commit()

    def is_valid(self, password_name):
        return hashpw(
            password_name.encode('utf-8'), self.password.encode('utf-8')
        ) == self.password.encode('utf-8')

administrator.__table__.choices = {
    'status': [
        'On',
        'Off',
    ],
}


class group(modules.database.base):
    __tablename__ = 'groups'
    __table_args__ = {
        'autoload': True,
    }

    def get_blacklist(self):
        return modules.utilities.get_filtered_list(self.blacklist.split('\n'))


class proxy(modules.database.base):
    __tablename__ = 'proxies'
    __table_args__ = {
        'autoload': True,
    }

    def before_insert(self):
        if not self.status or not self.status in self.__table__.choices[
            'status'
        ]:
            self.status = self.__table__.choices['status'][2]

    def update_status(self):
        self.status = 'Off'
        try:
            response = get(
                'http://mailsidekick.com/remote_addr.php',
                auth=self.get_auth(),
                proxies=self.get_proxies(),
                timeout=30,
                verify=False,
            )
            if (
                response
                and
                response.status_code == 200
                and
                response.text
                and
                len(response.text) >= 7
                and
                not '70.38.60.172' in response.text
            ):
                self.status = 'On'
        except Exception, exception:
            self.status = str(exception)
        g.mysql.add(self)
        g.mysql.commit()

    def get_auth(self):
        if self.username and self.password:
            return HTTPProxyAuth(self.username, self.password)

    def get_proxies(self):
        value = '%(hostname)s:%(port_number)s'
        if self.protocol in ['socks4', 'socks5']:
            value = '%(protocol)s://%(hostname)s:%(port_number)s'
        value = value % {
            'hostname': self.hostname,
            'port_number': self.port_number,
            'protocol': self.protocol,
        }
        return {
            'http': value,
            'https': value,
        }

    def get_protocol(self):
        for protocol in proxy.__table__.choices['protocol']:
            if self.protocol == protocol[0]:
                return protocol[1]
        return proxy.__table__.choices['protocol'][0][1]

proxy.__table__.choices = {
    'protocol': [
        ('1', 'Socks 4'),
        ('2', 'Socks 5'),
        ('3', 'HTTPS'),
        ('4', 'HTTP'),
    ],
    'status': [
        'On',
        'Off',
        'May Be',
    ],
}


class account(modules.database.base):
    __tablename__ = 'accounts'
    __table_args__ = {
        'autoload': True,
    }

    connections = Column(mutators_dict.as_mutable(json))

    group = relationship(
        'group',
        backref=backref(
            'accounts',
            cascade='all',
            lazy='dynamic'
        )
    )

    proxy = relationship(
        'proxy',
        backref=backref(
            'accounts',
            lazy='dynamic'
        )
    )

    @staticmethod
    def csv(user, stream):
        count = 0
        for row in DictReader(
            stream,
            delimiter=',',
            doublequote=True,
            lineterminator='\n',
            quotechar='"',
            quoting=QUOTE_ALL,
            skipinitialspace=True
        ):
            try:
                g.mysql.add(account(**{
                    'description': row['Description'],
                    'incoming_hostname': row['Incoming Hostname'],
                    'incoming_port_number': row['Incoming Port Number'],
                    'incoming_use_ssl': row['Incoming Use SSL'],
                    'outgoing_hostname': row['Outgoing Hostname'],
                    'outgoing_port_number': row['Outgoing Port Number'],
                    'outgoing_use_ssl': row['Outgoing Use SSL'],
                    'outgoing_use_tls': row['Outgoing Use TLS'],
                    'password': row['Password'],
                    'user': user,
                    'username': row['Username'],
                }))
                try:
                    g.mysql.commit()
                    count += 1
                except:
                    g.mysql.rollback()
            except:
                pass
        return count

    def __init__(self, *args, **kwargs):
        self.description = ''
        self.incoming_hostname = ''
        self.incoming_port_number = ''
        self.incoming_use_ssl = 'No'
        self.outgoing_hostname = ''
        self.outgoing_port_number = ''
        self.outgoing_use_ssl = 'No'
        self.outgoing_use_tls = 'No'
        self.username = ''
        self.password = ''
        self.connections = {
            'incoming': '',
            'outgoing': '',
        }
        super(account, self).__init__(*args, **kwargs)

    def before_insert(self):
        if not self.blacklist:
            self.blacklist = ''
        if not self.status or not self.status in self.__table__.choices[
            'status'
        ]:
            self.status = self.__table__.choices['status'][0]

    def toggle_status(self):
        self.status = 'Off' if self.status == 'On' else 'On'
        g.mysql.add(self)
        g.mysql.commit()

    def update_connections(self):
        self.connections['incoming'] = ''
        connection = self.get_incoming()
        if connection:
            self.connections['incoming'] = 'On'
            try:
                connection.quit()
            except:
                try:
                    connection.close()
                    connection.logout()
                except:
                    pass
        self.connections['outgoing'] = ''
        connection = self.get_outgoing()
        if connection:
            self.connections['outgoing'] = 'On'
            try:
                connection.quit()
            except:
                pass
        g.mysql.add(self)
        g.mysql.commit()

    def get_blacklist(self):
        return modules.utilities.get_filtered_list(self.blacklist.split('\n'))

    def get_dictionary(self):
        dictionary = self.to_dictionary()
        dictionary['incoming_use_ssl'] = True if dictionary[
            'incoming_use_ssl'
        ] == 'Yes' else False
        dictionary['outgoing_use_ssl'] = True if dictionary[
            'outgoing_use_ssl'
        ] == 'Yes' else False
        dictionary['outgoing_use_tls'] = True if dictionary[
            'outgoing_use_tls'
        ] == 'Yes' else False
        return dictionary

    def get_incoming(self):
        import imaplib
        import poplib
        if self.proxy:
            vendors.socks.setdefaultproxy(
                int(self.proxy.protocol),
                self.proxy.hostname,
                int(self.proxy.port_number),
                True,
                self.proxy.username if self.proxy.username else None,
                self.proxy.password if self.proxy.password else None
            )
            vendors.socks.wrapmodule(poplib)
            vendors.socks.wrapmodule(imaplib)
        try:
            signal(SIGALRM, handler)
            alarm(30)
            if self.incoming_hostname == 'pop3.live.com':
                connection = poplib.POP3_SSL(
                    self.incoming_hostname, int(self.incoming_port_number)
                ) if self.incoming_use_ssl == 'Yes' else poplib.POP3(
                    self.incoming_hostname, int(self.incoming_port_number)
                )
                connection.user(self.username)
                connection.pass_(self.password)
                return connection
            connection = imaplib.IMAP4_SSL(
                self.incoming_hostname, int(self.incoming_port_number)
            ) if self.incoming_use_ssl == 'Yes' else imaplib.IMAP4(
                self.incoming_hostname, int(self.incoming_port_number)
            )
            connection.login(self.username, self.password)
            alarm(0)
        except Timeout, exception:
            connection = None
            self.connections['incoming'] = str(exception)
        except Exception, exception:
            connection = None
            self.connections['incoming'] = str(exception)
            alarm(0)
        finally:
            alarm(0)
        return connection

    def get_name(self):
        return self.username.split('@')[0]

    def get_queues(self):
        return g.mysql.query(
            queue
        ).join(
            log
        ).filter(
            queue.status == 'Scheduled',
            log.account == self,
            log.id == queue.log_id
        ).count()

    def get_outgoing(self):
        import smtplib
        if self.proxy:
            vendors.socks.setdefaultproxy(
                int(self.proxy.protocol),
                self.proxy.hostname,
                int(self.proxy.port_number),
                True,
                self.proxy.username if self.proxy.username else None,
                self.proxy.password if self.proxy.password else None
            )
            vendors.socks.wrapmodule(smtplib)
        try:
            signal(SIGALRM, handler)
            alarm(30)
            connection = smtplib.SMTP_SSL(
                self.outgoing_hostname, int(self.outgoing_port_number)
            ) if self.outgoing_use_ssl == 'Yes' else smtplib.SMTP(
                self.outgoing_hostname, int(self.outgoing_port_number)
            )
            if self.outgoing_use_tls == 'Yes':
                connection.ehlo()
                connection.starttls()
                connection.ehlo()
            connection.login(self.username, self.password)
            alarm(0)
        except Timeout, exception:
            connection = None
            self.connections['outgoing'] = str(exception)
        except Exception, exception:
            connection = None
            self.connections['outgoing'] = str(exception)
            alarm(0)
        finally:
            alarm(0)
        return connection

account.__table__.choices = {
    'status': [
        'On',
        'Off',
    ],
    'incoming_use_ssl': [
        'Yes',
        'No',
    ],
    'outgoing_use_ssl': [
        'Yes',
        'No',
    ],
    'outgoing_use_tls': [
        'Yes',
        'No',
    ],
}

account.__table__.headers = [
    ('Description', [], ),
    ('Incoming Hostname', [], ),
    ('Incoming Port Number', ['must be a number'], ),
    ('Incoming Use SSL', ['must be either Yes or No', 'is case-sensitive'], ),
    ('Outgoing Hostname', [], ),
    ('Outgoing Port Number', ['must be a number'], ),
    ('Outgoing Use SSL', ['must be either Yes or No', 'is case-sensitive'], ),
    ('Outgoing Use TLS', ['must be either Yes or No', 'is case-sensitive'], ),
    ('Username', [], ),
    ('Password', [], ),
]


class article(modules.database.base):
    __tablename__ = 'articles'
    __table_args__ = {
        'autoload': True,
    }

    def before_insert(self):
        if not self.timestamp:
            self.timestamp = datetime.now()
        if not self.status or not self.status in self.__table__.choices[
            'status'
        ]:
            self.status = self.__table__.choices['status'][0]
        if not self.sticky or not self.sticky in self.__table__.choices[
            'sticky'
        ]:
            self.sticky = self.__table__.choices['sticky'][0]
        keys = [type[0] for type in self.__table__.choices['type']]
        if not self.type or not self.type in keys:
            self.type = keys[0]

    def before_update(self):
        if not self.timestamp:
            self.timestamp = datetime.now()

    def toggle_sticky(self):
        self.sticky = 'No' if self.sticky == 'Yes' else 'Yes'
        g.mysql.add(self)
        g.mysql.commit()

    def toggle_status(self):
        self.status = 'Off' if self.status == 'On' else 'On'
        g.mysql.add(self)
        g.mysql.commit()

    def get_prefix(self):
        if self.sticky == 'Yes':
            return 'Sticky:'
        return ''

    def get_type(self):
        for type in article.__table__.choices['type']:
            if self.type == type[0]:
                return type[1]
        return article.__table__.choices['type'][0][1]

article.__table__.choices = {
    'type': [
        ('success', 'Success'),
        ('error', 'Failure'),
        ('info', 'Information'),
    ],
    'status': [
        'On',
        'Off',
    ],
    'sticky': [
        'No',
        'Yes',
    ],
}


class pack(modules.database.base):
    __tablename__ = 'packs'
    __table_args__ = {
        'autoload': True,
    }


class filter(modules.database.base):
    __tablename__ = 'filters'
    __table_args__ = {
        'autoload': True,
    }

    schedule = Column(mutators_dict.as_mutable(json))
    conditions = Column(mutators_list.as_mutable(json))
    steps = Column(mutators_list.as_mutable(json))

    pack = relationship(
        'pack',
        backref=backref(
            'filters',
            cascade='all',
            lazy='dynamic'
        )
    )

    accounts = relationship(
        'account',
        backref=backref(
            'filters',
            lazy='dynamic',
        ),
        lazy='dynamic',
        secondary='filters_accounts'
    )

    def __init__(self, *args, **kwargs):
        self.schedule = self.__table__.schedule.copy()
        self.conditions = []
        self.steps = []
        super(filter, self).__init__(*args, **kwargs)

    def before_insert(self):
        if not self.status or not self.status in self.__table__.choices[
            'status'
        ]:
            self.status = self.__table__.choices['status'][0]
        if not self.position:
            self.position = g.mysql.query('position').from_statement(
                '''
                SELECT COALESCE(MAX(position), 0) + 1 AS position
                FROM filters
                '''
            ).one()[0]

    def toggle_position(self, direction):
        if direction == 'up':
            instance = g.mysql.query(
                filter
            ).filter(
                filter.user == self.user,
                filter.position < self.position
            ).order_by(
                'position DESC'
            ).first()
            if instance:
                swap(self, instance)
        if direction == 'down':
            instance = g.mysql.query(
                filter
            ).filter(
                filter.user == self.user,
                filter.position > self.position
            ).order_by(
                'position asc'
            ).first()
            if instance:
                swap(self, instance)

    def toggle_status(self):
        self.status = 'Off' if self.status == 'On' else 'On'
        g.mysql.add(self)
        g.mysql.commit()

    def is_valid(self, profanity, source, subject, body):
        source = source.lower()
        subject = subject.lower()
        body = body.lower()
        source_ = modules.utilities.get_filtered_list(source.split(' '))
        subject_ = modules.utilities.get_filtered_list(subject.split(' '))
        body_ = modules.utilities.get_filtered_list(body.split(' '))
        if not self.conditions:
            return True
        count = 0
        for row in self.conditions:
            contents = ('', '')
            if row['operand_1'] == 'From':
                contents = (source, source_)
            if row['operand_1'] == 'Subject':
                contents = (subject, subject_)
            if row['operand_1'] == 'Body':
                contents = (body, body_)
            if row['operand_2'] == '{{ profanity }}':
                if row['operator'] == 'is':
                    if contents[1] == profanity:
                        count += 1
                if row['operator'] == 'contains':
                    if any(word in contents[1] for word in profanity):
                        count += 1
                if row['operator'] == 'does not contain':
                    if not any(word in contents[1] for word in profanity):
                        count += 1
                if row['operator'] == 'has all these words':
                    if all(word in contents[1] for word in profanity):
                        count += 1
                if row['operator'] == 'has atleast one of these words':
                    if any(word in contents[1] for word in profanity):
                        count += 1
                if row['operator'] == 'has none of these words':
                    if not any(word in contents[1] for word in profanity):
                        count += 1
            else:
                if row['operator'] == 'is':
                    if row['operand_2'].lower() == contents[0]:
                        count += 1
                if row['operator'] == 'contains':
                    if row['operand_2'].lower() in contents[0]:
                        count += 1
                if row['operator'] == 'does not contain':
                    if not row['operand_2'].lower() in contents[0]:
                        count += 1
                if row['operator'] == 'has all these words':
                    if all(
                        word in contents[1]
                        for word in modules.utilities.get_filtered_list(
                            row['operand_2'].lower().split(' ')
                        )
                    ):
                        count += 1
                if row['operator'] == 'has atleast one of these words':
                    if any(
                        word in contents[1]
                        for word in modules.utilities.get_filtered_list(
                            row['operand_2'].lower().split(' ')
                        )
                    ):
                        count += 1
                if row['operator'] == 'has none of these words':
                    if not any(
                        word in contents[1]
                        for word in modules.utilities.get_filtered_list(
                            row['operand_2'].lower().split(' ')
                        )
                    ):
                        count += 1
        if count == len(self.conditions):
            return True

filter.__table__.choices = {
    'delay_unit': [
        'Minutes',
        'Hours',
        'Days',
    ],
    'status': [
        'On',
        'Off',
    ],
}
filter.__table__.schedule = {
    'days': [
        range(24),
        range(24),
        range(24),
        range(24),
        range(24),
        range(24),
        range(24),
    ],
    'timezone': 'UTC',
}


class group_(modules.database.base):
    __tablename__ = 'wp_groups_group'
    __table_args__ = {
        'autoload': True,
    }


class log(modules.database.base):
    __tablename__ = 'logs'
    __table_args__ = {
        'autoload': True,
    }

    account = relationship(
        'account',
        backref=backref(
            'logs',
            cascade='all',
            lazy='dynamic'
        )
    )

    def before_insert(self):
        if not self.timestamp:
            self.timestamp = datetime.now()


class meta(modules.database.base):
    __tablename__ = 'wp_usermeta'
    __table_args__ = {
        'autoload': True,
    }


class option(modules.database.base):
    __tablename__ = 'wp_options'
    __table_args__ = {
        'autoload': True,
    }

    @staticmethod
    def get_dictionary():
        dictionary = option.get_option_value()
        instance = option.get_instance()
        if instance:
            dictionary = loads(instance.option_value)
        return dictionary

    @staticmethod
    def get_instance():
        return g.mysql.query(
            option
        ).filter(
            option.option_name == option.get_option_name()
        ).first()

    @staticmethod
    def get_option_name():
        return 'settings'

    @staticmethod
    def get_option_value():
        return {
            'change_log': '',
            'profanity': [],
            'version': '0.1',
            'videos_accounts': [],
            'videos_dashboard': [],
            'videos_filters': [],
            'videos_groups': [],
            'videos_packs': [],
            'videos_proxies': [],
            'videos_queues': [],
            'videos_settings': [],
            'videos_suggestions': [],
            'videos_templates': [],
            'videos_variables': [],
        }

    @staticmethod
    def set_dictionary(dictionary):
        instance = option.get_instance()
        if not instance:
            instance = option(**{
                'option_name': option.get_option_name(),
                'autoload': 'no',
            })
        instance.option_value = dumps(dictionary)
        g.mysql.add(instance)
        g.mysql.commit()


class queue(modules.database.base):
    __tablename__ = 'queues'
    __table_args__ = {
        'autoload': True,
    }

    filter = relationship(
        'filter',
        backref=backref(
            'queues',
            cascade='all',
            lazy='dynamic'
        )
    )

    log = relationship(
        'log',
        backref=backref(
            'queues',
            cascade='all',
            lazy='dynamic'
        )
    )

    template = relationship(
        'template',
        backref=backref(
            'queues',
            cascade='all',
            lazy='dynamic'
        )
    )

    def before_insert(self):
        if not self.scheduled_at:
            self.scheduled_at = datetime.now()
        if not self.status or not self.status in self.__table__.choices[
            'status'
        ]:
            self.status = self.__table__.choices['status'][0]
        if self.is_invalid():
            self.status = 'Skipped'
        if not self.status == 'Scheduled':
            self.subject = ''
            self.body = ''

    def cancel(self):
        self.status = 'Cancelled'
        g.mysql.add(self)
        g.mysql.commit()

    def synchronize(self):
        self.template = self.get_template()

    def get_account(self):
        return g.mysql.query(
            account
        ).filter(
            account.id == self.filter.steps[self.step]['account']
        ).first() or self.log.account

    def get_reply_to(self):
        account = self.get_account()
        return '"%(name)s" <%(email)s>' % {
            'email':
            self.filter.steps[self.step]['reply_to_email'] or account.username,
            'name':
            self.filter.steps[self.step]['reply_to_name']
            or
            account.get_name(),
        }

    def get_scheduled_for(self):
        timestamp = self.scheduled_at + timedelta(
            minutes=self.filter.steps[self.step]['delay_quantity']
            if self.filter.steps[self.step]['delay_unit'] == 'Minutes' else 0,
            hours=self.filter.steps[self.step]['delay_quantity']
            if self.filter.steps[self.step]['delay_unit'] == 'Hours' else 0,
            days=self.filter.steps[self.step]['delay_quantity']
            if self.filter.steps[self.step]['delay_unit'] == 'Days' else 0
        )
        custom = timezone(self.filter.schedule['timezone'])
        default = timezone('UTC')
        timestamp = timestamp.replace(tzinfo=default).astimezone(custom)
        if sum(map(sum, self.filter.schedule['days'])):
            while True:
                if timestamp.hour in self.filter.schedule[
                    'days'
                ][timestamp.isoweekday() - 1]:
                    break
                timestamp = timestamp.replace(
                    minute=0, second=0
                ) + timedelta(hours=1)
        return (
            timestamp.astimezone(default).replace(tzinfo=None),
            timestamp.astimezone(custom).replace(tzinfo=None)
        )

    def get_template(self):
        templates = g.mysql.query(
            template
        ).filter(
            template.id.in_(self.filter.steps[self.step]['templates'])
        ).order_by(
            'id asc'
        ).all()
        if templates:
            return choice(templates)
        return choice(self.log.account.user.templates.all())

    def is_invalid(self):
        try:
            for item in self.log.account.group.get_blacklist():
                if match(
                    compile(item.replace('*', '.*?'), IGNORECASE), self.email
                ):
                    return True
            for item in self.log.account.get_blacklist():
                if match(
                    compile(item.replace('*', '.*?'), IGNORECASE), self.email
                ):
                    return True
            for item in self.log.account.user.get_settings()['blacklist']:
                if match(
                    compile(item.replace('*', '.*?'), IGNORECASE), self.email
                ):
                    return True
        except:
            pass
        return False

queue.__table__.choices = {
    'status': [
        'Scheduled',
        'Skipped',
        'Cancelled',
        'Backlogged',
        'Delivered',
    ],
}


class template(modules.database.base):
    __tablename__ = 'templates'
    __table_args__ = {
        'autoload': True,
    }

    def before_delete(self):
        path = self.get_path()
        if isdir(path):
            rmtree(path, True)

    def synchronize(self, action):
        if action in ['add', 'edit']:
            for attachment in request.files.getlist('attachments[add]'):
                name = secure_filename(attachment.filename)
                if name:
                    attachment.save(join(self.get_path(), name))
            for name in request.form.getlist('attachments[delete]'):
                path = join(self.get_path(), name)
                if isfile(path):
                    remove(path)
        if action in ['delete']:
            path = self.get_path()
            if isdir(path):
                rmtree(path)

    def get_attachments(self):
        path = self.get_path()
        if not path:
            return []
        attachments = []
        for name in sorted(listdir(path)):
            resource = join(path, name)
            if not isfile(resource):
                continue
            extension = ''
            try:
                extension = splitext(name)[1]
            except:
                pass
            attachments.append({
                'class': modules.utilities.get_class(extension),
                'extension': extension,
                'name': name,
                'resource': resource,
                'size': ((getsize(resource) * 1.00) / 1024.00),
            })
        return attachments

    def get_contents(self, variables, string, nl2br):
        for key in findall(r'({{ alphabets\|\d+ }})', string):
            string = string.replace(key, modules.utilities.get_alphabets(
                int(key.split(' ')[1].split('|')[-1])
            ))
        for key in findall(r'({{ numbers\|\d+ }})', string):
            string = string.replace(key, modules.utilities.get_numbers(
                int(key.split(' ')[1].split('|')[-1])
            ))
        for key in findall(r'({{ \d+\|\d+ }})', string):
            string = string.replace(key, str(
                randint(*map(int, key.split(' ')[1].split('|')))
            ))
        for key in findall(r'({{ .*? }})', string):
            if not '|' in key:
                continue
            string = string.replace(key, choice(key[3:-3].split('|')))
        for key, value in variables.iteritems():
            string = string.replace(
                key, value.replace('\n', '<br>') if nl2br else value
            )
        return string

    def get_path(self):
        if not self.id:
            return
        id = 0
        if self.user:
            id = self.user.ID
        path = join(template.__table__.path, str(id), str(self.id))
        if not isdir(path):
            makedirs(path)
        return path

    def get_subject_and_bodies(self):
        variables = {}
        if self.user:
            for variable in self.user.variables.all():
                variables['{{ %(key)s }}' % {
                    'key': variable.key,
                }] = variable.value
        return (
            self.get_contents(variables, self.subject, False),
            self.get_contents(variables, self.bodies_plain_text, False),
            self.get_contents(variables, self.bodies_html, True)
        )

template.__table__.path = join(
    dirname(__file__), '..', 'resources', 'files', 'templates'
)


class user(modules.database.base):
    __tablename__ = 'wp_users'
    __table_args__ = {
        'autoload': True,
    }

    accounts = relationship(
        'account',
        backref='user',
        lazy='dynamic'
    )

    filters = relationship(
        'filter',
        backref='user',
        lazy='dynamic'
    )

    groups_ = relationship(
        'group_',
        backref=backref(
            'users',
            lazy='dynamic',
        ),
        lazy='dynamic',
        secondary='wp_groups_user_group'
    )

    groups = relationship(
        'group',
        backref='user',
        lazy='dynamic'
    )

    meta = relationship(
        'meta',
        backref='user',
        lazy='dynamic'
    )

    packs = relationship(
        'pack',
        backref='user',
        lazy='dynamic'
    )

    proxies = relationship(
        'proxy',
        backref='user',
        lazy='dynamic'
    )

    templates = relationship(
        'template',
        backref='user',
        lazy='dynamic'
    )

    variables = relationship(
        'variable',
        backref='user',
        lazy='dynamic'
    )

    def get_age(self):
        instance = g.mysql.query(
            queue
        ).join(
            log
        ).join(
            account
        ).filter(
            account.id == log.account_id,
            account.user == self,
            log.id == queue.log_id
        ).order_by(
            'queues.id asc'
        ).first()
        if not instance:
            return 0
        return (datetime.now() - instance.scheduled_at).days

    def get_counts(self):

        def get_count(user, status):
            return g.mysql.query(
                queue
            ).join(
                log
            ).join(
                account
            ).filter(
                account.id == log.account_id,
                account.user == self,
                log.id == queue.log_id,
                queue.status == status
            ).order_by(
                'queues.id asc'
            ).count()

        return {
            'Backlogged': get_count(user, 'Backlogged'),
            'Cancelled': get_count(user, 'Cancelled'),
            'Delivered': get_count(user, 'Delivered'),
            'Everything': g.mysql.query(
                queue
            ).join(
                log
            ).join(
                account
            ).filter(
                account.id == log.account_id,
                account.user == self,
                log.id == queue.log_id
            ).order_by(
                'queues.id asc'
            ).count(),
            'Scheduled': get_count(user, 'Scheduled'),
            'Skipped': get_count(user, 'Skipped'),
        }

    def get_credits(self):
        if self.get_group() in ['Free', 'Premium', 'Premium+']:
            return {
                'remaining': 0,
                'settings': self.get_settings()['credits'],
                'total': 0,
                'used': 0,
            }
        total = self.get_total()
        now = datetime.now()
        used = g.mysql.query(
            queue
        ).join(
            log
        ).join(
            account
        ).filter(
            account.id == log.account_id,
            account.user == self,
            log.id == queue.log_id,
            queue.status == 'Delivered'
        )
        if not self.get_group() == 'Pay-As-You-Go':
            used = used.filter(
                func.month(queue.delivered_at) == now.month,
                func.year(queue.delivered_at) == now.year,
            )
        used = used.count()
        return {
            'remaining': total - used,
            'settings': self.get_settings()['credits'],
            'total': total,
            'used': used,
        }

    def get_first_name(self):
        first_name = self.display_name
        instance = g.mysql.query(
            meta
        ).filter(
            meta.meta_key == 'first_name',
            meta.user == self
        ).first()
        if instance and instance.meta_value:
            first_name = instance.meta_value
        return first_name

    def get_group(self):
        names = [
            group.name
            for group in self.groups_.all()
        ]
        if 'Free Plan' in names:
            return 'Free'
        if 'Third Tier+' in names:
            return 'Premium+'
        if 'Third Tier Subscription' in names:
            return 'Premium'
        if 'Second Tier+' in names:
            return 'Advanced+'
        if 'Second Tier Subscription' in names:
            return 'Advanced'
        if 'First Tier+' in names:
            return 'Starter+'
        if 'First Tier Subscription' in names:
            return 'Starter'
        if 'Pay As You Go Plan' in names:
            return 'Pay-As-You-Go'
        return ''

    def get_items(self):
        items = {}
        for instance in g.mysql.query(
            queue
        ).join(
            log
        ).join(
            account
        ).filter(
            account.id == log.account_id,
            account.user == self,
            log.id == queue.log_id
        ).order_by(
            'queues.id asc'
        ).all():
            if not instance.email in items:
                items[instance.email] = (
                    instance.name.encode('utf-8'),
                    instance.email.encode('utf-8'),
                    modules.utilities.get_date_and_time(
                        instance.scheduled_at
                    ).encode('utf-8'),
                    modules.utilities.get_date_and_time(
                        instance.delivered_at
                    ).encode('utf-8')
                    if instance.delivered_at else 'N/A'.encode('utf-8'),
                    instance.filter.id,
                )
        return items

    def get_meta(self):
        meta_key = 'blacklist'
        blacklist = g.mysql.query(
            meta
        ).filter(
            meta.meta_key == meta_key,
            meta.user == self
        ).order_by(
            'umeta_id asc'
        ).first()
        if not blacklist:
            blacklist = meta(**{
                'meta_key': meta_key,
                'user': self,
            })
        meta_key = 'credits'
        credits = g.mysql.query(
            meta
        ).filter(
            meta.meta_key == meta_key,
            meta.user == self
        ).order_by(
            'umeta_id asc'
        ).first()
        if not credits:
            credits = meta(**{
                'meta_key': meta_key,
                'user': self,
            })
        meta_key = 'filters'
        filters = g.mysql.query(
            meta
        ).filter(
            meta.meta_key == meta_key,
            meta.user == self
        ).order_by(
            'umeta_id asc'
        ).first()
        if not filters:
            filters = meta(**{
                'meta_key': meta_key,
                'user': self,
            })
        meta_key = 'profanity'
        profanity = g.mysql.query(
            meta
        ).filter(
            meta.meta_key == meta_key,
            meta.user == self
        ).order_by(
            'umeta_id asc'
        ).first()
        if not profanity:
            profanity = meta(**{
                'meta_key': meta_key,
                'user': self,
            })
        return {
            'blacklist': blacklist,
            'credits': credits,
            'filters': filters,
            'profanity': profanity,
        }

    def get_output(self, input, iterations):
        output = ''
        index = 0
        while index < iterations:
            value = ord(input[index])
            index += 1
            output += user.__table__.itoa64[value & 0x3f]
            if index < iterations:
                value |= (ord(input[index]) << 8)
            output += user.__table__.itoa64[(value >> 6) & 0x3f]
            if index >= iterations:
                break
            index += 1
            if index < iterations:
                value |= (ord(input[index]) << 16)
            output += user.__table__.itoa64[(value >> 12) & 0x3f]
            if index >= iterations:
                break
            index += 1
            output += user.__table__.itoa64[(value >> 18) & 0x3f]
        return output

    def get_products(self):
        products = []
        for post_meta in modules.database.engine.execute(
            '''
            SELECT post_id
            FROM wp_postmeta
            WHERE meta_key = %(meta_key)s AND meta_value = %(meta_value)s
            ''',
            {
                'meta_key': '_customer_user',
                'meta_value': self.ID,
            }
        ).fetchall():
            if modules.database.engine.execute(
                '''
                SELECT name
                FROM wp_terms
                WHERE term_id IN (
                    SELECT term_taxonomy_id
                    FROM wp_term_relationships
                    WHERE object_id = %(object_id)s
                )
                ''',
                {
                    'object_id': post_meta['post_id'],
                }
            ).fetchone()['name'] == 'completed':
                products.append(
                    modules.database.engine.execute(
                        '''
                        SELECT order_item_name
                        FROM wp_woocommerce_order_items
                        WHERE order_id = %(post_id)s
                        ''',
                        {
                            'post_id': post_meta['post_id'],
                        }
                    ).fetchone()['order_item_name']
                )
        return products

    def get_profanity(self):
        profanity = self.get_settings()['profanity']
        if '{{ import }}' in profanity:
            profanity.remove('{{ import }}')
            profanity += option.get_dictionary()['profanity']
        return modules.utilities.get_filtered_list(profanity)

    def get_queues(self):
        return g.mysql.query(
            queue
        ).join(
            log
        ).join(
            account
        ).filter(
            queue.status == 'Scheduled',
            account.id == log.account_id,
            account.user == self,
            log.id == queue.log_id
        ).count()

    def get_seconds(self):
        return (14 * 24 * 60 * 60) - (
            datetime.now() - self.user_registered
        ).total_seconds()

    def get_settings(self):
        blacklist = []
        credits = 50
        filters = 'No'
        profanity = ['{{ import }}']
        dictionary = self.get_meta()
        if dictionary['blacklist'].meta_value:
            blacklist = modules.utilities.get_filtered_list(
                dictionary['blacklist'].meta_value.split('\n')
            )
        if dictionary['credits'].meta_value:
            credits = int(dictionary['credits'].meta_value)
        if dictionary['filters'].meta_value:
            filters = dictionary['filters'].meta_value
        if dictionary['profanity'].meta_value:
            profanity = modules.utilities.get_filtered_list(
                dictionary['profanity'].meta_value.split('\n')
            )
        return {
            'blacklist': blacklist,
            'credits': credits,
            'filters': filters,
            'profanity': profanity,
        }

    def get_signature(self):
        salt = (
            '%x7$tQ&Ld6(^nOhW4PBfeOdISL3hNcVrrDdc2k2mA!6&2K5kzKuwA#oAZ&b3QC21'
        )
        return md5(salt + str(self.ID) + salt).hexdigest()

    def get_total(self):
        if settings.is_mahendra():
            return 5
        group = self.get_group()
        if group == 'Free':
            return 0
        if group == 'Premium+':
            return 0
        if group == 'Premium':
            return 0
        if group == 'Advanced+':
            return 3000
        if group == 'Advanced':
            return 3000
        if group == 'Starter+':
            return 500
        if group == 'Starter':
            return 500
        if group == 'Pay-As-You-Go':
            total = 0
            total += 50
            for product in self.get_products():
                if product == '900 Credits':
                    total += 900
                if product == '300 Credits':
                    total += 300
                if product == '50 Credits':
                    total += 50
            return total
        return 0

    def set_survey(self):
        g.mysql.add(meta(**{
            'meta_key': 'survey',
            'meta_value': 'true',
            'user': self,
        }))
        g.mysql.commit()

    def can_survey(self):
        if not self.get_age() > 3:
            return False
        if self.has_survey():
            return False
        if not self.get_group() == 'Pay-As-You-Go':
            return False
        return True

    def has_survey(self):
        instance = g.mysql.query(
            meta
        ).filter(
            meta.meta_key == 'survey',
            meta.user == self
        ).first()
        if instance:
            return True

    def is_active(self):
        if not self.get_group() == '':
            return True
        return False

    def is_valid(self, password):
        hash = self.user_pass
        count = 1 << user.__table__.itoa64.find(hash[3])
        salt = hash[4:12]
        if not isinstance(password, str):
            password = password.encode('utf-8')
        digest = md5(salt + password).digest()
        while count:
            digest = md5(digest + password).digest()
            count -= 1
        return hash[:12] + self.get_output(digest, 16) == hash

user.__table__.itoa64 = (
    './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
)


class variable(modules.database.base):
    __tablename__ = 'variables'
    __table_args__ = {
        'autoload': True,
    }


class filter_account(modules.database.base):
    __tablename__ = 'filters_accounts'
    __table_args__ = {
        'autoload': True,
    }


class user_group(modules.database.base):
    __tablename__ = 'wp_groups_user_group'
    __table_args__ = {
        'autoload': True,
    }


class code(modules.database.base):
    __tablename__ = 'codes'
    __table_args__ = {
        'autoload': True,
    }

    templates = relationship(
        'template',
        backref=backref(
            'codes',
            lazy='dynamic',
        ),
        lazy='dynamic',
        secondary='codes_templates'
    )

    packs = relationship(
        'pack',
        backref=backref(
            'codes',
            lazy='dynamic',
        ),
        lazy='dynamic',
        secondary='codes_packs'
    )

    filters = relationship(
        'filter',
        backref=backref(
            'codes',
            lazy='dynamic',
        ),
        lazy='dynamic',
        secondary='codes_filters'
    )

    def redeem(self, user, types):

        def get_templates(code):
            templates = []
            for instance in code.templates.order_by('name asc').all():
                t = g.mysql.query(
                    template
                ).filter(
                    template.name == instance.name,
                    template.user == user
                ).first()
                if t:
                    templates.append(t.id)
            return templates

        placeholder = user.accounts.filter(
            account.username == 'placeholder@mailsidekick.com'
        ).first()
        if 'templates' in types:
            for instance in self.templates.order_by('name asc').all():
                if not g.mysql.query(
                    template
                ).filter(
                    template.name == instance.name,
                    template.user == user
                ).first():
                    dictionary = instance.to_dictionary()
                    del dictionary['id']
                    dictionary['user'] = user
                    i = template(**dictionary)
                    g.mysql.add(i)
                    g.mysql.commit()
                    g.mysql.refresh(i)
                    path = i.get_path()
                    for attachment in instance.get_attachments():
                        copy2(attachment['resource'], path)
        if 'packs' in types:
            for instance in self.packs.order_by('name asc').all():
                if not g.mysql.query(
                    pack
                ).filter(
                    pack.name == instance.name,
                    pack.user == user
                ).first():
                    dictionary = instance.to_dictionary()
                    del dictionary['id']
                    dictionary['filters'] = []
                    for i in instance.filters.order_by(
                        'position asc'
                    ).all():
                        if not g.mysql.query(
                            filter
                        ).filter(
                            filter.name == i.name,
                            filter.user == user
                        ).first():
                            d = i.to_dictionary()
                            del d['id']
                            d['accounts'] = [placeholder]
                            for index, _ in enumerate(d['steps']):
                                d[
                                    'steps'
                                ][index]['account'] = str(placeholder.id)
                                d[
                                    'steps'
                                ][index]['templates'] = get_templates(self)
                            d['user'] = user
                            dictionary['filters'].append(filter(**d))
                    dictionary['user'] = user
                    g.mysql.add(pack(**dictionary))
                    g.mysql.commit()
        if 'filters' in types:
            for instance in self.filters.order_by('position asc').all():
                if not g.mysql.query(
                    filter
                ).filter(
                    filter.name == instance.name,
                    filter.user == user
                ).first():
                    dictionary = instance.to_dictionary()
                    del dictionary['id']
                    dictionary['accounts'] = [placeholder]
                    for index, _ in enumerate(dictionary['steps']):
                        dictionary[
                            'steps'
                        ][index]['account'] = str(placeholder.id)
                        dictionary[
                            'steps'
                        ][index]['templates'] = get_templates(self)
                    dictionary['user'] = user
                    g.mysql.add(filter(**dictionary))
                    g.mysql.commit()

    def get_filter_ids(self):
        return [
            instance.id
            for instance in self.filters.order_by('filters.id asc').all()
        ]

    def get_pack_ids(self):
        return [
            instance.id
            for instance in self.packs.order_by('packs.id asc').all()
        ]

    def get_items(self, user):
        return {
            'filters': [
                filter.name
                for filter in self.filters.order_by('position asc').all()
            ],
            'packs': [
                pack.name
                for pack in self.packs.order_by('name asc').all()
            ],
            'templates': [
                template.name
                for template in self.templates.order_by('name asc').all()
            ],
        }

    def has_redeemed(self, user):
        if g.mysql.query(
            meta
        ).filter(
            meta.meta_key == self.value,
            meta.user == user
        ).order_by(
            'umeta_id asc'
        ).first():
            return True
        return False


class code_template(modules.database.base):
    __tablename__ = 'codes_templates'
    __table_args__ = {
        'autoload': True,
    }


class code_pack(modules.database.base):
    __tablename__ = 'codes_packs'
    __table_args__ = {
        'autoload': True,
    }


class code_filter(modules.database.base):
    __tablename__ = 'codes_filters'
    __table_args__ = {
        'autoload': True,
    }


def swap(one, two):
    one.position, two.position = two.position, one.position
    g.mysql.add(one)
    g.mysql.add(two)
    g.mysql.commit()


def after_delete(mapper, connection, instance):
    function = getattr(instance, 'after_delete', None)
    if callable(function):
        function()


def after_flush(session, context):
    pass


def after_insert(mapper, connection, instance):
    function = getattr(instance, 'after_insert', None)
    if callable(function):
        function()


def after_update(mapper, connection, instance):
    set_columns(mapper, connection, instance)
    function = getattr(instance, 'after_update', None)
    if callable(function):
        function()


def before_delete(mapper, connection, instance):
    set_columns(mapper, connection, instance)
    function = getattr(instance, 'before_delete', None)
    if callable(function):
        function()


def before_flush(session, context, instances):
    for instance in session.new:
        if isinstance(instance, queue):
            instance.synchronize()


def before_insert(mapper, connection, instance):
    set_columns(mapper, connection, instance)
    function = getattr(instance, 'before_insert', None)
    if callable(function):
        function()


def before_update(mapper, connection, instance):
    set_columns(mapper, connection, instance)
    function = getattr(instance, 'before_update', None)
    if callable(function):
        function()


def set_columns(mapper, connection, instance):
    for column in mapper.local_table.c:
        if column.type.__visit_name__ in ['TEXT', 'VARCHAR']:
            value = getattr(instance, column.name)
            if not value:
                value = ''
            if isinstance(value, basestring):
                value = modules.utilities.get_unescaped_string(value.strip())
            setattr(instance, column.name, value)


listen(mapper, 'after_delete', after_delete)
listen(mapper, 'after_insert', after_insert)
listen(mapper, 'after_update', after_update)
listen(mapper, 'before_delete', before_update)
listen(mapper, 'before_insert', before_insert)
listen(mapper, 'before_update', before_update)
