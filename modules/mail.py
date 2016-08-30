# -*- coding: utf-8 -*-

from flask.ext.mail import Message
from mimetypes import init, types_map
from traceback import print_exc


def interpolate(string, variables):
    for key, value in variables.iteritems():
        string = string.replace('{{ %(key)s }}' % {
            'key': key,
        }, value)
    return string


def send(
    source,
    target,
    cc,
    bcc,
    subject,
    bodies_plain_text,
    bodies_html,
    attachments,
    headers,
    connection,
    variables
):
    if connection:
        subject = interpolate(subject, variables)
        bodies_plain_text = interpolate(bodies_plain_text, variables)
        bodies_html = interpolate(bodies_html, variables)
        message = Message(
            subject,
            sender=source,
            recipients=[target],
            cc=cc,
            bcc=bcc,
            body=bodies_plain_text,
            html=bodies_html,
            extra_headers=headers,
        )
        if attachments:
            init()
            for attachment in attachments:
                contents = ''
                with open(attachment['resource'], 'rb') as resource:
                    contents = resource.read()
                message.attach(
                    attachment['name'],
                    types_map[attachment['extension']]
                    if attachment['extension'] in types_map
                    else 'application/octet-stream',
                    contents
                )
        try:
            connection.sendmail(message.sender, message.send_to, str(message))
            return True
        except:
            print_exc()
    return False
