# -*- coding: utf-8 -*-

from datetime import datetime
from flask import Flask, g, redirect, send_from_directory, session, url_for
from flask_debugtoolbar import DebugToolbarExtension
from flask.ext.assets import Bundle, Environment
from jinja2 import Markup, escape
from os.path import abspath, dirname, join
from re import compile

from sqlalchemy.event import listen
from sqlalchemy.orm import scoped_session, sessionmaker

import modules.database
import modules.decorators
import modules.forms

import sections.administrators
import sections.others
import sections.users

import settings


def url_for_(rule, **kwargs):
    kwargs.setdefault('_external', True)
    return url_for(rule, **kwargs)

application = Flask(
    __name__,
    static_folder=join(abspath(dirname(__file__)), 'resources')
)

application.config.from_object(settings)

application.jinja_env.add_extension('jinja2.ext.do')
application.jinja_env.add_extension('jinja2.ext.loopcontrols')
application.jinja_env.add_extension('jinja2.ext.with_')
application.jinja_env.add_extension(
    'vendors.jinja2htmlcompress.SelectiveHTMLCompress'
)

application.jinja_env.globals['url_for'] = url_for_

application.register_blueprint(
    sections.administrators.blueprint, url_prefix='/administrators'
)
application.register_blueprint(sections.others.blueprint, url_prefix='/others')
application.register_blueprint(sections.users.blueprint, url_prefix='/users')

assets = Environment(application)

assets.cache = False
assets.debug = True if settings.is_mahendra() else False
assets.directory = application.static_folder
assets.manifest = 'json:assets/versions.json'
assets.url = application.static_url_path
assets.url_expire = True
assets.versions = 'timestamp'

assets.register('stylesheets', Bundle(
    'vendors/bootstrap/css/bootstrap.css',
    'vendors/bootstrap-daterangepicker/daterangepicker.css',
    'vendors/bootstrap-tour/css/bootstrap-tour.css',
    'vendors/slider/css/slider.css',
    'vendors/bootstrap-wysihtml5/bootstrap-wysihtml5.css',
    'vendors/font-awesome/css/font-awesome.css',
    'vendors/font-awesome/css/font-awesome-ie7.css',
    'vendors/flipclock/flipclock.css',
    'stylesheets/all.css',
    filters=None if settings.is_mahendra() else 'cssmin,cssrewrite',
    output='assets/compressed.css'
))
assets.register('javascripts', Bundle(
    'vendors/jquery.js',
    'vendors/jquery.cookie.js',
    'vendors/flipclock/flipclock.js',
    'vendors/angular.js',
    'vendors/moment.js',
    'vendors/wysihtml5/wysihtml5.js',
    'vendors/bootstrap/js/bootstrap.js',
    'vendors/bootstrap-daterangepicker/daterangepicker.js',
    'vendors/bootstrap-filestyle.js',
    'vendors/bootstrap-hover-dropdown.js',
    'vendors/slider/js/bootstrap-slider.js',
    'vendors/bootstrap-tour/js/bootstrap-tour.js',
    'vendors/bootstrap-wysihtml5/bootstrap-wysihtml5.js',
    'javascripts/all.js',
    filters=None if settings.is_mahendra() else 'rjsmin',
    output='assets/compressed.js'
))

DebugToolbarExtension(application)


@application.before_request
def before_request():
    g.mahendra = settings.is_mahendra()
    g.mysql = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=modules.database.engine,
        expire_on_commit=True
    ))()
    g.settings = modules.models.option.get_dictionary()
    g.year = datetime.now().strftime('%Y')
    session.permanent = True
    listen(g.mysql, 'after_flush', modules.models.after_flush)
    listen(g.mysql, 'before_flush', modules.models.before_flush)


@application.after_request
def after_request(response):
    try:
        g.mysql.commit()
    except:
        g.mysql.rollback()
    g.mysql.close()
    return response


@application.route('/')
def dashboard():
    return redirect(url_for('users.dashboard_overview'))


@application.route('/404')
@application.errorhandler(404)
def errors_404(error=None):
    return sections.others.errors_404(error)


@application.route('/500')
@application.errorhandler(500)
def errors_500(error=None):
    return sections.others.errors_500(error)


@application.route('/favicon.ico')
def favicon():
    return send_from_directory(join(
        application.root_path, 'resources', 'images'
    ), 'favicon.ico')


@application.template_filter('format_date')
def format_date(value):
    return modules.utilities.get_date(value)


@application.template_filter('format_date_and_time')
def format_date_and_time(value):
    return modules.utilities.get_date_and_time(value)


@application.template_filter('format_dumps')
def format_dumps(value):
    return modules.utilities.get_dumps(value)


@application.template_filter('format_float')
def format_float(value):
    return modules.utilities.get_float(value)


@application.template_filter('format_integer')
def format_integer(value):
    return modules.utilities.get_integer(value)


@application.template_filter('format_paragraph')
def format_paragraph(value):
    return Markup(
        '\n\n'.join(
            '<p>%(paragraph)s</p>' % {
                'paragraph': paragraph.replace('\n', '<br>\n')
            }
            for paragraph in compile(
                r'(?:\r\n|\r|\n){2,}'
            ).split(escape(value))
        )
    )

if __name__ == '__main__':
    application.run()
