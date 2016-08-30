# -*- coding: utf-8 -*-

from cgi import escape
from wtforms.compat import text_type
from wtforms.widgets import HTMLString, ListWidget, html_params


class list(ListWidget):

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        html = []
        html.append(u'<%(tag)s>' % {
            'tag': self.html_tag,
        })
        for item in field:
            parameters = {
                'left': item(),
                'right': item.label.text,
            }
            if self.prefix_label:
                parameters = {
                    'left': item.label.text,
                    'right': item(),
                }
            html.append(
                u'<li><label>%(left)s %(right)s</label></li>' % parameters
            )
        html.append(u'</%(tag)s>' % {
            'tag': self.html_tag,
        })
        return HTMLString(u''.join(html))


class textarea(object):

    def __init__(self, *args, **kwargs):
        self.rows = kwargs['rows']

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('rows', self.rows)
        return HTMLString('<textarea %(html_params)s>%(value)s</textarea>' % {
            'html_params': html_params(name=field.name, **kwargs),
            'value': escape(text_type(field._value())),
        })
