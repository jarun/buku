from contextlib import contextmanager
import threading
import os.path
import flask
import buku

try:
    from flask_babel import gettext, ngettext, pgettext, lazy_gettext, lazy_pgettext, LazyString
except ImportError:
    from flask_admin.babel import gettext as _gettext, ngettext, lazy_gettext
    gettext = lambda s, *a, **kw: (s if not kw else _gettext(s, *a, **kw))
    pgettext = lambda ctx, s, *a, **kw: gettext(s, *a, **kw)
    lazy_pgettext = lambda ctx, s, *a, **kw: lazy_gettext(s, *a, **kw)
    LazyString = lambda func, *args, **kwargs: func(*args, **kwargs)

_, _p, _l, _lp = gettext, pgettext, lazy_gettext, lazy_pgettext

def _key(s):  # replicates ad-hoc implementation of "get key from lazy string" used in flask-admin
    try:
        return s._args[0]  # works with _/_l, but not with _lp due to the extra context argument
    except Exception:
        return str(s)


def _make_db_holder():
    class DB:
        _lock = threading.RLock()  # thread-safe, just in case
        _dir = buku.BukuDb.get_default_dbdir()
        _db = _name = _file = None

        @property
        def bukudb(self):
            with self._lock:
                return self._db

        def metadata(self):
            with self._lock:
                return {'name': self._name, 'file': self._file, 'dir': self._dir}

        def path_from_name(self, name: str, *, lock=True):
            if not lock:
                return os.path.join(self._dir, name + '.db')
            with self._lock:
                return self.path_from_name(name, lock=False)

        def path(self, s: str, *, lock=True):
            return (s if not s or os.path.dirname(s) else self.path_from_name(s, lock=lock))

        def _init(self, dbpath: str, *, lock=True):
            dbpath = self.path(dbpath, lock=lock)
            flask.current_app.logger.debug(f'Instantiating DB connection for file: {dbpath}')
            return buku.BukuDb(dbfile=dbpath)

        def init(self, dbpath: str):
            with self._lock:
                self._db = self._init(dbpath, lock=False)
                self._dir, self._file = self._db.db_dir_and_file
                self._name = self._db.dbname
                setattr(flask.g, 'bukudb', self._db)
                flask.current_app.jinja_env.globals.update(dbname=self._name, dbfile=os.path.join(self._dir, self._file))
                return self._db

        @contextmanager
        def get(self):
            """get bukudb instance"""
            db = self._db
            if db:
                yield db
            else:
                db = self._init(flask.current_app.config.get('BUKUSERVER_DB_FILE', None))
                yield db
                db.close()

    return DB()

DB = _make_db_holder()


__all__ = ['_', '_p', '_l', '_lp', '_key', 'gettext', 'pgettext', 'ngettext', 'lazy_gettext', 'lazy_pgettext', 'LazyString', 'DB']
