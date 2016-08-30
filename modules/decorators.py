# -*- coding: utf-8 -*-

from flask import g, redirect, request, session, url_for
from functools import wraps

import modules.log
import modules.timer


def profile(indent):
    def decorator(function):
        @wraps(function)
        def decorated_function(*args, **kwargs):
            modules.log.write(10, '%(function)s()' % {
                'function': function.__name__
            }, indent)
            modules.timer.start(function.__name__)
            output = function(*args, **kwargs)
            modules.timer.stop(function.__name__)
            modules.log.write(10, '%(seconds).3f seconds' % {
                'seconds': modules.timer.get_seconds(function.__name__),
            }, indent)
            return output
        return decorated_function
    return decorator


def requires_administrator(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if g.administrator:
            return function(*args, **kwargs)
        if 'administrator' in session:
            del session['administrator']
        return redirect(url_for('administrators.sign_in', next=request.url))
    return decorated_function


def requires_user(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if g.user:
            return function(*args, **kwargs)
        if 'user' in session:
            del session['user']
        return redirect(url_for('users.sign_in', next=request.url))
    return decorated_function
