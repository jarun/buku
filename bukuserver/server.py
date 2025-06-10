#!/usr/bin/env python
# pylint: disable=wrong-import-order, ungrouped-imports
"""Server module."""
import os
import sys
import importlib.metadata
from urllib.parse import urlsplit, urlunsplit, parse_qs

import click
import flask
from flask import Flask, redirect, request, url_for
from flask.cli import FlaskGroup
from flask_admin import Admin
from flasgger import Swagger

from buku import BukuDb, __version__

try:
    from .middleware import ReverseProxyPrefixFix
except ImportError:
    from bukuserver.middleware import ReverseProxyPrefixFix

try:
    from . import api, views, util, _p, _l, gettext, ngettext
except ImportError:
    from bukuserver import api, views, util, _p, _l, gettext, ngettext

FLASK_VERSION = importlib.metadata.version('flask')


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


# handling popup= URL argument
def before_request():
    _post_popup = request.headers.get('Content-Type') != 'application/json' and request.form.get('popup')
    flask.g.popup = request.args.get('popup') or _post_popup

# applying popup= to the redirect URL
def after_request(response):
    if flask.g.popup and 'Location' in response.headers:
        _scheme, _netloc, _path, _query, _fragment = urlsplit(response.headers['Location'])
        _params = parse_qs(_query)
        if not _params.get('popup'):
            _query = '&'.join(s for s in [_query, 'popup=True'] if s)
            response.headers['Location'] = urlunsplit((_scheme, _netloc, _path, _query, _fragment))
    return response


def create_app(db_file=None):
    """create app."""
    app = Flask(__name__)
    db_file = os.getenv('BUKUSERVER_DB_FILE') or db_file
    if db_file and not os.path.dirname(db_file) and not os.path.splitext(db_file)[1]:
        db_file = os.path.join(BukuDb.get_default_dbdir(), db_file + '.db')
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
    app.config['BUKUSERVER_DB_FILE'] = db_file
    reverse_proxy_path = os.getenv('BUKUSERVER_REVERSE_PROXY_PATH')
    if reverse_proxy_path:
        if not reverse_proxy_path.startswith('/'):
            print('Warning: reverse proxy path should include preceding slash')
        if reverse_proxy_path.endswith('/'):
            print('Warning: reverse proxy path should not include trailing slash')
        app.config['REVERSE_PROXY_PATH'] = reverse_proxy_path
        ReverseProxyPrefixFix(app)
    bukudb = BukuDb(dbfile=db_file)
    app.config['FLASK_ADMIN_SWATCH'] = (os.getenv('BUKUSERVER_THEME') or 'default').lower()
    app.config['BUKUSERVER_LOCALE'] = os.getenv('BUKUSERVER_LOCALE') or 'en'
    _dir = os.path.dirname(os.path.realpath(__file__))
    app.config['SWAGGER'] = {'title': 'Bukuserver API', 'doc_dir': os.path.join(_dir, 'apidocs')}
    app.app_context().push()
    setattr(flask.g, 'bukudb', bukudb)
    init_locale(app)
    app.before_request(before_request)
    app.after_request(after_request)

    @app.shell_context_processor
    def shell_context():
        """Shell context definition."""
        return {'app': app, 'bukudb': bukudb}

    app.jinja_env.filters.update(util.JINJA_FILTERS)
    app.jinja_env.globals.update(_p=_p, dbfile=bukudb.dbfile, dbname=bukudb.dbname)

    admin = Admin(
        app, name='buku server', template_mode='bootstrap3',
        index_view=views.CustomAdminIndexView(
            template='bukuserver/home.html', url='/'
        )
    )
    Swagger(app, template_file=os.path.join(_dir, 'apidocs', 'template.yml'))
    # routing
    #  api
    app.add_url_rule('/api/tags', 'get_all_tags', api.get_all_tags, methods=['GET'], strict_slashes=False)
    app.add_url_rule('/api/tags/<tag>', view_func=api.ApiTagView.as_view('tag'), methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule('/api/bookmarks', view_func=api.ApiBookmarksView.as_view('bookmarks'), methods=['GET', 'POST', 'DELETE'])
    app.add_url_rule('/api/bookmarks/<int:index>', view_func=api.ApiBookmarkView.as_view('bookmark'), methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule('/api/bookmarks/refresh', 'bookmarks_refresh', api.refresh_bookmark, defaults={'index': None}, methods=['POST'])
    app.add_url_rule('/api/bookmarks/<int:index>/refresh', 'bookmark_refresh', api.refresh_bookmark, methods=['POST'])
    app.add_url_rule('/api/bookmarks/<int:index>/tiny', 'tiny_url', api.get_tiny_url, methods=['GET'])
    app.add_url_rule('/api/bookmarks/<int:start_index>/<int:end_index>',
                     view_func=api.ApiBookmarkRangeView.as_view('bookmark_range'), methods=['GET', 'PUT', 'DELETE'])
    app.add_url_rule('/api/bookmarks/search', view_func=api.ApiBookmarkSearchView.as_view('bookmarks_search'), methods=['GET', 'DELETE'])
    app.add_url_rule('/api/network_handle', 'network_handle', api.handle_network, methods=['POST'])
    app.add_url_rule('/api/fetch_data', 'fetch_data', api.fetch_data, methods=['POST'])

    #  non api
    @app.route('/favicon.ico')
    def favicon():
        return redirect(url_for('static', filename='bukuserver/favicon.svg'), code=301)  # permanent redirect

    app.add_url_rule('/bookmarklet', 'bookmarklet', api.bookmarklet_redirect, methods=['GET'])
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
            "version": FLASK_VERSION,
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
