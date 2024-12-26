try:  # as per Flask-Admin-1.6.1
    try:
        from flask_babelex import gettext, ngettext, pgettext, lazy_gettext, lazy_pgettext, LazyString
    except ImportError:
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

__all__ = ['_', '_p', '_l', '_lp', '_key', 'gettext', 'pgettext', 'ngettext', 'lazy_gettext', 'lazy_pgettext', 'LazyString']
