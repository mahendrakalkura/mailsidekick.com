# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
from email import message_from_string
from flask import g, url_for
from flask.ext.mail import Message
from imaplib import IMAP4, IMAP4_SSL
from poplib import POP3, POP3_SSL
from re import compile, sub
from shutil import copy2
from smtplib import SMTP_SSL
from sqlalchemy.sql import null
from traceback import print_exc

import modules.decorators
import modules.log
import modules.models
import modules.utilities

import settings

patterns = {
    'email': compile(r'<(.*?)>'),
    'name': compile(r'"(.*?)"'),
    'uid': compile(r'UID\s*?(\d+)'),
}


@modules.decorators.profile(0)
def accounts():
    for user in g.mysql.query(modules.models.user).order_by('ID asc').all():
        if not user.is_active():
            continue
        if g.mysql.query(
            modules.models.account
        ).filter(
            modules.models.account.user == user,
            modules.models.account.username == 'placeholder@mailsidekick.com'
        ).order_by(
            'id asc'
        ).first():
            continue
        g.mysql.add(modules.models.account(**{
            'blacklist': '',
            'connections': {
                'incoming': True,
                'outgoing': True,
            },
            'description': '',
            'incoming_hostname': 'imap.mailsidekick.com',
            'incoming_port_number': '000',
            'incoming_use_ssl': 'Yes',
            'outgoing_hostname': 'smtp.sidekick.com',
            'outgoing_port_number': '000',
            'outgoing_use_ssl': 'Yes',
            'outgoing_use_tls': 'Yes',
            'password': 'password',
            'status': 'On',
            'user': user,
            'username': 'placeholder@mailsidekick.com',
        }))
        g.mysql.commit()
    '''
    for account in g.mysql.query(
        modules.models.account
    ).order_by(
        'id asc'
    ).all():
        if (
            account.connections['incoming'] != 'On'
            or
            account.connections['outgoing'] != 'On'
        ):
            account.update_connections()
    '''


@modules.decorators.profile(0)
def codes():
    instance = g.mysql.query(modules.models.code).filter(
        modules.models.code.value == 'DEMO'
    ).first()
    if not instance:
        return
    for user in g.mysql.query(modules.models.user).order_by('ID asc').all():
        if not user.is_active():
            continue
        if not instance.has_redeemed(user):
            g.mysql.add(modules.models.meta(**{
                'meta_key': instance.value,
                'meta_value': instance.value,
                'user': user,
            }))
            g.mysql.commit()
        instance.redeem(user, ['filters', 'packs', 'templates'])


@modules.decorators.profile(0)
def credits():
    for user in g.mysql.query(modules.models.user).order_by('ID asc').all():
        if not user.is_active():
            continue
        if user.get_group() in ['Free', 'Premium', 'Premium+']:
            continue
        credits = user.get_credits()
        if credits['remaining'] < credits['settings']:
            message = Message(
                'Your email credits are getting low.',
                recipients=[
                    user.user_email,
                ],
                bcc=[
                    'mahendrakalkura@gmail.com'
                ],
                sender=settings.MANDRILL_SENDER,
                body='''
Your credit balance is running low (%(credits)s). You may obtain additional
credits here (http://mailsidekick.com/get/credits) to avoid a pause in your
campaign. Please note that credits will be automatically applied to your
account based on your subscription type when your next billing month begins.

Thank you for sending with Mail Sidekick.
                '''.strip() %
                {
                    'credits':
                    modules.utilities.get_integer(credits['remaining']),
                }
            )
            resource = SMTP_SSL(
                settings.MANDRILL_HOSTNAME, settings.MANDRILL_PORT_NUMBER
            )
            resource.login(
                settings.MANDRILL_USERNAME, settings.MANDRILL_PASSWORD
            )
            resource.sendmail(
                message.sender, message.send_to, str(message)
            )
            resource.quit()


@modules.decorators.profile(0)
def filters():
    timestamp = datetime.now() - timedelta(hours=1)
    for user in g.mysql.query(modules.models.user).order_by('ID asc').all():
        if not user.is_active():
            continue
        modules.log.write(10, user.get_first_name(), 1)
        if not user.get_settings()['filters'] == 'Yes':
            continue
        for filter in user.filters.filter(
            modules.models.filter.status == 'On'
        ).order_by(
            'id asc'
        ).all():
            modules.log.write(10, filter.name, 2)
            for email in user.get_items():
                count = filter.queues.filter(
                    modules.models.queue.email == email,
                    modules.models.queue.status == 'Delivered',
                    modules.models.queue.delivered_at >= timestamp
                ).order_by(
                    'id asc'
                ).count()
                modules.log.write(10, email, 3)
                modules.log.write(10, count, 4)
                if not count > 5:
                    continue
                filter.status = 'Off'
                g.mysql.add(filter)
                g.mysql.commit()
                for queue in filter.queues.filter(
                    modules.models.queue.status == 'Scheduled'
                ).order_by(
                    'id asc'
                ).all():
                    queue.status = 'Backlogged'
                    g.mysql.add(queue)
                    g.mysql.commit()
                message = Message(
                    'Auto Recipes Shutoff - %(filter_name)s' % {
                        'filter_name': filter.name,
                    },
                    recipients=[
                        user.user_email,
                    ],
                    bcc=[
                        'mahendrakalkura@gmail.com'
                    ],
                    sender=settings.MANDRILL_SENDER,
                    body='''
Your recipe %(filter_name)s has sent %(count)s emails to %(email)s within the
last 60 minutes. As a safety measure we have temporarily disabled it to prevent
further messages from sending. You may re-enable this recipe at any time by
visiting your recipes page located here: %(filters_overview)s

Additionally, if you wish to disable this safety measure you may do so in the
settings page located here: %(settings)s

Mail Sidekick Staff'''.strip() %
                    {
                        'count': count,
                        'email': email,
                        'filter_name': filter.name,
                        'filters_overview':
                        url_for('users.filters_overview', _external=True),
                        'settings': url_for('users.settings', _external=True),
                    }
                )
                resource = SMTP_SSL(
                    settings.MANDRILL_HOSTNAME, settings.MANDRILL_PORT_NUMBER
                )
                resource.login(
                    settings.MANDRILL_USERNAME, settings.MANDRILL_PASSWORD
                )
                resource.sendmail(
                    message.sender, message.send_to, str(message)
                )
                resource.quit()


@modules.decorators.profile(0)
def incoming():
    now = datetime.now()
    for user in g.mysql.query(modules.models.user).order_by('ID asc').all():
        if not user.is_active():
            continue
        modules.log.write(10, user.get_first_name(), 1)
        profanity = user.get_profanity()
        for account in user.accounts.filter(
            modules.models.account.status == 'On'
        ).order_by(
            'username asc'
        ).all():
            if account.username == 'placeholder@mailsidekick.com':
                continue
            modules.log.write(10, account.username, 2)
            items = []
            if not settings.is_mahendra():
                connection = account.get_incoming()
                if not connection:
                    continue
                if (
                    isinstance(connection, IMAP4)
                    or
                    isinstance(connection, IMAP4_SSL)
                ):
                    try:
                        connection.select()
                        _, numbers = connection.search(None, 'UnSeen')
                        if not numbers:
                            return
                        if not len(numbers):
                            return
                        for number in numbers[0].strip().split(' '):
                            number = number.strip()
                            if not number:
                                continue
                            modules.log.write(10, number, 3)
                            uid = modules.crontab.get_uid(
                                connection.fetch(number, '(UID)')[1]
                            )
                            if not uid:
                                continue
                            modules.log.write(10, uid, 3)
                            contents = None
                            try:
                                _, contents = connection.uid(
                                    'fetch', uid, '(RFC822)'
                                )
                            except:
                                pass
                            item = get_imap4(contents) if contents else None
                            if not item:
                                try:
                                    connection.uid(
                                        'store', uid, '-FLAGS', '(\Seen)'
                                    )
                                except:
                                    print_exc()
                                continue
                            items.append(item)
                    except:
                        print_exc()
                if (
                    isinstance(connection, POP3)
                    or
                    isinstance(connection, POP3_SSL)
                ):
                    try:
                        contents = connection.stat()
                        if not contents:
                            return
                        if not len(contents):
                            return
                        if not contents[0]:
                            return
                        _, numbers, _ = connection.list()
                        if not numbers:
                            return
                        if not len(numbers):
                            return
                        for number in numbers:
                            number = number.strip()
                            if not number:
                                continue
                            number = number.split(' ')[0]
                            modules.log.write(10, number, 3)
                            _, contents, _ = connection.retr(number)
                            item = get_pop3(contents)
                            if not item:
                                continue
                            items.append(item)
                    except:
                        print_exc()
                try:
                    connection.quit()
                except:
                    try:
                        connection.close()
                        connection.logout()
                    except:
                        pass
            else:
                items = [{
                    'attachments': [{
                        'prefix': '1',
                        'size': 3,
                        'suffix': '2',
                    }],
                    'body': '1',
                    'email': '1@1.com',
                    'message_id': '1',
                    'name': '1',
                    'subject': '1',
                }, {
                    'attachments': [],
                    'body': '2',
                    'email': '2@2.com',
                    'message_id': '2',
                    'name': '2',
                    'subject': '2',
                }, {
                    'attachments': [],
                    'body': '3',
                    'email': '3@3.com',
                    'message_id': '3',
                    'name': '3',
                    'subject': '3',
                }, {
                    'attachments': [],
                    'body': '4',
                    'email': '4@4.com',
                    'message_id': '4',
                    'name': '4',
                    'subject': '4',
                }, {
                    'attachments': [],
                    'body': '5',
                    'email': '5@5.com',
                    'message_id': '5',
                    'name': '5',
                    'subject': '5',
                }]
            if items:
                log = modules.models.log(**{
                    'account': account,
                })
                g.mysql.add(log)
                g.mysql.commit()
                g.mysql.refresh(log)
                for item in items:
                    for filter in account.filters.filter(
                        modules.models.filter.status == 'On'
                    ).order_by(
                        'position asc'
                    ).all():
                        if filter.is_valid(
                            profanity,
                            item['email'],
                            item['subject'],
                            item['body']
                        ):
                            item['filter'] = filter
                            item['log'] = log
                            item['status'], item['step'] = get_status_and_step(
                                filter, item
                            )
                            del item['attachments']
                            queue = modules.models.queue(**item)
                            g.mysql.add(queue)
                            g.mysql.commit()
                            g.mysql.refresh(queue)
                            if queue.status == 'Scheduled':
                                break
    for queue in g.mysql.query(
        modules.models.queue
    ).filter(
        modules.models.queue.status == 'Delivered'
    ).order_by(
        'id asc'
    ).all():
        if not queue.step < len(queue.filter.steps) - 1:
            continue
        step = queue.step + 1
        if g.mysql.query(
            modules.models.queue
        ).filter(
            modules.models.queue.filter == queue.filter,
            modules.models.queue.email == queue.email,
            modules.models.queue.step == step
        ).order_by(
            'id asc'
        ).count():
            continue
        if not queue.filter.steps[step]['number_of_emails'] == 0:
            continue
        if not queue.delivered_at + timedelta(
            days=queue.filter.steps[step]['number_of_days']
        ) < now:
            continue
        g.mysql.add(modules.models.queue(**{
            'body': queue.body,
            'email': queue.email,
            'filter': queue.filter,
            'log': queue.log,
            'message_id': queue.message_id,
            'name': queue.name,
            'status': 'Scheduled',
            'step': step,
            'subject': queue.subject,
            'template': queue.template,
        }))
        g.mysql.commit()


@modules.decorators.profile(0)
def outgoing(plans):
    for queue in g.mysql.query(
        modules.models.queue
    ).filter(
        modules.models.queue.status == 'Scheduled'
    ).all():
        if not queue.log.account.user.is_active():
            modules.log.write(10, '%(id)09d %(status)s' % {
                'id': queue.id,
                'status': 'user.is_active() == False',
            }, 1)
            continue
        if not queue.log.account.user.get_group() in plans:
            continue
        if not queue.log.account.status == 'On':
            modules.log.write(10, '%(id)09d %(status)s' % {
                'id': queue.id,
                'status': "account.status == 'Off'",
            }, 1)
            continue
        (
            subject, bodies_plain_text, bodies_html
        ) = queue.template.get_subject_and_bodies()
        now = datetime.now()
        today = date.today()
        status = 'N/A'
        if queue.get_scheduled_for()[0] < now:
            status = 'Not OK'
            account = queue.get_account()
            if not account.connections['outgoing'] in ['On', True]:
                modules.log.write(10, '%(id)09d %(status)s' % {
                    'id': queue.id,
                    'status':
                    "account.connections['outgoing'] == %(outgoing)s" % {
                        'outgoing': account.connections['outgoing'],
                    },
                }, 1)
                continue
            if not account.user.get_group() in [
                'Free',
                'Premium',
                'Premium+',
            ]:
                credits = account.user.get_credits()
                if credits['remaining'] == 0:
                    queue.status = 'Backlogged'
                    g.mysql.add(queue)
                    g.mysql.commit()
                    continue
            if modules.mail.send(
                account.username,
                queue.email,
                queue.template.cc,
                queue.template.bcc,
                subject,
                bodies_plain_text,
                bodies_html,
                queue.template.get_attachments(),
                {
                    'In-Reply-To': queue.message_id,
                    'Reply-To': queue.get_reply_to(),
                    'Sender': queue.get_reply_to(),
                },
                account.get_outgoing(),
                {
                    'body': queue.body,
                    'Day': today.strftime('%A'),
                    'day': today.strftime('%A').lower(),
                    'greetings': modules.utilities.get_greetings(now),
                    'Greetings': modules.utilities.get_greetings(now).title(),
                    'incoming_hostname': queue.log.account.incoming_hostname,
                    'Month': today.strftime('%B'),
                    'month': today.strftime('%B').lower(),
                    'source_email': queue.log.account.username,
                    'subject': queue.subject,
                    'outgoing_hostname': account.outgoing_hostname,
                    'target_email': queue.email,
                    'target_name': queue.name,
                    'today': modules.utilities.get_date(today),
                    'tomorrow': modules.utilities.get_date(
                        today + timedelta(days=1)
                    ),
                    'year': str(today.year),
                    'yesterday': modules.utilities.get_date(
                        today - timedelta(days=1)
                    ),
                }
            ):
                queue.delivered_at = now
                queue.status = 'Delivered'
                g.mysql.add(queue)
                g.mysql.commit()
                status = 'OK'
            modules.log.write(10, '%(id)09d %(status)s' % {
                'id': queue.id,
                'status': status,
            }, 1)


@modules.decorators.profile(0)
def proxies():
    for proxy in g.mysql.query(
        modules.models.proxy
    ).order_by(
        'id asc'
    ).all():
        if proxy.status == 'May Be':
            proxy.update_status()


@modules.decorators.profile(0)
def templates():
    meta_values = {
        'Advanced+': [18],
        'Premium+': [17],
        'Starter+': [19],
    }
    meta_key = 'upsell'
    for user in g.mysql.query(modules.models.user).order_by('ID asc').all():
        if not user.is_active():
            continue
        meta_value = user.get_group()
        ids = []
        try:
            ids = meta_values[meta_value]
        except:
            pass
        if not ids:
            continue
        if g.mysql.query(
            modules.models.meta
        ).filter(
            modules.models.meta.meta_key == meta_key,
            modules.models.meta.meta_value == meta_value,
            modules.models.meta.user == user
        ).order_by(
            'umeta_id asc'
        ).first():
            continue
        for template in g.mysql.query(
            modules.models.template
        ).filter(
            modules.models.template.id.in_(ids),
            modules.models.template.user == null()
        ).order_by(
            'name asc'
        ).all():
            dictionary = template.to_dictionary()
            del dictionary['id']
            dictionary['user'] = user
            instance = modules.models.template(**dictionary)
            g.mysql.add(instance)
            g.mysql.commit()
            g.mysql.refresh(instance)
            path = instance.get_path()
            for attachment in template.get_attachments():
                copy2(attachment['resource'], path)
        g.mysql.add(modules.models.meta(**{
            'meta_key': meta_key,
            'meta_value': meta_value,
            'user': user,
        }))
        g.mysql.commit()


@modules.decorators.profile(0)
def test():

    items = [{
        'incoming_hostname': 'imap.mail.yahoo.com',
        'incoming_port_number': '993',
        'incoming_use_ssl': 'Yes',
        'outgoing_hostname': 'smtp.mail.yahoo.com',
        'outgoing_port_number': '465',
        'outgoing_use_ssl': 'Yes',
        'outgoing_use_tls': 'No',
        'password': 'Machine123!!',
        'username': 'robocroan@yahoo.com',
    }, {
        'incoming_hostname': 'imap.aol.com',
        'incoming_port_number': '993',
        'incoming_use_ssl': 'Yes',
        'outgoing_hostname': 'smtp.aol.com',
        'outgoing_port_number': '587',
        'outgoing_use_ssl': 'No',
        'outgoing_use_tls': 'Yes',
        'password': 'Machine123!!',
        'username': 'robotcroan@aol.com',
    }, {
        'incoming_hostname': 'pop3.live.com',
        'incoming_port_number': '995',
        'incoming_use_ssl': 'Yes',
        'outgoing_hostname': 'smtp.live.com',
        'outgoing_port_number': '587',
        'outgoing_use_ssl': 'No',
        'outgoing_use_tls': 'Yes',
        'password': 'Machine123!!',
        'username': 'robotcroan@live.com',
    }, {
        'incoming_hostname': 'imap.gmail.com',
        'incoming_port_number': '993',
        'incoming_use_ssl': 'Yes',
        'outgoing_hostname': 'smtp.gmail.com',
        'outgoing_port_number': '465',
        'outgoing_use_ssl': 'Yes',
        'outgoing_use_tls': 'No',
        'password': 'Machine123!!',
        'username': 'robotcroan@gmail.com',
    }]
    proxy = {
        'hostname': '68.171.110.193',
        'password': 'ryjeianrlv',
        'port_number': '21230',
        'protocol': '3',
        'username': 'normancroa',
    }
    subject = 'Lorem ipsum dolor sit amet.'
    bodies_plain_text = '''
Lorem ipsum dolor sit amet, cu sit illud adipisci, ei posse disputationi ius,
est omnesque voluptaria in. His cu nominati assueverit, vim no tollit quodsi,
ei constituto eloquentiam consectetuer sit. Deleniti maluisset an duo. Usu ex
ipsum mazim expetendis. Ut alia stet mundi per, ne audiam splendide usu. Ea
inani mazim melius mei.

Mel ut dicam facete, pro delicata partiendo adolescens at, at sonet homero vim.
Ius prompta corpora petentium ad, imperdiet adipiscing quo ne. Aliquando
constituto definitionem no nec, ea labore consetetur necessitatibus sea. Cum et
inani necessitatibus, duo ullum laoreet facilis ex. Ea sale modus conceptam
eos. Te ius fierent adolescens, adhuc velit fuisset quo ne, te nominati
pertinacia mnesarchum nec.

Ei his legendos partiendo, vis vide appellantur an, utinam semper in sea. Inani
laudem admodum mea ad, et mel dico ludus. Vivendo adipisci facilisis eu mea.
Sea agam causae alterum ad. Pri in sale constituto scripserit, vis lorem
honestatis et.
    '''.strip()
    bodies_html = '''
<html>
    <head>
    </head>
    <body>
        <p>
            Lorem ipsum dolor sit amet, cu sit illud adipisci, ei posse
            disputationi ius, est omnesque voluptaria in. His cu nominati
            assueverit, vim no tollit quodsi, ei constituto eloquentiam
            consectetuer sit. Deleniti maluisset an duo. Usu ex ipsum mazim
            expetendis. Ut alia stet mundi per, ne audiam splendide usu. Ea
            inani mazim melius mei.
        </p>
        <p>
            Mel ut dicam facete, pro delicata partiendo adolescens at, at sonet
            homero vim. Ius prompta corpora petentium ad, imperdiet adipiscing
            quo ne. Aliquando constituto definitionem no nec, ea labore
            consetetur necessitatibus sea. Cum et inani necessitatibus, duo
            ullum laoreet facilis ex. Ea sale modus conceptam eos. Te ius
            fierent adolescens, adhuc velit fuisset quo ne, te nominati
            pertinacia mnesarchum nec.
        </p>
        <p>
            Ei his legendos partiendo, vis vide appellantur an, utinam semper
            in sea. Inani laudem admodum mea ad, et mel dico ludus. Vivendo
            adipisci facilisis eu mea. Sea agam causae alterum ad. Pri in sale
            constituto scripserit, vis lorem honestatis et.
        </p>
    </body>
</html>
    '''.strip()

    def process(account):
        status = False
        connection = account.get_incoming()
        if connection:
            status = True
        modules.log.write(
            10,
            'INCOMING = %(status)s' % {
                'status': 'Success' if status else 'Failure',
            },
            3
        )

        status = False
        connection = account.get_outgoing()
        if connection:
            status = True
        modules.log.write(
            10,
            'OUTGOING = %(status)s' % {
                'status': 'Success' if status else 'Failure',
            },
            3
        )

        modules.log.write(10, 'SEND', 3)
        for item in items:
            if item['username'] == account.username:
                continue
            status = False
            source = '"%(name)s" <%(email)s>' % {
                'email': account.username,
                'name': account.get_name(),
            }
            if modules.mail.send(
                account.username,
                item['username'],
                '',
                '',
                subject,
                bodies_plain_text,
                bodies_html,
                [],
                {
                    'Reply-To': source,
                    'Sender': source,
                },
                connection,
                {}
            ):
                status = True
            modules.log.write(
                10,
                '%(username)s = %(status)s' % {
                    'status': 'Success' if status else 'Failure',
                    'username': item['username'],
                },
                4
            )

        modules.log.write(10, 'BOUNCE = Success', 3)

    for item in items:
        modules.log.write(10, item['username'], 1)
        modules.log.write(10, 'without proxy', 2)
        account = modules.models.account(**item)
        process(account)
        modules.log.write(10, 'with proxy', 2)
        account = modules.models.account(**item)
        account.proxy = modules.models.proxy(**proxy)
        process(account)


def get_attachments(message):
    attachments = []
    if not message.get_content_maintype() == 'multipart':
        return attachments
    for index, part in enumerate(message.walk()):
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        name = part.get_filename()
        if not name:
            continue
        if '.' in name:
            prefix, suffix = name.rsplit('.', 1)
        else:
            prefix = name
            suffix = ''
        attachments.append({
            'prefix': prefix,
            'size': len(part.get_payload(decode=True)),
            'suffix': suffix,
        })
    return attachments


def get_body(message):
    body = ''
    for part in message.walk():
        if part.get_content_maintype() == 'text':
            body = part.get_payload()
            body = body.decode('quopri_codec')
            body = body.replace('\n', ' ')
            body = body.replace('\r', ' ')
            body = body.replace('\t', ' ')
            body = body.strip()
            break
    return body


def get_cleaned_string(string):
    string = string.replace('\n', ' ')
    string = string.replace('\r', ' ')
    string = string.replace('\t', ' ')
    string = sub(r'[ ]+', ' ', string)
    string = string.strip()
    return string


def get_imap4(contents):
    if not contents:
        modules.log.write(10, '#1.1', 4)
        return
    if not len(contents):
        modules.log.write(10, '#1.2', 4)
        return
    if not contents[0]:
        modules.log.write(10, '#1.3', 4)
        return
    if not len(contents[0]) >= 2:
        modules.log.write(10, '#1.4', 4)
        return
    if not contents[0][1]:
        modules.log.write(10, '#1.5', 4)
        return
    message = message_from_string(contents[0][1])
    if not message:
        modules.log.write(10, '#1.6', 4)
        return
    return get_item(message)


def get_pop3(contents):
    if not contents:
        modules.log.write(10, '#1.1', 4)
        return
    if not len(contents):
        modules.log.write(10, '#1.2', 4)
        return
    message = message_from_string('\n'.join(contents))
    if not message:
        modules.log.write(10, '#1.3', 4)
        return
    return get_item(message)


def get_item(message):

    def get_email(message):
        if 'Reply-To' in message:
            match = patterns['email'].search(message['Reply-To'])
            if match:
                return match.group(1)
            return message['Reply-To']
        if 'From' in message:
            match = patterns['email'].search(message['From'])
            if match:
                return match.group(1)
            return message['From']

    def get_name(message):
        if 'Reply-To' in message:
            match = patterns['name'].search(message['Reply-To'])
            if match:
                return match.group(1)
        if 'From' in message:
            match = patterns['name'].search(message['From'])
            if match:
                return match.group(1)

    message_id = message['Message-ID']
    if not message_id:
        modules.log.write(10, '#2.1', 4)
        return
    modules.log.write(10, message_id, 4)
    if g.mysql.query(
        modules.models.queue
    ).filter(
        modules.models.queue.message_id == message_id
    ).first():
        modules.log.write(10, '#2.2', 4)
        return
    email = get_email(message)
    modules.log.write(10, email, 4)
    name = get_name(message)
    if not name:
        name = email.split('@')[0]
    modules.log.write(10, name, 4)
    subject = message['Subject']
    if not subject:
        subject = ''
    modules.log.write(10, subject, 4)
    body = get_body(message)
    if not body:
        body = ''
    return {
        'attachments': get_attachments(message),
        'body': body,
        'email': email,
        'message_id': message_id,
        'name': name,
        'status': 'Scheduled',
        'subject': subject,
    }


def get_status_and_step(filter, item):

    def is_valid(item, step):
        count = 0
        for s in step['attachments']:
            status = False
            if s['operand_1'] == 'Count':
                try:
                    s['operand_2'] = int(s['operand_2'])
                except:
                    s['operand_2'] = 0
                    pass
                if s['operator'] == 'is greater than':
                    if s['operand_2'] > len(item['attachments']):
                        status = True
                if s['operator'] == 'is equal to':
                    if s['operand_2'] == len(item['attachments']):
                        status = True
                if s['operator'] == 'is lesser than':
                    if s['operand_2'] < len(item['attachments']):
                        status = True
                if s['operator'] == 'is not greater than':
                    if not s['operand_2'] > len(item['attachments']):
                        status = True
                if s['operator'] == 'is not equal to':
                    if not s['operand_2'] == len(item['attachments']):
                        status = True
                if s['operator'] == 'is not lesser than':
                    if not s['operand_2'] < len(item['attachments']):
                        status = True
            else:
                for i in item['attachments']:
                    if s['operand_1'] == 'Name':
                        contents = (
                            i['prefix'].lower(),
                            modules.utilities.get_filtered_list(
                                i['prefix'].lower().split(' ')
                            ),
                        )
                        if s['operator'] == 'is':
                            if s['operand_2'].lower() == contents[0]:
                                status = True
                        if s['operator'] == 'contains':
                            if s['operand_2'].lower() in contents[0]:
                                status = True
                        if s['operator'] == 'does not contain':
                            if not s['operand_2'].lower() in contents[0]:
                                status = True
                        if s['operator'] == 'has all these words':
                            if all(
                                word in contents[1]
                                for word in
                                modules.utilities.get_filtered_list(
                                    s['operand_2'].lower().split(' ')
                                )
                            ):

                                status = True
                        if s['operator'] == 'has atleast one of these words':
                            if any(
                                word in contents[1]
                                for word in
                                modules.utilities.get_filtered_list(
                                    s['operand_2'].lower().split(' ')
                                )
                            ):
                                status = True
                        if s['operator'] == 'has none of these words':
                            if not any(
                                word in contents[1]
                                for word in
                                modules.utilities.get_filtered_list(
                                    s['operand_2'].lower().split(' ')
                                )
                            ):
                                status = True
                    if s['operand_1'] == 'Extension':
                        contents = (
                            i['suffix'].lower(),
                            modules.utilities.get_filtered_list(
                                i['suffix'].lower().split(' ')
                            ),
                        )
                        if s['operator'] == 'is':
                            if s['operand_2'].lower() == contents[0]:
                                status = True
                        if s['operator'] == 'contains':
                            if s['operand_2'].lower() in contents[0]:
                                status = True
                        if s['operator'] == 'does not contain':
                            if not s['operand_2'].lower() in contents[0]:
                                status = True
                        if s['operator'] == 'has all these words':
                            if all(
                                word in contents[1]
                                for word in
                                modules.utilities.get_filtered_list(
                                    s['operand_2'].lower().split(' ')
                                )
                            ):

                                status = True
                        if s['operator'] == 'has atleast one of these words':
                            if any(
                                word in contents[1]
                                for word in
                                modules.utilities.get_filtered_list(
                                    s['operand_2'].lower().split(' ')
                                )
                            ):
                                status = True
                        if s['operator'] == 'has none of these words':
                            if not any(
                                word in contents[1]
                                for word in
                                modules.utilities.get_filtered_list(
                                    s['operand_2'].lower().split(' ')
                                )
                            ):
                                status = True
                    if s['operand_1'] == 'Size':
                        try:
                            s['operand_2'] = int(s['operand_2'])
                        except:
                            s['operand_2'] = 0
                            pass
                        if s['operator'] == 'is greater than':
                            if s['operand_2'] > i['size']:
                                status = True
                        if s['operator'] == 'is equal to':
                            if s['operand_2'] == i['size']:
                                status = True
                        if s['operator'] == 'is lesser than':
                            if s['operand_2'] < i['size']:
                                status = True
                        if s['operator'] == 'is not greater than':
                            if not s['operand_2'] > i['size']:
                                status = True
                        if s['operator'] == 'is not equal to':
                            if not s['operand_2'] == i['size']:
                                status = True
                        if s['operator'] == 'is not lesser than':
                            if not s['operand_2'] < i['size']:
                                status = True
            if status:
                count += 1
        if count == len(step['attachments']):
            return True

    now = datetime.now()
    queues = filter.queues.filter(
        modules.models.queue.email == item['email']
    ).order_by(
        'id desc'
    )
    if not queues.count():
        if is_valid(item, filter.steps[0]):
            return 'Scheduled', 0
        return 'Skipped', 0
    for account in filter.accounts.order_by('accounts.id asc').all():
        if not account.group:
            continue
        if not account.group.visibility:
            continue
        if not (
            (now - queues.first().scheduled_at).days
            >
            account.group.visibility
        ):
            return 'Skipped', queues.first().step
    if (
        now - queues.first().scheduled_at
    ).days > filter.visibility:
        if is_valid(item, filter.steps[0]):
            return 'Scheduled', 0
    if not queues.first().step < len(filter.steps) - 1:
        return 'Skipped', queues.first().step
    step = queues.first().step + 1
    if not queues.count() >= filter.steps[step]['number_of_emails']:
        return 'Skipped', queues.first().step
    if not queues.first().scheduled_at + timedelta(
        days=filter.steps[step]['number_of_days']
    ) < now:
        return 'Skipped', queues.first().step
    if is_valid(item, filter.steps[step]):
        return 'Scheduled', step
    return 'Skipped', queues.first().step


def get_uid(contents):
    if not contents:
        return
    if not len(contents):
        return
    if not contents[0]:
        return
    match = patterns['uid'].search(contents[0])
    if match:
        return int(match.group(1))
