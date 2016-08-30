# -*- coding: utf-8 -*-

from flask import Blueprint, render_template

blueprint = Blueprint('others', __name__)


@blueprint.route('/')
def dashboard():
    return render_template('others/views/dashboard.html')


@blueprint.route('/404')
def errors_404(error=None):
    return render_template('others/views/404.html'), 404


@blueprint.route('/403')
def errors_403(error=None):
    return render_template('others/views/403.html'), 403


@blueprint.route('/500')
def errors_500(error=None):
    return render_template('others/views/500.html'), 500
