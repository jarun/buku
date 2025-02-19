#!/usr/bin/env python
# pylint: disable=wrong-import-order, ungrouped-imports
"""Server module."""
import os
import sys
from typing import Union  # NOQA; type: ignore

from flask.cli import FlaskGroup
from flask_admin import Admin
from flask_api import FlaskAPI

import buku
from buku import BukuDb, __version__

try:
    from .middleware import ReverseProxyPrefixFix
except ImportError:
    from bukuserver.middleware import ReverseProxyPrefixFix
import click
import flask
from flask import __version__ as flask_version  # type: ignore
from flask import current_app, redirect, request, url_for

try:
    from . import api, views, util, _p, _l, gettext, ngettext
    from response import Response
except ImportError:
    from bukuserver import api, views, util, _p, _l, gettext, ngettext
    from bukuserver.response import Response


STATISTIC_DATA = None

def _fetch_data():
    url = request.data.get('url')
    try:
        return (None if not url else buku.fetch_data(url))
    except Exception as e:
        current_app.logger.debug(str(e))
        return None

def handle_network():
    res = _fetch_data()
    res_dict = res and {'title': res.title, 'description': res.desc, 'tags': res.keywords,
                        'recognized mime': int(res.mime), 'bad url': int(res.bad)}
    return (Response.FAILURE() if not res else Response.SUCCESS(data=res_dict))

def fetch_data():
    res = _fetch_data()
    return (Response.FAILURE() if not res else Response.SUCCESS(data=res._asdict()))


def refresh_bookmark(rec_id: Union[int, None]):
    result_flag = getattr(flask.g, 'bukudb', api.get_bukudb()).refreshdb(rec_id or 0, request.form.get('threads', 4))
    return Response.from_flag(result_flag)


get_tiny_url = lambda rec_id: Response.REMOVED()


_BOOL_VALUES = {'true': True, '1': True, 'false': False, '0': False}
def get_bool_from_env_var(key: str, default_value: bool = False) -> bool:
    """Get bool value from env var."""
    return _BOOL_VALUES.get(os.getenv(key, '').lower(), default_value)


def init_locale(app, context_processor=lambda: {}):
    try:  # as per Flask-Admin-1.6.1
        try:
            from flask_babelex import Babel
            Babel(app).localeselector(lambda: app.config['BUKUSERVER_LOCALE'])
        except ImportError:
            from flask_babel import Babel
            Babel().init_app(app, locale_selector=lambda: app.config['BUKUSERVER_LOCALE'])
        app.context_processor(lambda: {'lang': app.config['BUKUSERVER_LOCALE'] or 'en', **context_processor()})
    except Exception as e:
        app.jinja_env.add_extension('jinja2.ext.i18n')
        app.jinja_env.install_gettext_callables(gettext, ngettext, newstyle=True)
        app.logger.warning(f'failed to init locale ({e})')
        app.context_processor(lambda: {'lang': '', **context_processor()})


def create_app(db_file=None):
    """create app."""
    app = FlaskAPI(__name__)
    os.environ.setdefault('FLASK_DEBUG', ('1' if get_bool_from_env_var('BUKUSERVER_DEBUG') else '0'))
    per_page = int(os.getenv('BUKUSERVER_PER_PAGE', str(views.DEFAULT_PER_PAGE)))
    per_page = per_page if per_page > 0 else views.DEFAULT_PER_PAGE
    app.config['BUKUSERVER_PER_PAGE'] = per_page
    url_render_mode = os.getenv('BUKUSERVER_URL_RENDER_MODE', views.DEFAULT_URL_RENDER_MODE)
    if url_render_mode not in ('full', 'netloc', 'netloc-tag'):
        url_render_mode = views.DEFAULT_URL_RENDER_MODE
    app.config['BUKUSERVER_URL_RENDER_MODE'] = url_render_mode
    app.config['SECRET_KEY'] = os.getenv('BUKUSERVER_SECRET_KEY') or os.urandom(24)
    app.config['BUKUSERVER_READONLY'] = \
        get_bool_from_env_var('BUKUSERVER_READONLY')
    app.config['BUKUSERVER_DISABLE_FAVICON'] = \
        get_bool_from_env_var('BUKUSERVER_DISABLE_FAVICON', True)
    app.config['BUKUSERVER_OPEN_IN_NEW_TAB'] = \
        get_bool_from_env_var('BUKUSERVER_OPEN_IN_NEW_TAB')
    app.config['BUKUSERVER_DB_FILE'] = os.getenv('BUKUSERVER_DB_FILE') or db_file
    reverse_proxy_path = os.getenv('BUKUSERVER_REVERSE_PROXY_PATH')
    if reverse_proxy_path:
        if not reverse_proxy_path.startswith('/'):
            print('Warning: reverse proxy path should include preceding slash')
        if reverse_proxy_path.endswith('/'):
            print('Warning: reverse proxy path should not include trailing slash')
        app.config['REVERSE_PROXY_PATH'] = reverse_proxy_path
        ReverseProxyPrefixFix(app)
    bukudb = BukuDb(dbfile=app.config['BUKUSERVER_DB_FILE'])
    app.config['FLASK_ADMIN_SWATCH'] = (os.getenv('BUKUSERVER_THEME') or 'default').lower()
    app.config['BUKUSERVER_LOCALE'] = os.getenv('BUKUSERVER_LOCALE') or 'en'
    app.app_context().push()
    setattr(flask.g, 'bukudb', bukudb)
    init_locale(app)

    @app.shell_context_processor
    def shell_context():
        """Shell context definition."""
        return {'app': app, 'bukudb': bukudb}

    app.jinja_env.filters.update(util.JINJA_FILTERS)
    app.jinja_env.globals.update(_p=_p)

    admin = Admin(
        app, name='buku server', template_mode='bootstrap3',
        index_view=views.CustomAdminIndexView(
            template='bukuserver/home.html', url='/'
        )
    )
    # routing
    #  api
    tag_api_view = api.ApiTagView.as_view('tag_api')
    app.add_url_rule('/api/tags', defaults={'tag': None}, view_func=tag_api_view, methods=['GET'], strict_slashes=False)
    app.add_url_rule('/api/tags/<tag>', view_func=tag_api_view, methods=['GET', 'PUT', 'DELETE'])
    bookmark_api_view = api.ApiBookmarkView.as_view('bookmark_api')
    app.add_url_rule('/api/bookmarks', defaults={'rec_id': None}, view_func=bookmark_api_view, methods=['GET', 'POST', 'DELETE'])
    app.add_url_rule('/api/bookmarks/<int:rec_id>', view_func=bookmark_api_view, methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule('/api/bookmarks/refresh', 'refresh_bookmark', refresh_bookmark, defaults={'rec_id': None}, methods=['POST'])
    app.add_url_rule('/api/bookmarks/<int:rec_id>/refresh', 'refresh_bookmark', refresh_bookmark, methods=['POST'])
    app.add_url_rule('/api/bookmarks/<int:rec_id>/tiny', 'get_tiny_url', get_tiny_url, methods=['GET'])
    app.add_url_rule('/api/network_handle', 'network_handle', handle_network, methods=['POST'])
    app.add_url_rule('/api/fetch_data', 'fetch_data', fetch_data, methods=['POST'])
    bookmark_range_api_view = api.ApiBookmarkRangeView.as_view('bookmark_range_api')
    app.add_url_rule(
        '/api/bookmarks/<int:starting_id>/<int:ending_id>',
        view_func=bookmark_range_api_view, methods=['GET', 'PUT', 'DELETE'])
    bookmark_search_api_view = api.ApiBookmarkSearchView.as_view('bookmark_search_api')
    app.add_url_rule('/api/bookmarks/search', view_func=bookmark_search_api_view, methods=['GET', 'DELETE'])
    bookmarklet_view = api.BookmarkletView.as_view('bookmarklet')
    app.add_url_rule('/bookmarklet', view_func=bookmarklet_view, methods=['GET'])

    #  non api
    @app.route('/favicon.ico')
    def favicon():
        return redirect(url_for('static', filename='bukuserver/favicon.svg'), code=301)  # permanent redirect

    admin.add_view(views.BookmarkModelView(bukudb, _l('Bookmarks')))
    admin.add_view(views.TagModelView(bukudb, _l('Tags')))
    admin.add_view(views.StatisticView(bukudb, _l('Statistic'), endpoint='statistic'))
    return app


class CustomFlaskGroup(FlaskGroup):  # pylint: disable=too-few-public-methods
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for idx, param in enumerate(self.params):
            if param.name == "version":
                self.params[idx].help = "Show the program version"
                self.params[idx].callback = get_custom_version


def get_custom_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    message = "\n".join(["%(app_name)s %(app_version)s", "Flask %(version)s", "Python %(python_version)s"])
    click.echo(
        message
        % {
            "app_name": "buku",
            "app_version": __version__,
            "version": flask_version,
            "python_version": sys.version,
        },
        color=ctx.color,
    )
    ctx.exit()


@click.group(cls=CustomFlaskGroup, create_app=create_app)
def cli():
    """This is a script for the bukuserver application."""


if __name__ == '__main__':
    cli()
