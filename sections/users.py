# -*- coding: utf-8 -*-

from collections import OrderedDict
from cStringIO import StringIO
from csv import QUOTE_ALL, writer
from datetime import date, datetime, timedelta
from flask import (
    abort,
    Blueprint,
    flash,
    g,
    jsonify,
    redirect,
    render_template,
    request,
    Response,
    session,
    url_for
)
from sqlalchemy.sql import null

import modules.classes
import modules.database
import modules.decorators
import modules.models

blueprint = Blueprint('users', __name__)


@blueprint.before_request
def before_request():
    g.user = None
    if 'user' in session:
        g.user = g.mysql.query(modules.models.user).get(session['user'])
        if g.user and not g.user.is_active():
            return redirect(url_for('others.errors_403'))


@blueprint.route('/')
@modules.decorators.requires_user
def index():
    return redirect(url_for('users.dashboard_overview'))


@blueprint.route('/proxies/overview')
@modules.decorators.requires_user
def proxies_overview():
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'proxies',
            {},
            {
                'column': 'id',
                'direction': 'asc',
            },
            10,
            1
        )
    form = modules.forms.proxies_filters(**filters)
    query = form.get_query(g.user.proxies)
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'users/views/proxies_overview.html',
        form=form,
        order_by=order_by,
        pager=pager,
        proxies=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix]
    )


@blueprint.route('/proxies/add', methods=['GET', 'POST'])
@modules.decorators.requires_user
def proxies_add():
    form = modules.forms.proxies_add(request.form)
    form.id = 0
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(modules.models.proxy(**{
                'user': g.user,
            }))
            flash('The proxy was saved successfully.', 'success')
            return redirect(url_for('users.proxies_overview'))
        flash('The proxy was not saved successfully.', 'error')
    return render_template('users/views/proxies_add.html', form=form)


@blueprint.route('/proxies/process', methods=['GET', 'POST'])
@modules.decorators.requires_user
def proxies_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('proxies')
    if request.method == 'POST':
        modules.utilities.set_filters(
            'proxies', modules.forms.proxies_filters
        )
        if request.form['submit'] == 'verify':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    proxy = g.mysql.query(modules.models.proxy).get(id)
                    if proxy in g.user.proxies:
                        proxy.update_status()
                flash(
                    'The selected proxies were verified successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one proxy and try again.',
                    'error'
                )
        if request.form['submit'] == 'delete':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    proxy = g.mysql.query(modules.models.proxy).get(id)
                    if proxy in g.user.proxies:
                        g.mysql.delete(proxy)
                g.mysql.commit()
                flash(
                    'The selected proxies were deleted successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one proxy and try again.',
                    'error'
                )
    return redirect(url_for('users.proxies_overview'))


@blueprint.route('/proxies/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_user
def proxies_edit(id):
    proxy = g.mysql.query(modules.models.proxy).get(id)
    if not proxy in g.user.proxies:
        abort(404)
    form = modules.forms.proxies_edit(request.form, proxy)
    form.id = id
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(proxy)
            flash('The proxy was updated successfully.', 'success')
            return redirect(url_for('users.proxies_overview'))
        flash('The proxy was not updated successfully.', 'error')
    return render_template('users/views/proxies_edit.html', form=form, id=id)


@blueprint.route('/proxies/<int:id>/verify', methods=['GET', 'POST'])
@modules.decorators.requires_user
def proxies_verify(id):
    proxy = g.mysql.query(modules.models.proxy).get(id)
    if not proxy in g.user.proxies:
        abort(404)
    proxy.update_status()
    return redirect(url_for('users.proxies_overview'))


@blueprint.route('/proxies/<int:id>/delete', methods=['GET', 'POST'])
@modules.decorators.requires_user
def proxies_delete(id):
    proxy = g.mysql.query(modules.models.proxy).get(id)
    if not proxy in g.user.proxies:
        abort(404)
    if request.method == 'GET':
        return render_template('users/views/proxies_delete.html', id=id)
    if request.method == 'POST':
        g.mysql.delete(proxy)
        g.mysql.commit()
        flash('The proxy was deleted successfully.', 'success')
        return redirect(url_for('users.proxies_overview'))


@blueprint.route('/groups/overview')
@modules.decorators.requires_user
def groups_overview():
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'groups',
            {},
            {
                'column': 'id',
                'direction': 'asc',
            },
            10,
            1
        )
    form = modules.forms.groups_filters(**filters)
    query = form.get_query(g.user.groups)
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'users/views/groups_overview.html',
        form=form,
        groups=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix],
        order_by=order_by,
        pager=pager
    )


@blueprint.route('/groups/add', methods=['GET', 'POST'])
@modules.decorators.requires_user
def groups_add():
    form = modules.forms.groups_add(request.form)
    form.id = 0
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(modules.models.group(**{
                'user': g.user,
            }))
            flash('The group was saved successfully.', 'success')
            return redirect(url_for('users.groups_overview'))
        flash('The group was not saved successfully.', 'error')
    return render_template('users/views/groups_add.html', form=form)


@blueprint.route('/groups/process', methods=['GET', 'POST'])
@modules.decorators.requires_user
def groups_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('groups')
    if request.method == 'POST':
        modules.utilities.set_filters(
            'groups', modules.forms.groups_filters
        )
        if request.form['submit'] == 'delete':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    group = g.mysql.query(modules.models.group).get(id)
                    if group in g.user.groups:
                        g.mysql.delete(group)
                g.mysql.commit()
                flash(
                    'The selected groups were deleted successfully.', 'success'
                )
            else:
                flash(
                    'Please select atleast one group and try again.', 'error'
                )
    return redirect(url_for('users.groups_overview'))


@blueprint.route('/groups/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_user
def groups_edit(id):
    group = g.mysql.query(modules.models.group).get(id)
    if not group in g.user.groups:
        abort(404)
    form = modules.forms.groups_edit(request.form, group)
    form.id = id
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(group)
            flash('The group was updated successfully.', 'success')
            return redirect(url_for('users.groups_overview'))
        flash('The group was not updated successfully.', 'error')
    return render_template('users/views/groups_edit.html', form=form, id=id)


@blueprint.route('/groups/<int:id>/delete', methods=['GET', 'POST'])
@modules.decorators.requires_user
def groups_delete(id):
    group = g.mysql.query(modules.models.group).get(id)
    if not group in g.user.groups:
        abort(404)
    if request.method == 'GET':
        return render_template('users/views/groups_delete.html', id=id)
    if request.method == 'POST':
        g.mysql.delete(group)
        g.mysql.commit()
        flash('The group was deleted successfully.', 'success')
        return redirect(url_for('users.groups_overview'))


@blueprint.route('/accounts/overview')
@modules.decorators.requires_user
def accounts_overview():
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'accounts',
            {},
            {
                'column': 'id',
                'direction': 'asc',
            },
            10,
            1
        )
    form = modules.forms.accounts_filters(**filters)
    query = form.get_query(g.user.accounts)
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'users/views/accounts_overview.html',
        accounts=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix],
        form=form,
        order_by=order_by,
        pager=pager
    )


@blueprint.route('/accounts/add', methods=['GET', 'POST'])
@modules.decorators.requires_user
def accounts_add():
    if g.user.get_group() in ['Free']:
        if g.user.accounts.filter(
            modules.models.account.username != 'placeholder@mailsidekick.com',
        ).count() > 0:
            return render_template('users/views/accounts_add_free.html')
    account = modules.models.account()
    form = modules.forms.accounts_add(request.form)
    form.id = 0
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            account.user = g.user
            form.persist(account)
            flash('The account was saved successfully.', 'success')
            return redirect(url_for('users.accounts_overview'))
        flash('The account was not saved successfully.', 'error')
    return render_template(
        'users/views/accounts_add.html', account=account, form=form
    )


@blueprint.route('/accounts/process', methods=['GET', 'POST'])
@modules.decorators.requires_user
def accounts_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('accounts')
    if request.method == 'POST':
        modules.utilities.set_filters(
            'accounts', modules.forms.accounts_filters
        )
        if request.form['submit'] == 'verify':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    account = g.mysql.query(modules.models.account).get(id)
                    if account.username == 'placeholder@mailsidekick.com':
                        continue
                    if account in g.user.accounts:
                        account.update_connections()
                flash(
                    'The selected accounts were verified successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one account and try again.',
                    'error'
                )
        if request.form['submit'] == 'enable':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    account = g.mysql.query(modules.models.account).get(id)
                    if account.username == 'placeholder@mailsidekick.com':
                        continue
                    if account in g.user.accounts:
                        account.status = 'On'
                        g.mysql.merge(account)
                g.mysql.commit()
                flash(
                    'The selected accounts were enabled successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one account and try again.',
                    'error'
                )
        if request.form['submit'] == 'disable':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    account = g.mysql.query(modules.models.account).get(id)
                    if account.username == 'placeholder@mailsidekick.com':
                        continue
                    if account in g.user.accounts:
                        account.status = 'Off'
                        g.mysql.merge(account)
                g.mysql.commit()
                flash(
                    'The selected accounts were disabled successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one account and try again.',
                    'error'
                )
        if request.form['submit'] == 'delete':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    account = g.mysql.query(modules.models.account).get(id)
                    if account.username == 'placeholder@mailsidekick.com':
                        continue
                    if account in g.user.accounts:
                        g.mysql.delete(account)
                g.mysql.commit()
                flash(
                    'The selected accounts were deleted successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one account and try again.',
                    'error'
                )
    return redirect(url_for('users.accounts_overview'))


@blueprint.route('/accounts/import', methods=['GET', 'POST'])
@modules.decorators.requires_user
def accounts_import():
    if g.user.get_group() in ['Free']:
        return render_template('users/views/accounts_import_free.html')
    if request.method == 'POST':
        file = request.files.get('file')
        if not file.filename.lower().endswith('csv'):
            flash(
                'Error #1: Your import file must end in CSV. Please either '
                'use or reference the template provided.',
                'error'
            )
            return redirect(url_for('users.accounts_import'))
        '''
        if not file.mimetype in ['application/vnd.ms-excel', 'text/csv']:
            flash(
                'Error #2: You may only import files in CSV format. Please '
                'either use or reference the template provided.',
                'error'
            )
            return redirect(url_for('users.accounts_import'))
        '''
        count = modules.models.account.csv(g.user, file.stream)
        if not count:
            flash(
                'Error #3: Your import file does not contain any new email '
                'accounts. Please ensure that the accounts you\'re attempting '
                'to import do not already exist in your account list.',
                'error'
            )
            return redirect(url_for('users.accounts_import'))
        flash('%(count)d account(s) were imported successfully.' % {
            'count': count,
        }, 'success')
        return redirect(url_for('users.accounts_overview'))
    return render_template(
        'users/views/accounts_import.html',
        headers=modules.models.account.__table__.headers
    )


@blueprint.route('/accounts/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_user
def accounts_edit(id):
    account = g.mysql.query(modules.models.account).get(id)
    if not account in g.user.accounts:
        abort(404)
    if account.username == 'placeholder@mailsidekick.com':
        abort(404)
    form = modules.forms.accounts_edit(
        request.form, account, **account.get_dictionary()
    )
    form.id = id
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(account)
            flash('The account was updated successfully.', 'success')
            return redirect(url_for('users.accounts_overview'))
        flash('The account was not updated successfully.', 'error')
    return render_template(
        'users/views/accounts_edit.html', account=account, form=form, id=id
    )


@blueprint.route('/accounts/<int:id>/verify', methods=['GET', 'POST'])
@modules.decorators.requires_user
def accounts_verify(id):
    account = g.mysql.query(modules.models.account).get(id)
    if not account in g.user.accounts:
        abort(404)
    if account.username == 'placeholder@mailsidekick.com':
        abort(404)
    account.update_connections()
    return redirect(url_for('users.accounts_overview'))


@blueprint.route('/accounts/<int:id>/status')
@modules.decorators.requires_user
def accounts_status(id):
    account = g.mysql.query(modules.models.account).get(id)
    if not account in g.user.accounts:
        abort(404)
    if account.username == 'placeholder@mailsidekick.com':
        abort(404)
    account.toggle_status()
    return redirect(url_for('users.accounts_overview'))


@blueprint.route('/accounts/<int:id>/delete', methods=['GET', 'POST'])
@modules.decorators.requires_user
def accounts_delete(id):
    account = g.mysql.query(modules.models.account).get(id)
    if not account in g.user.accounts:
        abort(404)
    if account.username == 'placeholder@mailsidekick.com':
        abort(404)
    if request.method == 'GET':
        return render_template('users/views/accounts_delete.html', id=id)
    if request.method == 'POST':
        g.mysql.delete(account)
        g.mysql.commit()
        flash('The account was deleted successfully.', 'success')
        return redirect(url_for('users.accounts_overview'))


@blueprint.route('/history/<int:id>/overview')
@modules.decorators.requires_user
def history_overview(id):
    account = g.mysql.query(modules.models.account).get(id)
    if not account in g.user.accounts:
        abort(404)
    if account.username == 'placeholder@mailsidekick.com':
        abort(404)
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'history',
            {},
            {},
            10,
            1
        )
    query = g.mysql.query(
        modules.models.queue
    ).join(
        modules.models.log
    ).filter(
        modules.models.log.account == account,
        modules.models.queue.status == 'Delivered'
    )
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'users/views/history_overview.html',
        account=account,
        queues=query.order_by('scheduled_at asc')[pager.prefix:pager.suffix],
        pager=pager
    )


@blueprint.route('/history/<int:id>/process')
@modules.decorators.requires_user
def history_process(id):
    modules.utilities.set_order_by_limit_page('history')
    return redirect(url_for('users.history_overview', id=id))


@blueprint.route('/history/<int:id>/export')
@modules.decorators.requires_user
def history_export(id):
    account = g.mysql.query(modules.models.account).get(id)
    if not account in g.user.accounts:
        abort(404)
    if account.username == 'placeholder@mailsidekick.com':
        abort(404)
    rows = []
    rows.append([
        'Template',
        'Recipe (Step)',
        'Message ID',
        'Name',
        'Email',
        'Scheduled At',
        'Delivered At',
    ])
    for queue in g.mysql.query(
        modules.models.queue
    ).join(
        modules.models.log
    ).filter(
        modules.models.log.account == account,
        modules.models.queue.status == 'Delivered'
    ).order_by(
        'scheduled_at asc'
    ).all():
        rows.append([
            queue.template.name.encode('utf-8'),
            '%(name)s (%(step)s)' % {
                'name': queue.filter.name.encode('utf-8'),
                'step': queue.step,
            },
            queue.message_id.encode('utf-8'),
            queue.name.encode('utf-8'),
            queue.email.encode('utf-8'),
            modules.utilities.get_date_and_time(
                queue.scheduled_at
            ).encode('utf-8'),
            modules.utilities.get_date_and_time(
                queue.delivered_at
            ).encode('utf-8'),
        ])
    csv = StringIO()
    writer(
        csv,
        delimiter=',',
        doublequote=True,
        lineterminator='\n',
        quotechar='"',
        quoting=QUOTE_ALL,
        skipinitialspace=True
    ).writerows(rows)
    return Response(
        csv.getvalue(),
        headers={
            'Content-Disposition': 'attachment; filename=history.csv',
        },
        mimetype='text/csv'
    )


@blueprint.route('/variables/overview')
@modules.decorators.requires_user
def variables_overview():
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'variables',
            {},
            {
                'column': 'id',
                'direction': 'asc',
            },
            10,
            1
        )
    form = modules.forms.variables_filters(**filters)
    query = form.get_query(g.user.variables)
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'users/views/variables_overview.html',
        form=form,
        order_by=order_by,
        pager=pager,
        variables=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix]
    )


@blueprint.route('/variables/process', methods=['GET', 'POST'])
@modules.decorators.requires_user
def variables_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('variables')
    if request.method == 'POST':
        modules.utilities.set_filters(
            'variables', modules.forms.variables_filters
        )
        if request.form['submit'] == 'delete':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    variable = g.mysql.query(modules.models.variable).get(id)
                    if variable in g.user.variables:
                        g.mysql.delete(variable)
                g.mysql.commit()
                flash(
                    'The selected variables were deleted successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one variable and try again.',
                    'error'
                )
    return redirect(url_for('users.variables_overview'))


@blueprint.route('/variables/add', methods=['GET', 'POST'])
@modules.decorators.requires_user
def variables_add():
    form = modules.forms.variables_add(request.form)
    form.id = 0
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(modules.models.variable(**{
                'user': g.user,
            }))
            flash('The variable was saved successfully.', 'success')
            return redirect(url_for('users.variables_overview'))
        flash('The variable was not saved successfully.', 'error')
    return render_template('users/views/variables_add.html', form=form)


@blueprint.route('/variables/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_user
def variables_edit(id):
    variable = g.mysql.query(modules.models.variable).get(id)
    if not variable in g.user.variables:
        abort(404)
    form = modules.forms.variables_edit(request.form, variable)
    form.id = id
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(variable)
            flash('The variable was updated successfully.', 'success')
            return redirect(url_for('users.variables_overview'))
        flash('The variable was not updated successfully.', 'error')
    return render_template(
        'users/views/variables_edit.html', form=form, id=id
    )


@blueprint.route('/variables/<int:id>/delete', methods=['GET', 'POST'])
@modules.decorators.requires_user
def variables_delete(id):
    variable = g.mysql.query(modules.models.variable).get(id)
    if not variable in g.user.variables:
        abort(404)
    if request.method == 'GET':
        return render_template('users/views/variables_delete.html', id=id)
    if request.method == 'POST':
        g.mysql.delete(variable)
        g.mysql.commit()
        flash('The variable was deleted successfully.', 'success')
        return redirect(url_for('users.variables_overview'))


@blueprint.route('/templates/overview')
@modules.decorators.requires_user
def templates_overview():
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'templates',
            {},
            {
                'column': 'id',
                'direction': 'asc',
            },
            10,
            1
        )
    form = modules.forms.templates_filters(**filters)
    query = form.get_query(g.user.templates)
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'users/views/templates_overview.html',
        form=form,
        order_by=order_by,
        pager=pager,
        templates=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix],
    )


@blueprint.route('/templates/reset')
@modules.decorators.requires_user
def templates_reset():
    for code in g.mysql.query(modules.models.code).order_by('value asc').all():
        if code.has_redeemed(g.user):
            code.redeem(g.user, ['templates'])
    flash('Your redeemed templates have been reset successfully', 'success')
    return redirect(url_for('users.templates_overview'))


@blueprint.route('/templates/process', methods=['GET', 'POST'])
@modules.decorators.requires_user
def templates_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('templates')
    if request.method == 'POST':
        modules.utilities.set_filters(
            'templates', modules.forms.templates_filters
        )
        if request.form['submit'] == 'delete':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    template = g.mysql.query(modules.models.template).get(id)
                    if template in g.user.templates:
                        g.mysql.delete(template)
                        template.synchronize('delete')
                g.mysql.commit()
                flash(
                    'The selected templates were deleted successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one template and try again.',
                    'error'
                )
    return redirect(url_for('users.templates_overview'))


@blueprint.route('/templates/add', methods=['GET', 'POST'])
@modules.decorators.requires_user
def templates_add():
    template = modules.models.template(**{
        'user': g.user,
    })
    form = modules.forms.templates_add(request.form)
    form.id = 0
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(template)
            template.synchronize('add')
            flash('The template was saved successfully.', 'success')
            return redirect(url_for('users.templates_overview'))
        flash('The template was not saved successfully.', 'error')
    today = date.today()
    return render_template(
        'users/views/templates_add.html',
        form=form,
        template=template,
        today=today,
        tomorrow=today + timedelta(days=1),
        yesterday=today - timedelta(days=1),
    )


@blueprint.route('/templates/<int:id>/test', methods=['GET', 'POST'])
@modules.decorators.requires_user
def templates_test(id):
    template = g.mysql.query(modules.models.template).get(id)
    if not template in g.user.templates:
        abort(404)
    form = modules.forms.templates_test(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            if form.persist(template):
                flash('The template was tested successfully.', 'success')
                return redirect(url_for('users.templates_overview'))
        flash(
            'Template test failed: Unable to send from source email, please '
            'confirm connectivity from your email accounts list.',
            'error'
        )
    return render_template('users/views/templates_test.html', form=form, id=id)


@blueprint.route('/templates/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_user
def templates_edit(id):
    template = g.mysql.query(modules.models.template).get(id)
    if not template in g.user.templates:
        abort(404)
    form = modules.forms.templates_edit(request.form, template)
    form.id = template.id
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(template)
            template.synchronize('edit')
            flash('The template was updated successfully.', 'success')
            return redirect(url_for('users.templates_overview'))
        flash('The template was not updated successfully.', 'error')
    today = date.today()
    return render_template(
        'users/views/templates_edit.html',
        form=form,
        id=id,
        template=template,
        today=today,
        tomorrow=today + timedelta(days=1),
        yesterday=today - timedelta(days=1),
    )


@blueprint.route('/templates/<int:id>/delete', methods=['GET', 'POST'])
@modules.decorators.requires_user
def templates_delete(id):
    template = g.mysql.query(modules.models.template).get(id)
    if not template in g.user.templates:
        abort(404)
    if request.method == 'GET':
        return render_template('users/views/templates_delete.html', id=id)
    if request.method == 'POST':
        g.mysql.delete(template)
        g.mysql.commit()
        template.synchronize('delete')
        flash('The template was deleted successfully.', 'success')
        return redirect(url_for('users.templates_overview'))


@blueprint.route('/packs/overview')
@modules.decorators.requires_user
def packs_overview():
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'packs',
            {},
            {
                'column': 'id',
                'direction': 'asc',
            },
            10,
            1
        )
    form = modules.forms.packs_filters(**filters)
    query = form.get_query(g.user.packs)
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'users/views/packs_overview.html',
        form=form,
        order_by=order_by,
        packs=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix],
        pager=pager
    )


@blueprint.route('/packs/reset')
@modules.decorators.requires_user
def packs_reset():
    for code in g.mysql.query(modules.models.code).order_by('value asc').all():
        if code.has_redeemed(g.user):
            code.redeem(g.user, ['packs'])
    flash('Your redeemed recipe packs have been reset successfully', 'success')
    return redirect(url_for('users.packs_overview'))


@blueprint.route('/packs/add', methods=['GET', 'POST'])
@modules.decorators.requires_user
def packs_add():
    form = modules.forms.packs_add(request.form)
    form.id = 0
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(modules.models.pack(**{
                'user': g.user,
            }))
            flash('The pack was saved successfully.', 'success')
            return redirect(url_for('users.packs_overview'))
        flash('The pack was not saved successfully.', 'error')
    return render_template('users/views/packs_add.html', form=form)


@blueprint.route('/packs/process', methods=['GET', 'POST'])
@modules.decorators.requires_user
def packs_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('packs')
    if request.method == 'POST':
        modules.utilities.set_filters(
            'packs', modules.forms.packs_filters
        )
        if request.form['submit'] == 'delete':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    pack = g.mysql.query(modules.models.pack).get(id)
                    if pack in g.user.packs:
                        g.mysql.delete(pack)
                g.mysql.commit()
                flash(
                    'The selected packs were deleted successfully.', 'success'
                )
            else:
                flash(
                    'Please select atleast one pack and try again.', 'error'
                )
    return redirect(url_for('users.packs_overview'))


@blueprint.route('/packs/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_user
def packs_edit(id):
    pack = g.mysql.query(modules.models.pack).get(id)
    if not pack in g.user.packs:
        abort(404)
    form = modules.forms.packs_edit(request.form, pack)
    form.id = id
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(pack)
            flash('The pack was updated successfully.', 'success')
            return redirect(url_for('users.packs_overview'))
        flash('The pack was not updated successfully.', 'error')
    return render_template('users/views/packs_edit.html', form=form, id=id)


@blueprint.route('/packs/<int:id>/delete', methods=['GET', 'POST'])
@modules.decorators.requires_user
def packs_delete(id):
    pack = g.mysql.query(modules.models.pack).get(id)
    if not pack in g.user.packs:
        abort(404)
    if request.method == 'GET':
        return render_template('users/views/packs_delete.html', id=id)
    if request.method == 'POST':
        g.mysql.delete(pack)
        g.mysql.commit()
        flash('The pack was deleted successfully.', 'success')
        return redirect(url_for('users.packs_overview'))


@blueprint.route('/recipes/overview')
@modules.decorators.requires_user
def filters_overview():
    return render_template(
        'users/views/filters_overview.html',
        examples=[
            (filter.id, filter.name)
            for filter in g.mysql.query(
                modules.models.filter
            ).filter(
                modules.models.filter.user == null()
            ).order_by(
                'name asc'
            ).all()
        ],
        filters=g.user.filters.order_by('position asc').all(),
    )


@blueprint.route('/recipes/reset')
@modules.decorators.requires_user
def filters_reset():
    for code in g.mysql.query(modules.models.code).order_by('value asc').all():
        if code.has_redeemed(g.user):
            code.redeem(g.user, ['filters'])
    flash('Your redeemed recipes have been reset successfully', 'success')
    return redirect(url_for('users.filters_overview'))


@blueprint.route('/recipes/process', methods=['GET', 'POST'])
@modules.decorators.requires_user
def filters_process():
    if request.method == 'GET':
        pass
    if request.method == 'POST':
        if request.form['submit'] == 'enable':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    filter = g.mysql.query(modules.models.filter).get(id)
                    if filter in g.user.filters:
                        filter.status = 'On'
                        g.mysql.merge(filter)
                g.mysql.commit()
                flash(
                    'The selected recipes were enabled successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one recipe and try again.',
                    'error'
                )
        if request.form['submit'] == 'disable':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    filter = g.mysql.query(modules.models.filter).get(id)
                    if filter in g.user.filters:
                        filter.status = 'Off'
                        g.mysql.merge(filter)
                g.mysql.commit()
                flash(
                    'The selected recipes were disabled successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one recipe and try again.',
                    'error'
                )
        if request.form['submit'] == 'delete':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    filter = g.mysql.query(modules.models.filter).get(id)
                    if filter in g.user.filters:
                        g.mysql.delete(filter)
                g.mysql.commit()
                flash(
                    'The selected recipes were deleted successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one recipe and try again.',
                    'error'
                )
    return redirect(url_for('users.filters_overview'))


@blueprint.route('/recipes/add', methods=['GET', 'POST'])
@modules.decorators.requires_user
def filters_add():
    filter = modules.models.filter()
    form = modules.forms.filters_add(request.form, filter)
    form.id = 0
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            filter.user = g.user
            form.persist(filter)
            flash('The recipe was saved successfully.', 'success')
            return redirect(url_for('users.filters_overview'))
        flash('The recipe was not saved successfully.', 'error')
    return render_template(
        'users/views/filters_add.html',
        accounts=get_accounts(),
        filter=filter,
        form=form,
        templates=get_templates()
    )


@blueprint.route('/recipes/<int:id>/tour')
@modules.decorators.requires_user
def filters_tour(id):
    filter = g.mysql.query(modules.models.filter).get(id)
    if filter.user:
        abort(404)
    form = modules.forms.filters_edit(request.form, filter)
    form.id = id
    form.user_id = 0
    return render_template(
        'users/views/filters_tour.html',
        accounts=get_accounts(),
        filter=filter,
        form=form,
        id=id,
        templates=get_templates()
    )


@blueprint.route('/recipes/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_user
def filters_edit(id):
    filter = g.mysql.query(modules.models.filter).get(id)
    if not filter in g.user.filters:
        abort(404)
    form = modules.forms.filters_edit(request.form, filter)
    form.id = id
    form.user_id = g.user.ID
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(filter)
            flash('The recipe was updated successfully.', 'success')
            return redirect(url_for('users.filters_overview'))
        flash('The recipe was not updated successfully.', 'error')
    return render_template(
        'users/views/filters_edit.html',
        accounts=get_accounts(),
        filter=filter,
        form=form,
        id=id,
        templates=get_templates()
    )


@blueprint.route('/recipes/<int:id>/position/<direction>')
@modules.decorators.requires_user
def filters_position(id, direction):
    filter = g.mysql.query(modules.models.filter).get(id)
    if not filter in g.user.filters:
        abort(404)
    filter.toggle_position(direction)
    return redirect(url_for('users.filters_overview'))


@blueprint.route('/recipes/<int:id>/status')
@modules.decorators.requires_user
def filters_status(id):
    filter = g.mysql.query(modules.models.filter).get(id)
    if not filter in g.user.filters:
        abort(404)
    filter.toggle_status()
    return redirect(url_for('users.filters_overview'))


@blueprint.route('/recipes/<int:id>/delete', methods=['GET', 'POST'])
@modules.decorators.requires_user
def filters_delete(id):
    filter = g.mysql.query(modules.models.filter).get(id)
    if not filter in g.user.filters:
        abort(404)
    if request.method == 'GET':
        return render_template('users/views/filters_delete.html', id=id)
    if request.method == 'POST':
        g.mysql.delete(filter)
        g.mysql.commit()
        flash('The recipe was deleted successfully.', 'success')
        return redirect(url_for('users.filters_overview'))


@blueprint.route('/queues/overview/<status>')
@modules.decorators.requires_user
def queues_overview(status):
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'queues',
            {},
            {
                'column': 'queues.id',
                'direction': 'desc',
            },
            10,
            1
        )
    form = modules.forms.queues_filters(**filters)
    query = form.get_query(
        g.mysql.query(
            modules.models.queue
        ).join(
            modules.models.filter
        ).join(
            modules.models.template
        ).join(
            modules.models.log
        ).join(
            modules.models.account
        ).join(
            modules.models.user
        ).filter(
            modules.models.user.ID == g.user.ID
        )
    )
    if not status == 'everything':
        query = query.filter(modules.models.queue.status == status.title())
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'users/views/queues_overview.html',
        accounts=list(OrderedDict.fromkeys([
            instance.log.account
            for instance in g.mysql.query(
                modules.models.queue
            ).join(
                modules.models.log
            ).join(
                modules.models.account
            ).filter(
                modules.models.account.id == modules.models.log.account_id,
                modules.models.account.user == g.user,
                modules.models.log.id == modules.models.queue.log_id
            ).order_by(
                'accounts.id asc'
            ).all()
            if (
                instance.get_scheduled_for()[0] < datetime.now()
                and
                instance.status == 'Scheduled'
            )
        ])),
        form=form,
        order_by=order_by,
        pager=pager,
        queues=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix],
        status=status
    )


@blueprint.route('/queues/process/<status>', methods=['GET', 'POST'])
@modules.decorators.requires_user
def queues_process(status):
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('queues')
    if request.method == 'POST':
        modules.utilities.set_filters(
            'queues', modules.forms.queues_filters
        )
    return redirect(url_for('users.queues_overview', status=status))


@blueprint.route('/queues/export', methods=['GET', 'POST'])
@modules.decorators.requires_user
def queues_export():
    form = modules.forms.queues_export(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            rows = []
            rows.append([
                'Name',
                'Email',
                'Last Scheduled At',
                'Last Delivered At',
            ])
            for item in sorted(
                g.user.get_items().values(), key=lambda item: item[2]
            ):
                if item[4] in form.filters.data:
                    rows.append([item[0], item[1], item[2], item[3]])
            csv = StringIO()
            writer(
                csv,
                delimiter=',',
                doublequote=True,
                lineterminator='\n',
                quotechar='"',
                quoting=QUOTE_ALL,
                skipinitialspace=True
            ).writerows(rows)
            return Response(
                csv.getvalue(),
                headers={
                    'Content-Disposition':
                    'attachment; filename=queues.csv',
                },
                mimetype='text/csv'
            )
    return render_template('users/views/queues_export.html', form=form)


@blueprint.route('/queues/re-schedule/all')
@modules.decorators.requires_user
def queues_re_schedule_all():
    for queue in g.mysql.query(
        modules.models.queue
    ).join(
        modules.models.filter
    ).join(
        modules.models.template
    ).join(
        modules.models.log
    ).join(
        modules.models.account
    ).join(
        modules.models.user
    ).filter(
        modules.models.queue.status == 'Backlogged',
        modules.models.user.ID == g.user.ID,
    ).all():
        queue.status = 'Scheduled'
        g.mysql.add(queue)
        g.mysql.commit()
    return redirect(url_for('users.queues_overview', status='backlogged'))


@blueprint.route('/queues/cancel/all', methods=['GET', 'POST'])
@modules.decorators.requires_user
def queues_cancel_all():
    if request.method == 'GET':
        return render_template('users/views/queues_cancel_all.html')
    if request.method == 'POST':
        for queue in g.mysql.query(
            modules.models.queue
        ).join(
            modules.models.filter
        ).join(
            modules.models.template
        ).join(
            modules.models.log
        ).join(
            modules.models.account
        ).join(
            modules.models.user
        ).filter(
            modules.models.queue.status == 'Scheduled',
            modules.models.user.ID == g.user.ID,
        ).all():
            queue.status = 'Cancelled'
            g.mysql.add(queue)
            g.mysql.commit()
        return redirect(url_for('users.queues_overview', status='scheduled'))


@blueprint.route('/queues/re-schedule/<id>')
@modules.decorators.requires_user
def queues_re_schedule(id):
    queue = g.mysql.query(modules.models.queue).get(id)
    queue.status = 'Scheduled'
    g.mysql.add(queue)
    g.mysql.commit()
    return redirect(url_for('users.queues_overview', status='backlogged'))


@blueprint.route('/queues/<status>/<int:id>/cancel')
@modules.decorators.requires_user
def queues_cancel(status, id):
    queue = g.mysql.query(modules.models.queue).get(id)
    if not queue:
        abort(404)
    if not queue.log.account.user == g.user:
        abort(404)
    queue.cancel()
    return redirect(url_for('users.queues_overview', status=status))


@blueprint.route('/queues/<int:id>/view')
@modules.decorators.requires_user
def queues_view(id):
    queue = g.mysql.query(modules.models.queue).get(id)
    if not queue:
        abort(404)
    if not queue.log.account.user == g.user:
        abort(404)
    return render_template('users/views/queues_view.html', queue=queue)


@blueprint.route('/settings', methods=['GET', 'POST'])
@modules.decorators.requires_user
def settings():
    settings = g.user.get_settings()
    form = modules.forms.users_settings(
        request.form,
        blacklist='\n'.join(settings['blacklist']),
        credits=settings['credits'],
        filters=True if settings['filters'] == 'Yes' else False,
        profanity='\n'.join(settings['profanity'])
    )
    if g.user.get_group() in ['Free', 'Premium', 'Premium+']:
        del form.credits
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist()
            flash('Your settings have been saved successfully.', 'success')
            return redirect(url_for('users.settings'))
        flash('Your settings have not been saved successfully.', 'error')
    return render_template('users/views/settings.html', form=form)


@blueprint.route('/dashboard/overview')
@modules.decorators.requires_user
def dashboard_overview():
    alerts = {
        'accounts_gmail': [],
        'accounts_proxies': [],
        'credits': '',
        'filters': [],
    }
    for account in g.user.accounts.order_by('id asc').all():
        if account.connections['outgoing'] in ['On', '']:
            continue
        if not account.outgoing_hostname == 'smtp.gmail.com':
            continue
        if not account.outgoing_use_tls == 'Yes':
            continue
        alerts['accounts_gmail'].append(account)
    for account in g.user.accounts.order_by('id asc').all():
        if not account.proxy:
            continue
        if account.proxy.status == 'Off':
            alerts['accounts_proxies'].append(account)
    for filter in g.user.filters.order_by('id asc').all():
        if sum([
            step['number_of_days'] for step in filter.steps
        ]) > filter.visibility:
            alerts['filters'].append(filter)
    if not g.user.get_group() in ['Free', 'Premium', 'Premium+']:
        credits = g.user.get_credits()
        if credits['remaining'] < credits['settings']:
            alerts['credits'] = modules.utilities.get_integer(
                credits['remaining']
            )
    return render_template(
        'users/views/dashboard.html',
        alerts=alerts,
        articles=g.mysql.query(modules.models.article).filter(
            modules.models.article.status == 'On'
        ).order_by(
            'sticky desc , timestamp desc'
        ).all(),
        items=[
            {
                'key': 'News Items',
                'value': g.mysql.query(modules.models.article).filter(
                    modules.models.article.status == 'On'
                ).count(),
            }, {
                'key': 'Email Groups',
                'value': g.user.groups.count(),
            }, {
                'key': 'Proxies',
                'value': g.user.proxies.count(),
            }, {
                'key': 'Email Accounts',
                'value': g.user.accounts.count(),
            }, {
                'key': 'Email Templates',
                'value': g.user.templates.count(),
            }, {
                'key': 'Recipe Packs',
                'value': g.user.packs.count(),
            }, {
                'key': 'Recipes',
                'value': g.user.filters.count(),
            }, {
                'key': 'Currently In Queue',
                'value': g.user.get_queues(),
            }, {
                'key': 'Custom Variables',
                'value': g.user.variables.count(),
            },
        ]
    )


@blueprint.route('/dashboard/history', methods=['POST'])
@modules.decorators.requires_user
def dashboard_history():
    items = []
    for queue in g.mysql.query(
        modules.models.queue
    ).join(
        modules.models.log
    ).join(
        modules.models.account
    ).join(
        modules.models.user
    ).filter(
        modules.models.queue.status == 'Delivered',
        modules.models.user.ID == g.user.ID
    ).order_by(
        'delivered_at desc'
    ).all()[0:5]:
        items.append({
            'account': {
                'username': queue.get_account().username,
            },
            'delivered_at': modules.utilities.get_date_and_time(
                queue.delivered_at
            ),
            'email': queue.email,
            'href': url_for('users.queues_view', id=queue.id),
            'name': queue.name,
        })
    return jsonify({
        'items': items,
    })


@blueprint.route('/suggestions', methods=['GET', 'POST'])
@modules.decorators.requires_user
def suggestions():
    form = modules.forms.suggestions(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            form.send()
            flash('Your suggestion has been sent successfully.', 'success')
            return redirect(url_for('users.suggestions'))
        flash('Your suggestion has not been sent successfully.', 'error')
    return render_template('users/views/suggestions.html', form=form)


@blueprint.route('/survey', methods=['GET', 'POST'])
@modules.decorators.requires_user
def survey():
    if request.args.get('reset') == 'yes':
        instance = g.mysql.query(
            modules.models.meta
        ).filter(
            modules.models.meta.meta_key == 'survey',
            modules.models.meta.user == g.user
        ).first()
        if instance:
            g.mysql.delete(instance)
            g.mysql.commit()
        return redirect(url_for('users.dashboard_overview'))
    if not g.user.can_survey():
        return redirect(url_for('users.dashboard_overview'))
    referer = request.args.get(
        'referer'
    ) or request.referrer or url_for('users.dashboard_overview')
    form = modules.forms.survey(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            form.send()
            flash(
                'Thank you for sending us your feedback, we really appreciate '
                'it!',
                'success'
            )
            return redirect(referer)
        flash('Your answers have not been sent successfully.', 'error')
    return render_template(
        'users/views/survey.html', form=form, referer=referer
    )


@blueprint.route('/redeem', methods=['GET', 'POST'])
@modules.decorators.requires_user
def redeem():
    items = {}
    status = False
    form = modules.forms.redeem(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            items = form.get_items(g.user, ['filters', 'packs', 'templates'])
            status = True
    return render_template(
        'users/views/redeem.html', form=form, items=items, status=status
    )


@blueprint.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    if g.user:
        return redirect(
            request.args.get('next') or url_for('users.dashboard_overview')
        )
    form = modules.forms.users_sign_in(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            flash('You have been signed in successfully.', 'success')
            return redirect(
                request.args.get('next') or url_for('users.dashboard_overview')
            )
        flash('You have not been signed in successfully.', 'error')
    return render_template('users/views/sign_in.html', form=form)


@blueprint.route('/sign-out')
def sign_out():
    if 'user' in session:
        del session['user']
    flash('You have been signed out successfully.', 'success')
    return redirect(url_for('users.dashboard_overview'))


def get_accounts():
    return [('0', 'N/A')] + [
        (str(account.id), account.username)
        for account in g.user.accounts.filter(
            modules.models.account.status == 'On'
        ).order_by(
            'username asc'
        ).all()
    ]


def get_templates():
    return [
        (template.id, template.name)
        for template in g.user.templates.order_by('name asc').all()
    ]
