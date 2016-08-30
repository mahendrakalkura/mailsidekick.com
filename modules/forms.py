# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from flask import g, request, session
from flask.ext.mail import Message
from flask_wtf import Form
from itertools import izip, izip_longest
from pytz import all_timezones
from re import sub
from simplejson import loads
from smtplib import SMTP_SSL
from sqlalchemy.sql import null
from traceback import print_exc
from wtforms.ext.sqlalchemy.fields import (
    QuerySelectField, QuerySelectMultipleField
)
from wtforms.fields import (
    BooleanField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    TextAreaField,
    TextField,
)
from wtforms.widgets import CheckboxInput

import modules.database
import modules.fields
import modules.mail
import modules.models
import modules.utilities
import modules.validators
import modules.widgets

import settings


def get_accounts_choices():
    return [
        (account.id, account.username) for account in get_accounts_factory()
    ]


def get_accounts_factory():
    return g.mysql.query(
        modules.models.account
    ).filter(
        modules.models.account.user == (
            g.user if hasattr(g, 'user') else null()
        ),
        modules.models.account.status == 'On'
    ).order_by(
        'username asc'
    )


def get_filters_choices():
    return [(filter.id, filter.name) for filter in get_filters_factory()]


def get_filters_factory():
    return g.mysql.query(
        modules.models.filter
    ).filter(
        modules.models.filter.user == (
            g.user if hasattr(g, 'user') else null()
        ),
        modules.models.filter.status == 'On'
    ).order_by(
        'position asc'
    )


def get_groups_choices():
    return [(group.id, group.name) for group in get_groups_factory()]


def get_groups_factory():
    return g.mysql.query(
        modules.models.group
    ).filter(
        modules.models.group.user == (
            g.user if hasattr(g, 'user') else null()
        ),
    ).order_by(
        'id asc'
    )


def get_packs_choices():
    return [(pack.id, pack.name) for pack in get_packs_factory()]


def get_packs_factory():
    return g.mysql.query(
        modules.models.pack
    ).filter(
        modules.models.pack.user == (g.user if hasattr(g, 'user') else null()),
    ).order_by(
        'id asc'
    )


def get_proxies_choices():
    return [(proxy.id, proxy.name) for proxy in get_proxies_factory()]


def get_proxies_factory():
    return g.mysql.query(
        modules.models.proxy
    ).filter(
        modules.models.proxy.user == (
            g.user if hasattr(g, 'user') else null()
        ),
    ).order_by(
        'id asc'
    )


def get_templates_choices():
    return [
        (template.id, template.name) for template in get_templates_factory()
    ]


def get_templates_factory():
    return g.user.templates.order_by('name asc')


class administrators_form(Form):
    email = TextField(validators=[
        modules.validators.required(),
        modules.validators.email(),
        modules.validators.unique(table='administrators', columns=[]),
    ])
    password = PasswordField()
    name = TextField(validators=[modules.validators.required()])

    def persist(self, administrator):
        administrator.email = self.email.data
        administrator.name = self.name.data
        administrator.set_password_from_string(self.password.data)
        g.mysql.add(administrator)
        g.mysql.commit()


class administrators_add(administrators_form):

    def __init__(self, *args, **kwargs):
        super(administrators_add, self).__init__(*args, **kwargs)
        self['password'].validators = [modules.validators.required()]
        self['password'].flags.required = True


class administrators_edit(administrators_form):
    pass


class administrators_filters(Form):
    email = TextField()
    name = TextField()
    status = SelectField(
        choices=modules.utilities.get_tuples(
            modules.models.administrator.__table__.choices['status'],
            ('', 'All'),
        ),
        default=''
    )

    def get_query(self, query):
        if self.email.data:
            query = query.filter(modules.models.administrator.email.like(
                '%%%(email)s%%' % {
                    'email': self.email.data,
                }
            ))
        if self.name.data:
            query = query.filter(modules.models.administrator.name.like(
                '%%%(name)s%%' % {
                    'name': self.name.data,
                }
            ))
        if self.status.data:
            query = query.filter(
                modules.models.administrator.status == self.status.data
            )
        return query


class administrators_profile(administrators_form):
    pass


class administrators_settings(Form):

    @staticmethod
    def get_dictionary():
        dictionary = modules.models.option.get_dictionary()
        for key, _ in dictionary.iteritems():
            if key == 'change_log':
                dictionary[key] = dictionary[key]
                continue
            if key == 'version':
                dictionary[key] = dictionary[key]
                continue
            dictionary[key] = '\n'.join(dictionary[key])
        return dictionary

    def persist(self):
        dictionary = modules.models.option.get_option_value()
        for key, _ in dictionary.iteritems():
            if key == 'change_log':
                dictionary[key] = getattr(self, key).data
                continue
            if key == 'version':
                dictionary[key] = getattr(self, key).data
                continue
            dictionary[key] = modules.utilities.get_filtered_list(
                getattr(self, key).data.split('\n')
            )
        modules.models.option.set_dictionary(dictionary)


class administrators_sign_in(Form):
    email = TextField(validators=[modules.validators.required()])
    password = PasswordField(validators=[modules.validators.required()])

    def validate(self):
        if super(administrators_sign_in, self).validate():
            administrator = g.mysql.query(
                modules.models.administrator
            ).filter(
                modules.models.administrator.email == self.email.data,
                modules.models.administrator.status == 'On'
            ).first()
            if administrator and administrator.is_valid(self.password.data):
                session['administrator'] = administrator.id
                return True
        self.email.errors = ['Invalid Email/Password']
        self.password.errors = []
        return False


class accounts_form(Form):
    group = QuerySelectField(
        allow_blank=False,
        blank_text='',
        get_label='name',
        query_factory=get_groups_factory,
        validators=[modules.validators.required()]
    )
    proxy = QuerySelectField(
        allow_blank=True,
        blank_text='',
        get_label='name',
        query_factory=get_proxies_factory
    )
    description = TextAreaField(
        description=[
            'This is a general purpose field. You can add notes pertaining to '
            'this account in here.',
        ],
        label='Description',
        validators=[modules.validators.required()],
        widget=modules.widgets.textarea(rows=5)
    )
    incoming_hostname = TextField(
        label='Hostname',
        validators=[modules.validators.required()]
    )
    incoming_port_number = IntegerField(
        label='Port Number',
        validators=[modules.validators.required()]
    )
    incoming_use_ssl = BooleanField(label='Use SSL?')
    outgoing_hostname = TextField(
        label='Hostname',
        validators=[modules.validators.required()]
    )
    outgoing_port_number = IntegerField(
        label='Port Number',
        validators=[modules.validators.required()]
    )
    outgoing_use_ssl = BooleanField(label='Use SSL?')
    outgoing_use_tls = BooleanField(label='Use TLS?')
    username = TextField(validators=[
        modules.validators.required(),
        modules.validators.unique(table='accounts', columns=['user_id'])
    ])
    password = TextField(validators=[modules.validators.required()])
    blacklist = TextAreaField(
        description=[
            'Please enter one email per line. You can use the * wildcard.',
        ],
        label='Blacklist',
        widget=modules.widgets.textarea(rows=5)
    )

    def persist(self, account):
        account.group = self.group.data
        account.proxy = self.proxy.data
        account.description = self.description.data
        account.incoming_hostname = self.incoming_hostname.data
        account.incoming_port_number = self.incoming_port_number.data
        account.incoming_use_ssl = \
            'Yes' if self.incoming_use_ssl.data else 'No'
        account.outgoing_hostname = self.outgoing_hostname.data
        account.outgoing_port_number = self.outgoing_port_number.data
        account.outgoing_use_ssl = \
            'Yes' if self.outgoing_use_ssl.data else 'No'
        account.outgoing_use_tls = \
            'Yes' if self.outgoing_use_tls.data else 'No'
        account.username = self.username.data
        account.password = self.password.data
        account.blacklist = self.blacklist.data
        g.mysql.add(account)
        g.mysql.commit()


class accounts_add(accounts_form):
    pass


class accounts_edit(accounts_form):
    pass


class accounts_filters(Form):
    group = SelectField(choices=[], coerce=int, default='')
    incoming_hostname = TextField(label='Hostname')
    incoming_port_number = IntegerField(label='Port Number')
    incoming_use_ssl = SelectField(
        choices=modules.utilities.get_tuples(
            modules.models.account.__table__.choices['incoming_use_ssl'],
            ('', 'All'),
        ),
        default='',
        label='Use SSL?'
    )
    outgoing_hostname = TextField(label='Hostname')
    outgoing_port_number = IntegerField(label='Port Number')
    outgoing_use_ssl = SelectField(
        choices=modules.utilities.get_tuples(
            modules.models.account.__table__.choices['outgoing_use_ssl'],
            ('', 'All'),
        ),
        default='',
        label='Use SSL?'
    )
    outgoing_use_tls = SelectField(
        choices=modules.utilities.get_tuples(
            modules.models.account.__table__.choices['outgoing_use_tls'],
            ('', 'All'),
        ),
        default='',
        label='Use TLS?'
    )
    username = TextField()
    password = TextField()
    status = SelectField(
        choices=modules.utilities.get_tuples(
            modules.models.account.__table__.choices['status'],
            ('', 'All'),
        ),
        default=''
    )

    def __init__(self, *args, **kwargs):
        super(accounts_filters, self).__init__(*args, **kwargs)
        self.group.choices = [(0, 'All')] + get_groups_choices()

    def get_query(self, query):
        if self.group.data:
            query = query.filter(
                modules.models.account.group_id == self.group.data
            )
        if self.incoming_hostname.data:
            query = query.filter(modules.models.account.incoming_hostname.like(
                '%%%(hostname)s%%' % {
                    'hostname': self.incoming_hostname.data,
                }
            ))
        if self.incoming_port_number.data:
            query = query.filter(
                modules.models.account.incoming_port_number.like(
                    '%%%(port_number)s%%' % {
                        'port_number': self.incoming_port_number.data,
                    }
                )
            )
        if self.incoming_use_ssl.data:
            query = query.filter(
                modules.models.account.incoming_use_ssl
                ==
                self.incoming_use_ssl.data
            )
        if self.outgoing_hostname.data:
            query = query.filter(modules.models.account.outgoing_hostname.like(
                '%%%(hostname)s%%' % {
                    'hostname': self.outgoing_hostname.data,
                }
            ))
        if self.outgoing_port_number.data:
            query = query.filter(
                modules.models.account.outgoing_port_number.like(
                    '%%%(port_number)s%%' % {
                        'port_number': self.outgoing_port_number.data,
                    }
                )
            )
        if self.outgoing_use_ssl.data:
            query = query.filter(
                modules.models.account.outgoing_use_ssl
                ==
                self.outgoing_use_ssl.data
            )
        if self.outgoing_use_tls.data:
            query = query.filter(
                modules.models.account.outgoing_use_tls
                ==
                self.outgoing_use_tls.data
            )
        if self.username.data:
            query = query.filter(modules.models.account.username.like(
                '%%%(username)s%%' % {
                    'username': self.username.data,
                }
            ))
        if self.password.data:
            query = query.filter(modules.models.account.password.like(
                '%%%(password)s%%' % {
                    'password': self.password.data,
                }
            ))
        if self.status.data:
            query = query.filter(
                modules.models.account.status == self.status.data
            )
        return query


class articles_form(Form):
    type = SelectField(
        choices=modules.models.article.__table__.choices['type'],
        default='',
        validators=[modules.validators.required()]
    )
    title = TextField(validators=[modules.validators.required()])
    contents = modules.fields.wysihtml5(
        validators=[modules.validators.required()],
        widget=modules.widgets.textarea(rows=10)
    )

    def persist(self, article):
        article.type = self.type.data
        article.title = self.title.data
        article.contents = self.contents.data
        g.mysql.add(article)
        g.mysql.commit()


class articles_add(articles_form):
    pass


class articles_edit(articles_form):
    pass


class articles_filters(Form):
    type = SelectField(
        choices=[
            ('', 'All')
        ] + modules.models.article.__table__.choices['type'],
        default=''
    )
    title = TextField()
    status = SelectField(
        choices=modules.utilities.get_tuples(
            modules.models.article.__table__.choices['status'],
            ('', 'All'),
        ),
        default=''
    )
    timestamp = modules.fields.daterangepicker(label='Date/Time')

    def get_query(self, query):
        if self.type.data:
            query = query.filter(modules.models.article.type == self.type.data)
        if self.title.data:
            query = query.filter(
                modules.models.article.title.like('%%%(title)s%%' % {
                    'title': self.title.data,
                })
            )
        if self.status.data:
            query = query.filter(
                modules.models.article.status == self.status.data
            )
        if self.timestamp.data:
            timestamp = self.timestamp.data.split(' to ')
            query = query.filter(
                modules.models.article.timestamp >= timestamp[0] + ' 00:00:00',
                modules.models.article.timestamp <= timestamp[1] + ' 23:59:59'
            )
        return query


class filters_form(Form):
    pack = QuerySelectField(
        allow_blank=True,
        blank_text='N/A',
        get_label='name',
        query_factory=get_packs_factory
    )
    name = TextField(validators=[
        modules.validators.required(),
        modules.validators.unique(table='filters', columns=['user_id']),
    ])
    description = TextAreaField(
        description=[
            'This is a general purpose field. You can add notes pertaining to '
            'this recipe in here.',
        ],
        label='Description',
        validators=[modules.validators.required()],
        widget=modules.widgets.textarea(rows=5)
    )
    accounts = QuerySelectMultipleField(
        allow_blank=False,
        description=[
            'This recipe will be applied to the accounts that you select '
            'here.',
        ],
        get_label='username',
        label='Account(s)',
        option_widget=CheckboxInput(),
        query_factory=get_accounts_factory,
        validators=[modules.validators.required()],
        widget=modules.widgets.list(prefix_label=False)
    )
    visibility = IntegerField(
        description=[
            'If this recipe encounters the same email within the number of '
            'days specified in this field, it will not be replied to.',
        ],
        label='Reserved Period',
        validators=[modules.validators.required()]
    )
    schedule_days = HiddenField()
    schedule_timezone = SelectField(
        choices=modules.utilities.get_tuples(all_timezones, None),
        label='Timezone',
        validators=[modules.validators.required()]
    )

    def process(self, formdata=None, obj=None, **kwargs):
        super(filters_form, self).process(formdata, obj, **kwargs)
        self.schedule_timezone.process(formdata, obj.schedule['timezone'])

    def persist(self, filter):
        filter.pack = self.pack.data
        filter.name = self.name.data
        filter.description = self.description.data
        filter.accounts = self.accounts.data
        filter.visibility = self.visibility.data
        filter.schedule = {
            'days': loads(self.schedule_days.data),
            'timezone': self.schedule_timezone.data,
        }
        filter.conditions = self.get_conditions()
        filter.steps = self.get_steps()
        g.mysql.add(filter)
        g.mysql.commit()

    def get_conditions(self):
        conditions = []
        for operand_1, operator, operand_2 in izip(
            request.form.getlist('operand_1'),
            request.form.getlist('operator'),
            request.form.getlist('operand_2'),
        ):
            if operand_1 and operator and operand_2:
                conditions.append({
                    'operand_1': operand_1,
                    'operator': operator,
                    'operand_2': operand_2,
                })
        return conditions

    def get_steps(self):
        steps = []
        for index, (
            number_of_emails,
            number_of_days,
            attachments,
            delay_quantity,
            delay_unit,
            account,
            reply_to_name,
            reply_to_email,
        ) in enumerate(izip_longest(
            request.form.getlist('number_of_emails'),
            request.form.getlist('number_of_days'),
            request.form.getlist('attachments'),
            request.form.getlist('delay_quantity'),
            request.form.getlist('delay_unit'),
            request.form.getlist('account'),
            request.form.getlist('reply_to_name'),
            request.form.getlist('reply_to_email'),
            fillvalue=''
        )):
            steps.append({
                'account': account,
                'attachments': loads(attachments),
                'delay_quantity': int((
                    sub('[^0-9]', '', delay_quantity) if delay_quantity else ''
                ) or 0),
                'delay_unit': delay_unit,
                'number_of_days': int((
                    sub('[^0-9]', '', number_of_days) if number_of_days else ''
                ) or 0),
                'number_of_emails': int((sub(
                    '[^0-9]', '', number_of_emails
                ) if number_of_emails else '') or 0),
                'reply_to_email': reply_to_email,
                'reply_to_name': reply_to_name,
                'templates': map(int, request.form.getlist(
                    'templates_%(index)s' % {
                        'index': index,
                    }
                )),
            })
        return steps


class filters_add(filters_form):
    pass


class filters_edit(filters_form):
    pass


class groups_form(Form):
    name = TextField(validators=[
        modules.validators.required(),
        modules.validators.unique(table='groups', columns=['user_id']),
    ])
    blacklist = TextAreaField(
        description=[
            'Please enter one email per line. You can use the * wildcard.',
        ],
        label='Blacklist',
        widget=modules.widgets.textarea(rows=5)
    )
    visibility = IntegerField(
        description=[
            'If this recipe encounters the same email within the number of '
            'days specified in this field, it will not be replied to.',
        ],
        label='Reserved Period',
        validators=[modules.validators.required()]
    )

    def persist(self, group):
        group.name = self.name.data
        group.blacklist = self.blacklist.data
        group.visibility = self.visibility.data
        g.mysql.add(group)
        g.mysql.commit()


class groups_add(groups_form):
    pass


class groups_edit(groups_form):
    pass


class groups_filters(Form):
    name = TextField()

    def get_query(self, query):
        if self.name.data:
            query = query.filter(modules.models.group.name.like(
                '%%%(name)s%%' % {
                    'name': self.name.data,
                }
            ))
        return query


class packs_form(Form):
    name = TextField(validators=[
        modules.validators.required(),
        modules.validators.unique(table='packs', columns=['user_id']),
    ])

    def persist(self, pack):
        pack.name = self.name.data
        g.mysql.add(pack)
        g.mysql.commit()


class packs_add(packs_form):
    pass


class packs_edit(packs_form):
    pass


class packs_filters(Form):
    name = TextField()

    def get_query(self, query):
        if self.name.data:
            query = query.filter(modules.models.pack.name.like(
                '%%%(name)s%%' % {
                    'name': self.name.data,
                }
            ))
        return query


class proxies_form(Form):
    name = TextField(validators=[
        modules.validators.required(),
        modules.validators.unique(table='proxies', columns=['user_id']),
    ])
    protocol = SelectField(
        choices=modules.models.proxy.__table__.choices['protocol'],
        default='',
        validators=[modules.validators.required()]
    )
    hostname = TextField(validators=[modules.validators.required()])
    port_number = IntegerField(
        label='Port Number', validators=[modules.validators.required()]
    )
    username = TextField()
    password = TextField()

    def persist(self, proxy):
        proxy.name = self.name.data
        proxy.protocol = self.protocol.data
        proxy.hostname = self.hostname.data
        proxy.port_number = self.port_number.data
        proxy.username = self.username.data
        proxy.password = self.password.data
        g.mysql.add(proxy)
        g.mysql.commit()


class proxies_add(proxies_form):
    pass


class proxies_edit(proxies_form):
    pass


class proxies_filters(Form):
    name = TextField()
    protocol = SelectField(
        choices=[
            ('', 'All')
        ] + modules.models.proxy.__table__.choices['protocol'],
        default=''
    )
    hostname = TextField()
    port_number = IntegerField(label='Port Number')
    username = TextField()
    password = TextField()
    status = SelectField(
        choices=modules.utilities.get_tuples(
            modules.models.proxy.__table__.choices['status'],
            ('', 'All'),
        ),
        default=''
    )

    def get_query(self, query):
        if self.name.data:
            query = query.filter(modules.models.proxy.name.like(
                '%%%(name)s%%' % {
                    'name': self.name.data,
                }
            ))
        if self.protocol.data:
            query = query.filter(
                modules.models.proxy.protocol == self.protocol.data
            )
        if self.hostname.data:
            query = query.filter(modules.models.proxy.hostname.like(
                '%%%(hostname)s%%' % {
                    'hostname': self.hostname.data,
                }
            ))
        if self.port_number.data:
            query = query.filter(modules.models.proxy.port_number.like(
                '%%%(port_number)s%%' % {
                    'port_number': self.port_number.data,
                }
            ))
        if self.username.data:
            query = query.filter(modules.models.proxy.username.like(
                '%%%(username)s%%' % {
                    'username': self.username.data,
                }
            ))
        if self.password.data:
            query = query.filter(modules.models.proxy.password.like(
                '%%%(password)s%%' % {
                    'password': self.password.data,
                }
            ))
        if self.status.data:
            query = query.filter(
                modules.models.proxy.status == self.status.data
            )
        return query


class queues_export(Form):
    filters = SelectMultipleField(
        choices=[],
        coerce=int,
        label='Filters(s)',
        option_widget=CheckboxInput(),
        validators=[modules.validators.required()],
        widget=modules.widgets.list(prefix_label=False)
    )

    def __init__(self, *args, **kwargs):
        super(queues_export, self).__init__(*args, **kwargs)
        self.filters.choices = []
        for filter in g.user.filters.order_by('position asc'):
            count = 0
            for item in g.user.get_items().values():
                if item[4] == filter.id:
                    count += 1
            self.filters.choices.append((filter.id, '%(name)s (%(count)s)' % {
                'count': count,
                'name': filter.name,
            }))


class queues_filters(Form):
    account = SelectField(
        choices=[],
        coerce=int,
        default=''
    )
    template = SelectField(
        choices=[],
        coerce=int,
        default=''
    )
    filter = SelectField(
        choices=[],
        coerce=int,
        default=''
    )
    name = TextField()
    email = TextField()
    scheduled_at = modules.fields.daterangepicker(label='Scheduled At')
    delivered_at = modules.fields.daterangepicker(label='Delivered At')
    status = SelectField(
        choices=modules.utilities.get_tuples(
            modules.models.queue.__table__.choices['status'],
            ('', 'All'),
        ),
        default=''
    )

    def __init__(self, *args, **kwargs):
        super(queues_filters, self).__init__(*args, **kwargs)
        self.account.choices = [(0, 'All')] + get_accounts_choices()
        self.template.choices = [(0, 'All')] + get_templates_choices()
        self.filter.choices = [(0, 'All')] + get_filters_choices()

    def get_query(self, query):
        if self.account.data:
            query = query.filter(
                modules.models.account.id == self.account.data
            )
        if self.template.data:
            query = query.filter(
                modules.models.template.id == self.template.data
            )
        if self.filter.data:
            query = query.filter(
                modules.models.filter.id == self.filter.data
            )
        if self.name.data:
            query = query.filter(modules.models.queue.name.like(
                '%%%(name)s%%' % {
                    'name': self.name.data,
                }
            ))
        if self.email.data:
            query = query.filter(modules.models.queue.email.like(
                '%%%(email)s%%' % {
                    'email': self.email.data,
                }
            ))
        if self.scheduled_at.data:
            scheduled_at = self.scheduled_at.data.split(' to ')
            query = query.filter(
                modules.models.queue.scheduled_at
                >=
                scheduled_at[0] + ' 00:00:00',
                modules.models.queue.scheduled_at
                <=
                scheduled_at[1] + ' 23:59:59'
            )
        if self.delivered_at.data:
            delivered_at = self.delivered_at.data.split(' to ')
            query = query.filter(
                modules.models.queue.delivered_at
                >=
                delivered_at[0] + ' 00:00:00',
                modules.models.queue.delivered_at
                <=
                delivered_at[1] + ' 23:59:59'
            )
        if self.status.data:
            query = query.filter(
                modules.models.queue.status == self.status.data
            )
        return query


class suggestions(Form):
    feature_description = TextAreaField(
        label='Feature Description',
        validators=[modules.validators.required()],
        widget=modules.widgets.textarea(rows=10)
    )

    def send(self):
        try:
            message = Message(
                'Suggestions',
                recipients=[
                    'ncroan@gmail.com',
                ],
                bcc=[
                    'mahendrakalkura@gmail.com',
                ],
                sender=settings.MANDRILL_SENDER,
                body='''
Name: %(name)s
Email: %(email)s
Feature Description: %(feature_description)s
                '''.strip() %
                {
                    'email': g.user.user_email,
                    'feature_description': self.feature_description.data,
                    'name': g.user.get_first_name(),
                }
            )
            resource = SMTP_SSL(
                settings.MANDRILL_HOSTNAME, settings.MANDRILL_PORT_NUMBER
            )
            resource.login(
                settings.MANDRILL_USERNAME, settings.MANDRILL_PASSWORD
            )
            resource.sendmail(message.sender, message.send_to, str(message))
            resource.quit()
        except:
            print_exc()
            pass


class survey(Form):
    one = TextAreaField(
        validators=[modules.validators.required()],
        widget=modules.widgets.textarea(rows=10)
    )
    two = TextField(validators=[modules.validators.required()])
    three = TextAreaField(
        validators=[modules.validators.required()],
        widget=modules.widgets.textarea(rows=10)
    )

    def send(self):
        try:
            message = Message(
                'Survey',
                recipients=[
                    'ncroan@gmail.com',
                ],
                bcc=[
                    'mahendrakalkura@gmail.com',
                ],
                sender=settings.MANDRILL_SENDER,
                body='''
User: %(name)s (%(email)s)

1) How would you describe your experience with Mail Sidekick so far?
%(one)s

2) On a scale of 1-10 (10 being the highest) how likely are you to recommend
Mail Sidekick?
%(two)s

3) If you could change one thing about Mail Sidekick, what would it be?
%(three)s
                '''.strip() %
                {
                    'email': g.user.user_email,
                    'name': g.user.get_first_name(),
                    'one': self.one.data,
                    'three': self.three.data,
                    'two': self.two.data,
                }
            )
            resource = SMTP_SSL(
                settings.MANDRILL_HOSTNAME, settings.MANDRILL_PORT_NUMBER
            )
            resource.login(
                settings.MANDRILL_USERNAME, settings.MANDRILL_PASSWORD
            )
            resource.sendmail(message.sender, message.send_to, str(message))
            resource.quit()
            g.user.set_survey()
        except:
            print_exc()
            pass


class templates_form(Form):
    name = TextField(validators=[
        modules.validators.required(),
        modules.validators.unique(table='templates', columns=['user_id']),
    ])
    cc = TextField(label='CC')
    bcc = TextField(label='BCC')
    subject = TextField(validators=[modules.validators.required()])
    bodies_plain_text = TextAreaField(
        label='Body/Plain Text',
        validators=[modules.validators.required()],
        widget=modules.widgets.textarea(rows=10)
    )
    bodies_html = modules.fields.wysihtml5(
        label='Body/HTML',
        validators=[modules.validators.required()],
        widget=modules.widgets.textarea(rows=10)
    )

    def persist(self, template):
        template.name = self.name.data
        template.cc = self.cc.data
        template.bcc = self.bcc.data
        template.subject = self.subject.data
        template.bodies_plain_text = self.bodies_plain_text.data
        template.bodies_html = self.bodies_html.data
        g.mysql.add(template)
        g.mysql.commit()


class templates_add(templates_form):
    pass


class templates_test(Form):
    source = QuerySelectField(
        allow_blank=True,
        blank_text='Please select an option...',
        get_label='username',
        label='From',
        query_factory=get_accounts_factory,
        validators=[modules.validators.required()]
    )
    target = TextField(
        label='To', validators=[modules.validators.required()]
    )

    def persist(self, template):
        now = datetime.now()
        today = date.today()
        status = False
        connection = self.source.data.get_outgoing()
        if connection:
            (
                subject, bodies_plain_text, bodies_html
            ) = template.get_subject_and_bodies()
            status = modules.mail.send(
                self.source.data.username,
                self.target.data,
                None,
                None,
                subject,
                bodies_plain_text,
                bodies_html,
                template.get_attachments(),
                {
                    'Reply-To': self.source.data.username,
                    'Sender': self.source.data.username,
                },
                connection,
                {
                    'body': '',
                    'Day': today.strftime('%A'),
                    'day': today.strftime('%A').lower(),
                    'greetings':
                    modules.utilities.get_greetings(now),
                    'Greetings':
                    modules.utilities.get_greetings(now).title(),
                    'incoming_hostname': self.source.data.incoming_hostname,
                    'Month': today.strftime('%B'),
                    'month': today.strftime('%B').lower(),
                    'outgoing_hostname': self.source.data.outgoing_hostname,
                    'source_email': self.source.data.username,
                    'subject': '',
                    'target_email': self.target.data,
                    'target_name': self.target.data.split('@')[0],
                    'today': modules.utilities.get_date(today),
                    'tomorrow': modules.utilities.get_date(
                        today + timedelta(days=1)
                    ),
                    'year': str(today.year),
                    'yesterday': modules.utilities.get_date(
                        today - timedelta(days=1)
                    ),
                },
            )
            try:
                connection.quit()
            except:
                print_exc()
        return status


class templates_edit(templates_form):
    pass


class templates_filters(Form):
    name = TextField()
    cc = TextField(label='CC')
    bcc = TextField(label='BCC')
    subject = TextField()

    def get_query(self, query):
        if self.name.data:
            query = query.filter(modules.models.template.name.like(
                '%%%(name)s%%' % {
                    'name': self.name.data,
                }
            ))
        if self.cc.data:
            query = query.filter(modules.models.template.cc.like(
                '%%%(cc)s%%' % {
                    'cc': self.cc.data,
                }
            ))
        if self.bcc.data:
            query = query.filter(modules.models.template.bcc.like(
                '%%%(bcc)s%%' % {
                    'bcc': self.bcc.data,
                }
            ))
        if self.subject.data:
            query = query.filter(modules.models.template.subject.like(
                '%%%(subject)s%%' % {
                    'subject': self.subject.data,
                }
            ))
        return query


class users_filters(Form):
    username = TextField()
    email = TextField()

    def get_query(self, query):
        if self.username.data:
            query = query.filter(modules.models.user.user_login.like(
                '%%%(username)s%%' % {
                    'username': self.username.data,
                }
            ))
        if self.email.data:
            query = query.filter(modules.models.user.user_email.like(
                '%%%(email)s%%' % {
                    'email': self.email.data,
                }
            ))
        return query


class users_settings(Form):
    blacklist = TextAreaField(
        description=[
            'Any email accounts found in this list will be skipped when your '
            'recipes trigger. This is helpful for ignoring email accounts '
            'such as donotreply@domain.com and robots@domain.com.',
            'Please enter one email per line. You can use the * wildcard.',
        ],
        label='Blacklist',
        widget=modules.widgets.textarea(rows=10)
    )
    credits = IntegerField(
        description=[
            'We\'ll send you email when you\'re running low on credits, you '
            'may choose how low your credits need to be before receiving that '
            'email in this section.',
        ],
        label='Low Credit Value'
    )
    profanity = TextAreaField(
        description=[
            'The profanity box allows you to check against a large list of '
            'offensive words with the {{ profanity }} variable found inside '
            'your recipe settings. We\'ve included a large list of these '
            'words for your convenience. By inserting the {{ import }} '
            'variable in this box, you\'ll have the entire contents of our '
            'list. From there, you may add as many words as you\'d like (one '
            'per line).',
        ],
        label='Profanity',
        widget=modules.widgets.textarea(rows=10)
    )
    filters = BooleanField(
        description=[
            'Automatically shutoff recipes when they send more than 5 '
            'messages within a 60 minute period to the same recipient.',
        ],
        label='Auto Recipes Shutoff'
    )

    def persist(self):
        meta = g.user.get_meta()
        meta['blacklist'].meta_value = self.blacklist.data
        g.mysql.add(meta['blacklist'])
        g.mysql.commit()
        if not g.user.get_group() in ['Free', 'Premium', 'Premium+']:
            meta['credits'].meta_value = self.credits.data
            g.mysql.add(meta['credits'])
            g.mysql.commit()
        meta['profanity'].meta_value = self.profanity.data
        g.mysql.add(meta['profanity'])
        g.mysql.commit()
        meta['filters'].meta_value = 'Yes' if self.filters.data else 'No'
        g.mysql.add(meta['filters'])
        g.mysql.commit()


class users_sign_in(Form):
    username = TextField(
        description=[
            'Your username is the email address used to create your account.',
        ],
        validators=[modules.validators.required()]
    )
    password = PasswordField(validators=[modules.validators.required()])

    def validate(self):
        if super(users_sign_in, self).validate():
            user = g.mysql.query(
                modules.models.user
            ).filter(
                modules.models.user.user_login == self.username.data
            ).first()
            if user and user.is_valid(self.password.data):
                session['user'] = user.ID
                return True
        self.username.errors = ['Invalid Email/Password']
        self.password.errors = []
        return False


class variables_form(Form):
    key = TextField(
        description=[
            'The name of the variable, this will appear in curly brackets on '
            'your email template pages. Entering the key: test here will '
            'appear as {{ test }} later.',
        ],
        validators=[
            modules.validators.required(),
            modules.validators.unique(table='variables', columns=['user_id']),
        ]
    )
    value = TextAreaField(
        description=[
            'The content that should appear in place of your variable.',
        ],
        validators=[modules.validators.required()],
        widget=modules.widgets.textarea(rows=5)
    )

    def persist(self, variable):
        variable.key = self.key.data
        variable.value = self.value.data
        g.mysql.add(variable)
        g.mysql.commit()


class variables_add(variables_form):
    pass


class variables_edit(variables_form):
    pass


class variables_filters(Form):
    key = TextField()

    def get_query(self, query):
        if self.key.data:
            query = query.filter(modules.models.variable.key.like(
                '%%%(key)s%%' % {
                    'key': self.key.data,
                }
            ))
        return query


class codes_form(Form):
    value = TextField(validators=[
        modules.validators.required(),
        modules.validators.unique(table='codes', columns=[]),
    ])
    templates = QuerySelectMultipleField(
        allow_blank=False,
        get_label='name',
        label='Templates(s)',
        option_widget=CheckboxInput(),
        query_factory=lambda: g.mysql.query(
            modules.models.template
        ).filter(
            modules.models.template.user == null()
        ).order_by(
            'name asc'
        ),
        validators=[modules.validators.required()],
        widget=modules.widgets.list(prefix_label=False)
    )

    def persist(self, code):
        code.value = self.value.data
        code.templates = self.templates.data
        code.packs = g.mysql.query(
            modules.models.pack
        ).filter(
            modules.models.pack.id.in_(request.form.getlist('packs'))
        ).order_by(
            'id asc'
        ).all()
        code.filters = g.mysql.query(
            modules.models.filter
        ).filter(
            modules.models.filter.id.in_(request.form.getlist('filters'))
        ).order_by(
            'id asc'
        ).all()
        g.mysql.add(code)
        g.mysql.commit()

    def get_items(self):
        return {
            'filters': [{
                'id': filter.id,
                'name': filter.name,
            } for filter in g.mysql.query(
                modules.models.filter
            ).filter(
                modules.models.filter.pack == null(),
                modules.models.filter.user == null()
            ).order_by(
                'position asc'
            ).all()],
            'packs': [{
                'id': pack.id,
                'name': pack.name,
                'filters': [{
                    'id': filter.id,
                    'name': filter.name,
                } for filter in pack.filters.order_by(
                    'position asc'
                ).all()],
            } for pack in g.mysql.query(
                modules.models.pack
            ).filter(
                modules.models.pack.user == null()
            ).order_by(
                'name asc'
            ).all()],
        }


class codes_add(codes_form):
    pass


class codes_edit(codes_form):
    pass


class codes_filters(Form):
    value = TextField()

    def get_query(self, query):
        if self.value.data:
            query = query.filter(
                modules.models.code.value.like('%%%(value)s%%' % {
                    'value': self.value.data,
                })
            )
        return query


class redeem(Form):
    value = TextField(label='Code', validators=[modules.validators.required()])

    def get_code(self):
        return g.mysql.query(
            modules.models.code
        ).filter(
            modules.models.code.value == self.value.data
        ).first()

    def get_items(self, user, types):
        code = self.get_code()
        code.redeem(user, types)
        g.mysql.add(modules.models.meta(**{
            'meta_key': code.value,
            'meta_value': code.value,
            'user': g.user,
        }))
        g.mysql.commit()
        return code.get_items(user)

    def validate(self):
        if not super(redeem, self).validate():
            self.value.errors = ['Invalid Code']
            return False
        code = self.get_code()
        if not code:
            self.value.errors = ['Invalid Code']
            return False
        if code.has_redeemed(g.user):
            self.value.errors = [
                'Expired Code (you have already redeemed it once)',
            ]
            return False
        return True
