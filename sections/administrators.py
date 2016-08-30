# -*- coding: utf-8 -*-

from contextlib import closing
from datetime import date, datetime, timedelta
from flask import (
    Blueprint,
    abort,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for
)
from sqlalchemy import func
from sqlalchemy.sql import null, text
from wtforms.fields import TextAreaField, TextField

import modules.classes
import modules.database
import modules.decorators
import modules.models
import modules.utilities
import modules.widgets
import modules.validators

blueprint = Blueprint('administrators', __name__)


@blueprint.before_request
def before_request():
    g.administrator = None
    if 'administrator' in session:
        g.administrator = g.mysql.query(modules.models.administrator).get(
            session['administrator']
        )


@blueprint.route('/administrators/overview')
@modules.decorators.requires_administrator
def administrators_overview():
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'administrators',
            {},
            {
                'column': 'id',
                'direction': 'asc',
            },
            10,
            1
        )
    form = modules.forms.administrators_filters(**filters)
    query = form.get_query(g.mysql.query(modules.models.administrator))
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'administrators/views/administrators_overview.html',
        administrators=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix],
        form=form,
        order_by=order_by,
        pager=pager
    )


@blueprint.route('/administrators/process', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def administrators_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('administrators')
    if request.method == 'POST':
        modules.utilities.set_filters(
            'administrators', modules.forms.administrators_filters
        )
        if request.form['submit'] == 'enable':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    administrator = g.mysql.query(
                        modules.models.administrator
                    ).get(id)
                    administrator.status = 'On'
                    g.mysql.merge(administrator)
                g.mysql.commit()
                flash(
                    'The selected administrators were enabled successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one administrator and try again.',
                    'error'
                )
        if request.form['submit'] == 'disable':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    administrator = g.mysql.query(
                        modules.models.administrator
                    ).get(id)
                    administrator.status = 'Off'
                    g.mysql.merge(administrator)
                g.mysql.commit()
                flash(
                    'The selected administrators were disabled successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one administrator and try again.',
                    'error'
                )
        if request.form['submit'] == 'delete':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    g.mysql.delete(g.mysql.query(
                        modules.models.administrator
                    ).get(id))
                g.mysql.commit()
                flash(
                    'The selected administrators were deleted successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one administrator and try again.',
                    'error'
                )
    return redirect(url_for('administrators.administrators_overview'))


@blueprint.route('/administrators/add', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def administrators_add():
    administrator = modules.models.administrator()
    form = modules.forms.administrators_add(request.form)
    form.id = 0
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(administrator)
            flash('The administrator was saved successfully.', 'success')
            return redirect(url_for('administrators.administrators_overview'))
        flash('The administrator was not saved successfully.', 'error')
    return render_template(
        'administrators/views/administrators_add.html', form=form
    )


@blueprint.route('/administrators/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def administrators_edit(id):
    administrator = g.mysql.query(modules.models.administrator).get(id)
    form = modules.forms.administrators_edit(request.form, administrator)
    form.id = administrator.id
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(administrator)
            flash('The administrator was updated successfully.', 'success')
            return redirect(url_for('administrators.administrators_overview'))
        flash('The administrator was not updated successfully.', 'error')
    return render_template(
        'administrators/views/administrators_edit.html', form=form, id=id
    )


@blueprint.route('/administrators/<int:id>/status')
@modules.decorators.requires_administrator
def administrators_status(id):
    g.mysql.query(modules.models.administrator).get(id).toggle_status()
    return redirect(url_for('administrators.administrators_overview'))


@blueprint.route('/administrators/<int:id>/delete', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def administrators_delete(id):
    if request.method == 'GET':
        return render_template(
            'administrators/views/administrators_delete.html', id=id
        )
    if request.method == 'POST':
        g.mysql.delete(g.mysql.query(modules.models.administrator).get(id))
        g.mysql.commit()
        flash('The administrator was deleted successfully.', 'success')
        return redirect(url_for('administrators.administrators_overview'))


@blueprint.route('/users/overview')
@modules.decorators.requires_administrator
def users_overview():
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'users',
            {},
            {
                'column': 'ID',
                'direction': 'asc',
            },
            10,
            1
        )
    form = modules.forms.users_filters(**filters)
    query = form.get_query(g.mysql.query(modules.models.user))
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'administrators/views/users_overview.html',
        users=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix],
        form=form,
        order_by=order_by,
        pager=pager
    )


@blueprint.route('/users/process', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def users_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('users')
    if request.method == 'POST':
        modules.utilities.set_filters('users', modules.forms.users_filters)
    return redirect(url_for('administrators.users_overview'))


@blueprint.route('/users/<int:id>/transfer')
@modules.decorators.requires_administrator
def users_transfer(id):
    session['user'] = id
    url = request.args.get('url')
    if url:
        return redirect(url)
    return redirect(url_for('users.dashboard_overview'))


@blueprint.route('/articles/overview')
@modules.decorators.requires_administrator
def articles_overview():
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'articles',
            {},
            {
                'column': 'timestamp',
                'direction': 'desc',
            },
            10,
            1
        )
    form = modules.forms.articles_filters(**filters)
    query = form.get_query(g.mysql.query(modules.models.article))
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'administrators/views/articles_overview.html',
        articles=query.order_by(
            'sticky desc , timestamp desc' % order_by
        )[pager.prefix:pager.suffix],
        form=form,
        order_by=order_by,
        pager=pager
    )


@blueprint.route('/articles/process', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def articles_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('articles')
    if request.method == 'POST':
        modules.utilities.set_filters(
            'articles', modules.forms.articles_filters
        )
        if request.form['submit'] == 'enable':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    article = g.mysql.query(modules.models.article).get(id)
                    article.status = 'On'
                    g.mysql.merge(article)
                g.mysql.commit()
                flash(
                    'The selected articles were enabled successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one article and try again.',
                    'error'
                )
        if request.form['submit'] == 'disable':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    article = g.mysql.query(modules.models.article).get(id)
                    article.status = 'Off'
                    g.mysql.merge(article)
                    g.mysql.commit()
                flash(
                    'The selected articles were disabled successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one article and try again.',
                    'error'
                )
        if request.form['submit'] == 'stick':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    article = g.mysql.query(modules.models.article).get(id)
                    article.sticky = 'Yes'
                    g.mysql.merge(article)
                g.mysql.commit()
                flash(
                    'The selected articles were stuck successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one article and try again.',
                    'error'
                )
        if request.form['submit'] == 'unstick':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    article = g.mysql.query(modules.models.article).get(id)
                    article.sticky = 'No'
                    g.mysql.merge(article)
                    g.mysql.commit()
                flash(
                    'The selected articles were unstuck successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one article and try again.',
                    'error'
                )
        if request.form['submit'] == 'delete':
            ids = request.form.getlist('ids')
            if ids:
                for id in ids:
                    g.mysql.delete(g.mysql.query(
                        modules.models.article
                    ).get(id))
                g.mysql.commit()
                flash(
                    'The selected articles were deleted successfully.',
                    'success'
                )
            else:
                flash(
                    'Please select atleast one article and try again.',
                    'error'
                )
    return redirect(url_for('administrators.articles_overview'))


@blueprint.route('/articles/add', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def articles_add():
    article = modules.models.article()
    article.timestamp = datetime.now()
    form = modules.forms.articles_add(request.form)
    form.id = 0
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(article)
            flash('The article was saved successfully.', 'success')
            return redirect(url_for('administrators.articles_overview'))
        flash('The article was not saved successfully.', 'error')
    return render_template('administrators/views/articles_add.html', form=form)


@blueprint.route('/articles/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def articles_edit(id):
    article = g.mysql.query(modules.models.article).get(id)
    article.timestamp = datetime.now()
    form = modules.forms.articles_edit(request.form, article)
    form.id = article.id
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(article)
            flash('The article was updated successfully.', 'success')
            return redirect(url_for('administrators.articles_overview'))
        flash('The article was not updated successfully.', 'error')
    return render_template(
        'administrators/views/articles_edit.html', id=id, form=form
    )


@blueprint.route('/articles/<int:id>/sticky')
@modules.decorators.requires_administrator
def articles_sticky(id):
    g.mysql.query(modules.models.article).get(id).toggle_sticky()
    return redirect(url_for('administrators.articles_overview'))


@blueprint.route('/articles/<int:id>/status')
@modules.decorators.requires_administrator
def articles_status(id):
    g.mysql.query(modules.models.article).get(id).toggle_status()
    return redirect(url_for('administrators.articles_overview'))


@blueprint.route('/articles/<int:id>/delete', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def articles_delete(id):
    if request.method == 'GET':
        return render_template(
            'administrators/views/articles_delete.html', id=id
        )
    if request.method == 'POST':
        g.mysql.delete(g.mysql.query(modules.models.article).get(id))
        g.mysql.commit()
        flash('The article was deleted successfully.', 'success')
        return redirect(url_for('administrators.articles_overview'))


@blueprint.route('/templates/overview')
@modules.decorators.requires_administrator
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
    query = form.get_query(
        g.mysql.query(
            modules.models.template
        ).filter(
            modules.models.template.user == null()
        )
    )
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'administrators/views/templates_overview.html',
        form=form,
        order_by=order_by,
        pager=pager,
        templates=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix],
    )


@blueprint.route('/templates/process', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def templates_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('templates')
    if request.method == 'POST':
        modules.utilities.set_filters(
            'templates', modules.forms.templates_filters
        )
    return redirect(url_for('administrators.templates_overview'))


@blueprint.route('/templates/add', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def templates_add():
    template = modules.models.template()
    form = modules.forms.templates_add(request.form)
    form.id = 0
    form.user_id = None
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(template)
            template.synchronize('add')
            flash('The email template was saved successfully.', 'success')
            return redirect(url_for('administrators.templates_overview'))
        flash('The email template was not saved successfully.', 'error')
    today = date.today()
    return render_template(
        'administrators/views/templates_add.html',
        form=form,
        template=template,
        today=today,
        tomorrow=today + timedelta(days=1),
        yesterday=today - timedelta(days=1),
    )


@blueprint.route('/templates/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def templates_edit(id):
    template = g.mysql.query(modules.models.template).get(id)
    if template.user:
        abort(404)
    form = modules.forms.templates_edit(request.form, template)
    form.id = template.id
    form.user_id = None
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(template)
            template.synchronize('edit')
            flash('The email template was updated successfully.', 'success')
            return redirect(url_for('administrators.templates_overview'))
        flash('The email template was not updated successfully.', 'error')
    today = date.today()
    return render_template(
        'administrators/views/templates_edit.html',
        form=form,
        id=id,
        template=template,
        today=today,
        tomorrow=today + timedelta(days=1),
        yesterday=today - timedelta(days=1),
    )


@blueprint.route('/packs/overview')
@modules.decorators.requires_administrator
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
    query = form.get_query(
        g.mysql.query(
            modules.models.pack
        ).filter(
            modules.models.pack.user == null()
        )
    )
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'administrators/views/packs_overview.html',
        form=form,
        order_by=order_by,
        packs=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix],
        pager=pager,
    )


@blueprint.route('/packs/process', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def packs_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('packs')
    if request.method == 'POST':
        modules.utilities.set_filters('packs', modules.forms.packs_filters)
    return redirect(url_for('administrators.packs_overview'))


@blueprint.route('/packs/add', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def packs_add():
    pack = modules.models.pack()
    form = modules.forms.packs_add(request.form)
    form.id = 0
    form.user_id = None
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(pack)
            flash('The pack was saved successfully.', 'success')
            return redirect(url_for('administrators.packs_overview'))
        flash('The pack was not saved successfully.', 'error')
    return render_template(
        'administrators/views/packs_add.html', form=form, pack=pack
    )


@blueprint.route('/packs/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def packs_edit(id):
    pack = g.mysql.query(modules.models.pack).get(id)
    if pack.user:
        abort(404)
    form = modules.forms.packs_edit(request.form, pack)
    form.id = pack.id
    form.user_id = None
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(pack)
            flash('The pack was updated successfully.', 'success')
            return redirect(url_for('administrators.packs_overview'))
        flash('The pack was not updated successfully.', 'error')
    return render_template(
        'administrators/views/packs_edit.html', form=form, id=id, pack=pack
    )


@blueprint.route('/filters/overview')
@modules.decorators.requires_administrator
def filters_overview():
    return render_template(
        'administrators/views/filters_overview.html',
        filters=g.mysql.query(
            modules.models.filter
        ).filter(
            modules.models.filter.user == null()
        ).order_by(
            'position asc'
        ).all()
    )


@blueprint.route('/filters/add', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def filters_add():
    filter = modules.models.filter()
    form = modules.forms.filters_add(request.form, filter)
    form.id = 0
    form.user_id = None
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(filter)
            flash('The recipe was saved successfully.', 'success')
            return redirect(url_for('administrators.filters_overview'))
        flash('The recipe was not saved successfully.', 'error')
    return render_template(
        'administrators/views/filters_add.html',
        accounts=get_accounts(),
        filter=filter,
        form=form,
        templates=get_templates()
    )


@blueprint.route('/filters/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def filters_edit(id):
    filter = g.mysql.query(modules.models.filter).get(id)
    if filter.user:
        abort(404)
    form = modules.forms.filters_edit(request.form, filter)
    form.id = filter.id
    form.user_id = None
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(filter)
            flash('The recipe was updated successfully.', 'success')
            return redirect(url_for('administrators.filters_overview'))
        flash('The recipe was not updated successfully.', 'error')
    return render_template(
        'administrators/views/filters_edit.html',
        accounts=get_accounts(),
        filter=filter,
        form=form,
        id=id,
        templates=get_templates()
    )


@blueprint.route('/recipes/<int:id>/position/<direction>')
@modules.decorators.requires_administrator
def filters_position(id, direction):
    filter = g.mysql.query(modules.models.filter).get(id)
    if filter.user:
        abort(404)
    filter.toggle_position(direction)
    return redirect(url_for('administrators.filters_overview'))


@blueprint.route('/recipes/<int:id>/status')
@modules.decorators.requires_administrator
def filters_status(id):
    filter = g.mysql.query(modules.models.filter).get(id)
    if filter.user:
        abort(404)
    filter.toggle_status()
    return redirect(url_for('administrators.filters_overview'))


@blueprint.route('/codes/overview')
@modules.decorators.requires_administrator
def codes_overview():
    filters, order_by, limit, page = \
        modules.utilities.get_filters_order_by_limit_page(
            'codes',
            {},
            {
                'column': 'id',
                'direction': 'asc',
            },
            10,
            1
        )
    form = modules.forms.codes_filters(**filters)
    query = form.get_query(g.mysql.query(modules.models.code))
    pager = modules.classes.pager(query.count(), limit, page)
    return render_template(
        'administrators/views/codes_overview.html',
        form=form,
        order_by=order_by,
        codes=query.order_by(
            '%(column)s %(direction)s' % order_by
        )[pager.prefix:pager.suffix],
        pager=pager
    )


@blueprint.route('/codes/process', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def codes_process():
    if request.method == 'GET':
        modules.utilities.set_order_by_limit_page('codes')
    if request.method == 'POST':
        modules.utilities.set_filters(
            'codes', modules.forms.codes_filters
        )
    return redirect(url_for('administrators.codes_overview'))


@blueprint.route('/codes/add', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def codes_add():
    code = modules.models.code()
    form = modules.forms.codes_add(request.form)
    form.id = 0
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(code)
            flash('The code was saved successfully.', 'success')
            return redirect(url_for('administrators.codes_overview'))
        flash('The code was not saved successfully.', 'error')
    return render_template(
        'administrators/views/codes_add.html',
        filter_ids=[],
        form=form,
        pack_ids=[]
    )


@blueprint.route('/codes/<int:id>/edit', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def codes_edit(id):
    code = g.mysql.query(modules.models.code).get(id)
    form = modules.forms.codes_edit(request.form, code)
    form.id = code.id
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(code)
            flash('The code was updated successfully.', 'success')
            return redirect(url_for('administrators.codes_overview'))
        flash('The code was not updated successfully.', 'error')
    return render_template(
        'administrators/views/codes_edit.html',
        filter_ids=code.get_filter_ids(),
        form=form,
        id=id,
        pack_ids=code.get_pack_ids()
    )


@blueprint.route('/settings', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def settings():
    for key, _ in modules.models.option.get_option_value().iteritems():
        if key == 'change_log':
            setattr(
                modules.forms.administrators_settings,
                key,
                modules.fields.wysihtml5(
                    validators=[modules.validators.required()],
                    widget=modules.widgets.textarea(rows=10),
                )
            )
            continue
        if key == 'version':
            setattr(
                modules.forms.administrators_settings,
                key,
                TextField(
                    label='Version',
                    validators=[modules.validators.required()],
                )
            )
            continue
        setattr(
            modules.forms.administrators_settings,
            key,
            TextAreaField(
                description=[
                    'Please enter one item per line.',
                ],
                label=key.split('_')[-1].title(),
                widget=modules.widgets.textarea(rows=5)
            )
        )
    form = modules.forms.administrators_settings(
        request.form,
        **modules.forms.administrators_settings.get_dictionary()
    )
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist()
            flash('Your settings have been saved successfully.', 'success')
            return redirect(url_for('administrators.settings'))
        flash('Your settings have not been saved successfully.', 'error')
    return render_template('administrators/views/settings.html', form=form)


@blueprint.route('/')
@blueprint.route('/dashboard')
@modules.decorators.requires_administrator
def dashboard():
    now = datetime.now()
    last_backup = 'N/A'
    next_backup = 'N/A'
    failed_backup = 'N/A'
    try:
        files = {}
        for item in modules.utilities.get_s3().list():
            key = item.name.split('_')[0]
            if not key in files:
                files[key] = 0
            files[key] += item.size
        files = sorted(files.items(), key=lambda item: item[0], reverse=True)
        date = datetime.strptime(files[0][0], '%Y-%m-%d')
        last_backup = '%(date)s <em>(%(size)s MB)</em>' % {
            'date': modules.utilities.get_date(date),
            'size': modules.utilities.get_float(
                (files[0][1] * 1.00) / (1024 * 1024 * 1.00)
            ),
        }
        next_backup = modules.utilities.get_date(date + timedelta(days=1))
        dates = [key for key, value in files]
        for key, value in files:
            key = (
                datetime.strptime(key, '%Y-%m-%d') - timedelta(days=1)
            ).isoformat(' ').split(' ')[0]
            if key == dates[-1]:
                break
            if not key in dates:
                failed_backup = key
                break
    except:
        from traceback import print_exc
        print_exc()
        pass
    backups = [{
        'key': 'Last Backup',
        'value': last_backup,
    }, {
        'key': 'Next Backup',
        'value': next_backup,
    }, {
        'key': 'Failed Backup',
        'value': failed_backup,
    }]
    tsi = g.mysql.query(
        modules.models.queue
    ).filter(
        modules.models.queue.status.in_(['Scheduled']),
    ).order_by('id asc').count()
    tsiitf_absolute = 0
    tsiitf_relative = 0
    tsiitp_absolute = 0
    tsiitp_relative = 0
    for queue in g.mysql.query(
        modules.models.queue
    ).filter(
        modules.models.queue.status.in_(['Scheduled']),
    ).order_by('id asc'):
        if queue.get_scheduled_for()[0] > now:
            tsiitf_absolute += 1
        else:
            tsiitp_absolute += 1
    if tsi:
        tsiitf_relative = (tsiitf_absolute * 100.00) / (tsi * 1.00)
        tsiitp_relative = (tsiitp_absolute * 100.00) / (tsi * 1.00)
    usage = [{
        'key': 'Total Scheduled Items',
        'value': modules.utilities.get_integer(tsi),
    }, {
        'key': 'Total Scheduled Items (in the future)',
        'value': '%(absolute)s (%(relative)s%%)' % {
            'absolute': modules.utilities.get_integer(tsiitf_absolute),
            'relative': modules.utilities.get_float(tsiitf_relative),
        },
    }, {
        'key': 'Total Scheduled Items (in the past)',
        'value': '%(absolute)s (%(relative)s%%)' % {
            'absolute': modules.utilities.get_integer(tsiitp_absolute),
            'relative': modules.utilities.get_float(tsiitp_relative),
        },
    }, {
        'key': 'Total Backlogged Items',
        'value': modules.utilities.get_integer(g.mysql.query(
            modules.models.queue
        ).filter(
            modules.models.queue.status.in_(['Backlogged']),
        ).order_by('id asc').count()),
    }, {
        'key': 'Email Sent This Month',
        'value': modules.utilities.get_integer(g.mysql.query(
            modules.models.queue
        ).filter(
            func.year(modules.models.queue.delivered_at) == now.year,
            func.month(modules.models.queue.delivered_at) == now.month,
            modules.models.queue.status == 'Delivered',
        ).order_by('id asc').count()),
    }, {
        'key': 'Email Sent To Date',
        'value': modules.utilities.get_integer(g.mysql.query(
            modules.models.queue
        ).filter(
            modules.models.queue.status == 'Delivered',
        ).order_by('id asc').count()),
    }, {
        'key': '<strong>Most Usage By User</strong>',
        'value': '<strong>To Date/This Month</strong>',
    }, {
        'key': '',
        'value': '',
    }, {
        'key': '',
        'value': '',
    }, {
        'key': '',
        'value': '',
    }]
    with closing(modules.database.engine.connect()) as connection:
        for index, row in enumerate(list(connection.execute(text(
            '''
            SELECT
                wp_users.ID,
                wp_users.user_email,
                wp_users.user_login,
                COUNT(queues.id)
            FROM wp_users
            INNER JOIN accounts on wp_users.ID = accounts.user_id
            INNER JOIN logs on accounts.id = logs.account_id
            INNER JOIN queues on logs.id = queues.log_id
            WHERE queues.status = :status
            GROUP BY wp_users.ID
            ORDER BY COUNT(queues.id) DESC
            '''
        ), status='Delivered').fetchall())[0:3]):
            usage[index + 7]['key'] = (
                '<a href="mailto:%(email)s" target="_blank">'
                '%(username)s'
                '</a>'
            ) % {
                'email': row[1],
                'username': row[2],
            }
            usage[index + 7]['value'] = '%(all)s/%(some)s' % {
                'all': modules.utilities.get_integer(row[3]),
                'some': modules.utilities.get_integer(connection.execute(
                    text(
                        '''
                        SELECT COUNT(queues.id)
                        FROM queues
                        INNER JOIN logs on logs.id = queues.log_id
                        INNER JOIN accounts on accounts.id = logs.account_id
                        WHERE
                            accounts.user_id = :id
                            AND
                            queues.status = :status
                            AND
                            YEAR(queues.delivered_at) = :year
                            AND
                            MONTH(queues.delivered_at) = :month
                        ORDER BY COUNT(queues.id) DESC
                        '''
                    ),
                    id=row[0],
                    month=now.month,
                    status='Delivered',
                    year=now.year,
                ).fetchone()[0]),
            }
    return render_template(
        'administrators/views/dashboard.html',
        backups=backups,
        statistics=[
            {
                'key': item['key'],
                'value': g.mysql.query(
                    modules.database.base.metadata.tables[item['table']]
                ).count() if 'table' in item else item['value'],
            }
            for item in [
                {
                    'key': 'Administrators',
                    'table': 'administrators',
                }, {
                    'key': 'Articles',
                    'table': 'articles',
                }, {
                    'key': 'Codes',
                    'table': 'codes',
                }, {
                    'key': 'Templates',
                    'value': g.mysql.query(
                        modules.models.template
                    ).filter(
                        modules.models.template.user == null()
                    ).count(),
                }, {
                    'key': 'Users',
                    'table': 'wp_users',
                }, {
                    'key': 'Proxies',
                    'table': 'proxies',
                }, {
                    'key': 'Accounts',
                    'table': 'accounts',
                }, {
                    'key': 'Templates',
                    'value': g.mysql.query(
                        modules.models.template
                    ).filter(
                        modules.models.template.user != null()
                    ).count(),
                }, {
                    'key': 'Recipes',
                    'table': 'filters',
                }, {
                    'key': 'Logs',
                    'table': 'logs',
                }, {
                    'key': 'Queues',
                    'table': 'queues',
                },
            ]
        ],
        usage=usage,
    )


@blueprint.route('/profile', methods=['GET', 'POST'])
@modules.decorators.requires_administrator
def profile():
    form = modules.forms.administrators_profile(request.form, g.administrator)
    form.id = g.administrator.id
    if request.method == 'POST':
        if form.validate_on_submit():
            form.persist(g.administrator)
            flash('Your profile have been saved successfully.', 'success')
            return redirect(url_for('administrators.profile'))
        flash('Your profile have not been saved successfully.', 'error')
    return render_template('administrators/views/profile.html', form=form)


@blueprint.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    if g.administrator:
        return redirect(
            request.args.get('next') or url_for('administrators.dashboard')
        )
    form = modules.forms.administrators_sign_in(request.form)
    if request.method == 'POST':
        if form.validate_on_submit():
            flash('You have been signed in successfully.', 'success')
            return redirect(
                request.args.get('next') or url_for('administrators.dashboard')
            )
        flash('You have not been signed in successfully.', 'error')
    return render_template('administrators/views/sign_in.html', form=form)


@blueprint.route('/sign-out')
def sign_out():
    if 'administrator' in session:
        del session['administrator']
    flash('You have been signed out successfully.', 'success')
    return redirect(url_for('administrators.dashboard'))


def get_accounts():
    return [('0', 'N/A')] + [
        (str(account.id), account.username)
        for account in g.mysql.query(
            modules.models.account
        ).filter(
            modules.models.account.user == null(),
            modules.models.account.status == 'On'
        ).order_by(
            'username asc'
        ).all()
    ]


def get_templates():
    return [
        (template.id, template.name)
        for template in g.mysql.query(
            modules.models.template
        ).filter(
            modules.models.template.user == null()
        ).order_by(
            'name asc'
        ).all()
    ]
