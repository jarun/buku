#!/usr/bin/env python3
#
# Bookmark management utility
#
# Copyright © 2015-2025 Arun Prakash Jana <engineerarun@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with buku.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import annotations  # for |

import argparse
import calendar
import codecs
import collections
import contextlib
import email.message
import json
import locale
import logging
import os
import platform
import random
import re
import shutil
import signal
import sqlite3
import struct
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import unicodedata
import webbrowser
from enum import Enum
from itertools import chain
from functools import total_ordering
from subprocess import DEVNULL, PIPE, Popen
from typing import Any, Dict, List, Optional, Tuple, NamedTuple
from collections.abc import Sequence, Set, Callable
from warnings import warn
import xml.etree.ElementTree as ET
from urllib.parse import urlparse  # urllib3.util.parse_url() encodes netloc

import urllib3
from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector
from urllib3.util import Retry, make_headers

try:
    from mypy_extensions import TypedDict
except ImportError:
    TypedDict = None  # type: ignore

__version__ = '5.0'
__author__ = 'Arun Prakash Jana <engineerarun@gmail.com>'
__license__ = 'GPLv3'

# Global variables
INTERRUPTED = False  # Received SIGINT
DELIM = ','  # Delimiter used to store tags in DB
SKIP_MIMES = {'.pdf', '.txt'}
PROMPTMSG = 'buku (? for help): '  # Prompt message string

strip_delim = lambda s, delim=DELIM, sub=' ': str(s).replace(delim, sub)
taglist = lambda ss: sorted(set(s.lower().strip() for s in ss if (s or '').strip()))
like_escape = lambda s, c='`': s.replace(c, c+c).replace('_', c+'_').replace('%', c+'%')
split_by_marker = lambda s: re.split(r'\s+(?=[.:>#*])', s)

def taglist_str(tag_str, convert=None):
    tags = taglist(tag_str.split(DELIM))
    return delim_wrap(DELIM.join(tags if not convert else taglist(convert(tags))))

def filter_from(values, subset, *, exclude=False):
    subset, exclude = set(subset), bool(exclude)
    return [x for x in values if (x in subset) != exclude]


# Default format specifiers to print records
ID_STR = '%d. %s [%s]\n'
ID_DB_STR = '%d. %s'
MUTE_STR = '%s (L)\n'
URL_STR = '   > %s\n'
DESC_STR = '   + %s\n'
DESC_WRAP = '%s%s'
TAG_STR = '   # %s\n'
TAG_WRAP = '%s%s'

# Colormap for color output from "googler" project
COLORMAP = {k: '\x1b[%sm' % v for k, v in {
    'a': '30', 'b': '31', 'c': '32', 'd': '33',
    'e': '34', 'f': '35', 'g': '36', 'h': '37',
    'i': '90', 'j': '91', 'k': '92', 'l': '93',
    'm': '94', 'n': '95', 'o': '96', 'p': '97',
    'A': '30;1', 'B': '31;1', 'C': '32;1', 'D': '33;1',
    'E': '34;1', 'F': '35;1', 'G': '36;1', 'H': '37;1',
    'I': '90;1', 'J': '91;1', 'K': '92;1', 'L': '93;1',
    'M': '94;1', 'N': '95;1', 'O': '96;1', 'P': '97;1',
    'x': '0', 'X': '1', 'y': '7', 'Y': '7;1', 'z': '2',
}.items()}

# DB flagset values
[FLAG_NONE, FLAG_IMMUTABLE] = [0x00, 0x01]

FIELD_FILTER = {
    1: ('id', 'url'),
    2: ('id', 'url', 'tags'),
    3: ('id', 'title'),
    4: ('id', 'url', 'title', 'tags'),
    5: ('id', 'title', 'tags'),
    10: ('url',),
    20: ('url', 'tags'),
    30: ('title',),
    40: ('url', 'title', 'tags'),
    50: ('title', 'tags'),
}
ALL_FIELDS = ('id', 'url', 'title', 'desc', 'tags')
JSON_FIELDS = {'id': 'index', 'url': 'uri', 'desc': 'description'}

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64; rv:137.0) Gecko/20100101 Firefox/137.0'
MYHEADERS = None  # Default dictionary of headers
MYPROXY = None  # Default proxy
TEXT_BROWSERS = ['elinks', 'links', 'links2', 'lynx', 'w3m', 'www-browser']
IGNORE_FF_BOOKMARK_FOLDERS = frozenset(["placesRoot", "bookmarksMenuFolder"])
PERMANENT_REDIRECTS = {301, 308}

# IntSet: TypeAlias = Set[int] | range      # TODO: use after dropping 3.9
# Ints: TypeAlias = Sequence[int] | IntSet
# IntOrInts: TypeAlias = int | Ints
# T = TypeVar('T')
# Values: TypeAlias = Sequence[T] | Set[T]
# del T

# Set up logging
LOGGER = logging.getLogger()
LOGDBG = LOGGER.debug
LOGERR = LOGGER.error

# Define the default path to ca-certificates
# In Linux distros with openssl, it is /etc/ssl/certs/ca-certificates.crt
# Fall back to use `certifi` otherwise
if sys.platform.startswith('linux') and os.path.isfile('/etc/ssl/certs/ca-certificates.crt'):
    CA_CERTS = '/etc/ssl/certs/ca-certificates.crt'
else:
    import certifi
    CA_CERTS = certifi.where()


class BukuCrypt:
    """Class to handle encryption and decryption of
    the database file. Functionally a separate entity.

    Involves late imports in the static functions but it
    saves ~100ms each time. Given that encrypt/decrypt are
    not done automatically and any one should be called at
    a time, this doesn't seem to be an outrageous approach.
    """

    # Crypto constants
    BLOCKSIZE = 0x10000  # 64 KB blocks
    SALT_SIZE = 0x20
    CHUNKSIZE = 0x80000  # Read/write 512 KB chunks

    @staticmethod
    def get_filehash(filepath):
        """Get the SHA256 hash of a file.

        Parameters
        ----------
        filepath : str
            Path to the file.

        Returns
        -------
        hash : bytes
            Hash digest of file.
        """

        from hashlib import sha256

        with open(filepath, 'rb') as fp:
            hasher = sha256()
            buf = fp.read(BukuCrypt.BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = fp.read(BukuCrypt.BLOCKSIZE)

            return hasher.digest()

    @staticmethod
    def encrypt_file(iterations, dbfile=None):
        """Encrypt the bookmarks database file.

        Parameters
        ----------
        iterations : int
            Number of iterations for key generation.
        dbfile : str, optional
            Custom database file path (including filename).
        """

        try:
            from getpass import getpass
            from hashlib import sha256

            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        except ImportError:
            LOGERR('cryptography lib(s) missing')
            sys.exit(1)

        if iterations < 1:
            LOGERR('Iterations must be >= 1')
            sys.exit(1)

        if not dbfile:
            dbfile = os.path.join(BukuDb.get_default_dbdir(), 'bookmarks.db')
        encfile = dbfile + '.enc'

        db_exists = os.path.exists(dbfile)
        enc_exists = os.path.exists(encfile)

        if db_exists and not enc_exists:
            pass
        elif not db_exists:
            LOGERR('%s missing. Already encrypted?', dbfile)
            sys.exit(1)
        else:
            # db_exists and enc_exists
            LOGERR('Both encrypted and flat DB files exist!')
            sys.exit(1)

        password = getpass()
        passconfirm = getpass()
        if not password or not passconfirm:
            LOGERR('Empty password')
            sys.exit(1)
        if password != passconfirm:
            LOGERR('Passwords do not match')
            sys.exit(1)

        try:
            # Get SHA256 hash of DB file
            dbhash = BukuCrypt.get_filehash(dbfile)
        except Exception as e:
            LOGERR(e)
            sys.exit(1)

        # Generate random 256-bit salt and key
        salt = os.urandom(BukuCrypt.SALT_SIZE)
        key = ('%s%s' % (password, salt.decode('utf-8', 'replace'))).encode('utf-8')
        for _ in range(iterations):
            key = sha256(key).digest()

        iv = os.urandom(16)
        encryptor = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        ).encryptor()
        filesize = os.path.getsize(dbfile)

        try:
            with open(dbfile, 'rb') as infp, open(encfile, 'wb') as outfp:
                outfp.write(struct.pack('<Q', filesize))
                outfp.write(salt)
                outfp.write(iv)

                # Embed DB file hash in encrypted file
                outfp.write(dbhash)

                while True:
                    chunk = infp.read(BukuCrypt.CHUNKSIZE)
                    if len(chunk) == 0:
                        break
                    if len(chunk) % 16 != 0:
                        chunk = b'%b%b' % (chunk, b' ' * (16 - len(chunk) % 16))

                    outfp.write(encryptor.update(chunk))

                outfp.write(encryptor.finalize())

            os.remove(dbfile)
            print('File encrypted')
            sys.exit(0)
        except Exception as e:
            with contextlib.suppress(FileNotFoundError):
                os.remove(encfile)
            LOGERR(e)
            sys.exit(1)

    @staticmethod
    def decrypt_file(iterations, dbfile=None):
        """Decrypt the bookmarks database file.

        Parameters
        ----------
        iterations : int
            Number of iterations for key generation.
        dbfile : str, optional
            Custom database file path (including filename).
            The '.enc' suffix must be omitted.
        """

        try:
            from getpass import getpass
            from hashlib import sha256

            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        except ImportError:
            LOGERR('cryptography lib(s) missing')
            sys.exit(1)

        if iterations < 1:
            LOGERR('Decryption failed')
            sys.exit(1)

        if not dbfile:
            dbfile = os.path.join(BukuDb.get_default_dbdir(), 'bookmarks.db')
        else:
            dbfile = os.path.abspath(dbfile)
            dbpath, filename = os.path.split(dbfile)

        encfile = dbfile + '.enc'

        enc_exists = os.path.exists(encfile)
        db_exists = os.path.exists(dbfile)

        if enc_exists and not db_exists:
            pass
        elif not enc_exists:
            LOGERR('%s missing', encfile)
            sys.exit(1)
        else:
            # db_exists and enc_exists
            LOGERR('Both encrypted and flat DB files exist!')
            sys.exit(1)

        password = getpass()
        if not password:
            LOGERR('Decryption failed')
            sys.exit(1)

        try:
            with open(encfile, 'rb') as infp:
                size = struct.unpack('<Q', infp.read(struct.calcsize('Q')))[0]

                # Read 256-bit salt and generate key
                salt = infp.read(32)
                key = ('%s%s' % (password, salt.decode('utf-8', 'replace'))).encode('utf-8')
                for _ in range(iterations):
                    key = sha256(key).digest()

                iv = infp.read(16)
                decryptor = Cipher(
                    algorithms.AES(key),
                    modes.CBC(iv),
                    backend=default_backend(),
                ).decryptor()

                # Get original DB file's SHA256 hash from encrypted file
                enchash = infp.read(32)

                with open(dbfile, 'wb') as outfp:
                    while True:
                        chunk = infp.read(BukuCrypt.CHUNKSIZE)
                        if len(chunk) == 0:
                            break
                        outfp.write(decryptor.update(chunk))
                    outfp.write(decryptor.finalize())
                    outfp.truncate(size)

            # Match hash of generated file with that of original DB file
            dbhash = BukuCrypt.get_filehash(dbfile)
            if dbhash != enchash:
                os.remove(dbfile)
                LOGERR('Decryption failed')
                sys.exit(1)
            else:
                os.remove(encfile)
                print('File decrypted')
        except struct.error:
            with contextlib.suppress(FileNotFoundError):
                os.remove(dbfile)
            LOGERR('Tainted file')
            sys.exit(1)
        except Exception as e:
            with contextlib.suppress(FileNotFoundError):
                os.remove(dbfile)
            LOGERR(e)
            sys.exit(1)


@total_ordering
class SortKey:
    def __init__(self, value, ascending=True):
        self.value, self.ascending = value, bool(ascending)

    def __eq__(self, other):
        other = (other.value if isinstance(other, SortKey) else other)
        return self.value == other

    def __lt__(self, other):
        other = (other.value if isinstance(other, SortKey) else other)
        return self.value != other and ((self.value < other) == self.ascending)

    def __repr__(self):
        return ('+' if self.ascending else '-') + repr(self.value)


class FetchResult(NamedTuple):
    url: str                            # resulting URL after following PERMANENT redirects
    title: str = ''
    desc: str = ''
    keywords: str = ''
    mime: bool = False
    bad: bool = False
    fetch_status: Optional[int] = None  # None means no fetch occurred (e.g. due to a network error)

    def tag_redirect(self, pattern: str = None) -> str:
        return ('' if self.fetch_status not in PERMANENT_REDIRECTS else (pattern or 'http:{}').format(self.fetch_status))

    def tag_error(self, pattern: str = None) -> str:
        return ('' if (self.fetch_status or 0) < 400 else (pattern or 'http:{}').format(self.fetch_status))

    def tags(self, *, keywords: bool = True, redirect: bool | str = False, error: bool | str = False) -> str:
        _redirect = redirect and self.tag_redirect(None if redirect is True else redirect)
        _error = error and self.tag_error(None if error is True else error)
        return DELIM.join(taglist((keywords and self.keywords or '').split(DELIM) + [_redirect, _error]))


class BookmarkVar(NamedTuple):
    """Bookmark data named tuple"""
    id: int
    url: str
    title: Optional[str] = None
    tags_raw: str = ''
    desc: str = ''
    flags: int = FLAG_NONE

    @property
    def immutable(self) -> bool:
        return bool(self.flags & FLAG_IMMUTABLE)

    @property
    def tags(self) -> str:
        return self.tags_raw[1:-1]

    @property
    def taglist(self) -> List[str]:
        return [x for x in self.tags_raw.split(',') if x]

    @property
    def netloc(self) -> str:
        return get_netloc(self.url) or ''

bookmark_vars = lambda xs: ((x if isinstance(x, BookmarkVar) else BookmarkVar(*x)) for x in xs)


class BukuDb:
    """Abstracts all database operations.

    Attributes
    ----------
    conn : sqlite database connection.
    cur : sqlite database cursor.
    json : string
        Empty string if results should be printed in JSON format to stdout.
        Nonempty string if results should be printed in JSON format to file. The string has to be a valid path.
        None if the results should be printed as human-readable plaintext.
    field_filter : int
        Indicates format for displaying bookmarks. Default is 0.
    chatty : bool
        Sets the verbosity of the APIs. Default is False.
    """

    def __init__(
            self, json: Optional[str] = None, field_filter: int = 0, chatty: bool = False,
            dbfile: Optional[str] = None, colorize: bool = True) -> None:
        """Database initialization API.

        Parameters
        ----------
        json : string
            Empty string if results should be printed in JSON format to stdout.
            Nonempty string if results should be printed in JSON format to file. The string has to be a valid path.
            None if the results should be printed as human-readable plaintext.
        field_filter : int
            Indicates format for displaying bookmarks. Default is 0.
        chatty : bool
            Sets the verbosity of the APIs. Default is False.
        colorize : bool
            Indicates whether color should be used in output. Default is True.
        """

        self.json = json
        self.field_filter = field_filter
        self.chatty = chatty
        self.colorize = colorize
        self.conn, self.cur = BukuDb.initdb(dbfile, self.chatty)
        self.lock = threading.RLock()  # repeatable lock, only blocks *concurrent* access
        self._to_export = None  # type: Optional[Dict[str, str | BookmarkVar]]
        self._to_delete = None  # type: Optional[int | Sequence[int] | Set[int] | range]

    @staticmethod
    def get_default_dbdir():
        """Determine the directory path where dbfile will be stored.

        If $BUKU_DEFAULT_DBDIR is specified, use it
        else if $XDG_DATA_HOME is defined, use $XDG_DATA_HOME/buku
        else if $HOME exists, use $HOME/.local/share/buku
        else if the platform is Windows and %APPDATA% exists, use %APPDATA%\\buku
        else use the current directory.

        Returns
        -------
        str
            Path to database file.
        """

        _get = os.environ.get
        if _get('BUKU_DEFAULT_DBDIR'):
            return os.path.abspath(_get('BUKU_DEFAULT_DBDIR'))
        home_locations = [
            _get('XDG_DATA_HOME'),
            _get('HOME') and os.path.join(_get('HOME'), '.local', 'share'),
            sys.platform == 'win32' and _get('APPDATA'),
        ]
        data_home = next((s for s in home_locations if s), None)
        return (os.path.join(data_home, 'buku') if data_home else os.getcwd())

    @staticmethod
    def initdb(dbfile: Optional[str] = None, chatty: bool = False) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
        """Initialize the database connection.

        Create DB file and/or bookmarks table if they don't exist.
        Alert on encryption options on first execution.

        Parameters
        ----------
        dbfile : str, optional
            Custom database file path (including filename).
        chatty : bool
            If True, shows informative message on DB creation.

        Returns
        -------
        tuple
            (connection, cursor).
        """

        if not dbfile:
            dbpath = BukuDb.get_default_dbdir()
            filename = 'bookmarks.db'
            dbfile = os.path.join(dbpath, filename)
        else:
            dbfile = os.path.abspath(dbfile)
            dbpath, filename = os.path.split(dbfile)

        try:
            if not os.path.exists(dbpath):
                os.makedirs(dbpath)
        except Exception as e:
            LOGERR(e)
            os._exit(1)

        db_exists = os.path.exists(dbfile)
        enc_exists = os.path.exists(dbfile + '.enc')

        if db_exists and not enc_exists:
            pass
        elif enc_exists and not db_exists:
            LOGERR('Unlock database first')
            sys.exit(1)
        elif db_exists and enc_exists:
            LOGERR('Both encrypted and flat DB files exist!')
            sys.exit(1)
        elif chatty:
            # not db_exists and not enc_exists
            print('DB file is being created at %s.\nYou should encrypt it.' % dbfile)

        try:
            # Create a connection
            conn = sqlite3.connect(dbfile, check_same_thread=False)
            conn.create_function('REGEXP', 2, regexp)
            conn.create_function('NETLOC', 1, get_netloc)
            cur = conn.cursor()

            # Create table if it doesn't exist
            # flags: designed to be extended in future using bitwise masks
            # Masks:
            #     0b00000001: set title immutable
            cur.execute('CREATE TABLE if not exists bookmarks ('
                        'id integer PRIMARY KEY, '
                        'URL text NOT NULL UNIQUE, '
                        'metadata text default \'\', '
                        'tags text default \',\', '
                        'desc text default \'\', '
                        'flags integer default 0)')
            conn.commit()
        except Exception as e:
            LOGERR('initdb(): %s', e)
            raise e

        return (conn, cur)

    @property
    def dbfile(self) -> str:
        return next(path for _, name, path in self.conn.execute('PRAGMA database_list') if name == 'main')

    @property
    def dbname(self) -> str:
        return os.path.basename(self.dbfile).removesuffix('.db')

    def _fetch(self, query: str, *args, lock: bool = True) -> List[BookmarkVar]:
        if not lock:
            self.cur.execute(query, args)
            return [BookmarkVar(*x) for x in self.cur.fetchall()]
        with self.lock:
            return self._fetch(query, *args, lock=False)

    def _fetch_first(self, query: str, *args, lock: bool = True) -> Optional[BookmarkVar]:
        rows = self._fetch(query + ' LIMIT 1', *args, lock=lock)
        return rows[0] if rows else None

    def _ordering(self, fields=['+id'], for_db=True) -> List[Tuple[str, bool]]:
        """Converts field list to ordering parameters (for DB query or entity list sorting).
        Fields are listed in priority order, with '+'/'-' prefix signifying ASC/DESC; assuming ASC if not specified.
        Other than names from DB, you can pass those from JSON export."""
        names = {'index': 'id', 'uri': 'url', 'description': 'desc', **({'title': 'metadata'} if for_db else {'metadata': 'title'})}
        valid = list(names) + list(names.values()) + ['tags', 'netloc']
        _fields = [(re.sub(r'^[+-]', '', s), not s.startswith('-')) for s in (fields or [])]
        _fields = [(names.get(field, field), direction) for field, direction in _fields if field in valid]
        return _fields or [('id', True)]

    def _sort(self, records: List[BookmarkVar], fields=['+id'], ignore_case=True) -> List[BookmarkVar]:
        text_fields = (set() if not ignore_case else {'url', 'desc', 'title', 'tags', 'netloc'})
        get = lambda x, k: (getattr(x, k) if k not in text_fields else str(getattr(x, k) or '').lower())
        order = self._ordering(fields, for_db=False)
        return sorted(bookmark_vars(records), key=lambda x: [SortKey(get(x, k), ascending=asc) for k, asc in order])

    def _order(self, fields=['+id'], ignore_case=True) -> str:
        """Converts field list to SQL 'ORDER BY' parameters. (See also BukuDb._ordering().)"""
        text_fields = (set() if not ignore_case else {'url', 'desc', 'metadata', 'tags'})
        get = lambda field: ('LOWER(NETLOC(url))' if field == 'netloc' else field if field not in text_fields else f'LOWER({field})')
        return ', '.join(f'{get(field)} {"ASC" if direction else "DESC"}' for field, direction in self._ordering(fields))

    def get_rec_all(self, *, lock: bool = True, order: List[str] = ['id']):
        """Get all the bookmarks in the database.

        Parameters
        ----------
        lock : bool
            Whether to restrict concurrent access (True by default).
        order : list of str
            Order description (fields from JSON export or DB, prepended with '+'/'-' for ASC/DESC).

        Returns
        -------
        list
            A list of tuples representing bookmark records.
        """

        return self._fetch(f'SELECT * FROM bookmarks ORDER BY {self._order(order)}', lock=lock)

    def get_rec_by_id(self, index: int, *, lock: bool = True) -> Optional[BookmarkVar]:
        """Get a bookmark from database by its ID.

        Parameters
        ----------
        index : int
            DB index of bookmark record.
        lock : bool
            Whether to restrict concurrent access (True by default).

        Returns
        -------
        BookmarkVar or None
            Bookmark data, or None if index is not found.
        """

        return self._fetch_first('SELECT * FROM bookmarks WHERE id = ?', index, lock=lock)

    def get_rec_all_by_ids(self, indices: Sequence[int] | Set[int] | range, *, lock: bool = True, order: List[str] = ['id']):  # Ints
        """Get all the bookmarks in the database.

        Parameters
        ----------
        indices : int[] | int{} | range
            DB indices of bookmark records.
        lock : bool
            Whether to restrict concurrent access (True by default).
        order : list of str
            Order description (fields from JSON export or DB, prepended with '+'/'-' for ASC/DESC).

        Returns
        -------
        list
            A list of tuples representing bookmark records.
        """

        _order, placeholder = self._order(order), ', '.join(['?'] * len(indices))
        return indices and self._fetch(f'SELECT * FROM bookmarks WHERE id IN ({placeholder}) ORDER BY {_order}',
                                       *list(indices), lock=lock)

    def get_rec_id(self, url: str, *, lock: bool = True):
        """Check if URL already exists in DB.

        Parameters
        ----------
        url : str
            A URL to search for in the DB.
        lock : bool
            Whether to restrict concurrent access (True by default).

        Returns
        -------
        int
            DB index, or None if URL not found in DB.
        """

        row = self._fetch_first('SELECT * FROM bookmarks WHERE url = ?', url, lock=lock)
        return row and row.id

    def get_rec_ids(self, urls: Sequence[str] | Set[str], *, lock: bool = True):  # Values[str]
        """Check if URL already exists in DB.

        Parameters
        ----------
        urls : str[] | str{}
            URLs to search for in the DB.
        lock : bool
            Whether to restrict concurrent access (True by default).

        Returns
        -------
        list
            A list of DB indices.
        """

        if not urls:
            return []
        if not lock:
            placeholder = ', '.join(['?'] * len(urls))
            self.cur.execute(f'SELECT id FROM bookmarks WHERE url IN ({placeholder})', list(urls))
            return [x[0] for x in self.cur.fetchall()]
        with self.lock:
            return self.get_rec_ids(urls, lock=False)

    def get_max_id(self, *, lock: bool = True) -> int:
        """Fetch the ID of the last record.

        Parameters
        ----------
        lock : bool
            Whether to restrict concurrent access (True by default).

        Returns
        -------
        int
            ID of the record if any record exists, else None.
        """

        if not lock:
            self.cur.execute('SELECT MAX(id) FROM bookmarks')
            return self.cur.fetchall()[0][0]
        with self.lock:
            return self.get_max_id(lock=False)

    def add_rec(
            self,
            url: str,
            title_in: Optional[str] = None,
            tags_in: Optional[str] = None,
            desc: Optional[str] = None,
            immutable: bool = False,
            delay_commit: bool = False,
            fetch: bool = True,
            url_redirect: bool = False,
            tag_redirect: bool | str = False,
            tag_error: bool | str = False,
            del_error: Optional[Set[int] | range] = None,
            tags_fetch: bool = True,
            tags_except: Optional[str] = None) -> int:  # Optional[IntSet]
        """Add a new bookmark.

        Parameters
        ----------
        url : str
            URL to bookmark.
        title_in : str, optional
            Title to add manually. Default is None.
        tags_in : str, optional
            Comma-separated tags to add manually, instead of fetching them. Default is None.
        tags_except : str, optional
            These are removed from the resulting tags list. Default is None.
        tags_fetch : bool
            True if tags parsed from the fetched page should be included. Default is True.
        desc : str, optional
            Description of the bookmark. Default is None.
        immutable : bool
            Indicates whether to disable title fetch from web. Default is False.
        delay_commit : bool
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.
        fetch : bool
            Fetch page from web and parse for data. Required fetch-status params to take effect.
        url_redirect : bool
            Bookmark the URL produced after following all PERMANENT redirects.
        tag_redirect : bool | str
            Adds a tag by the given pattern if the url resolved to a PERMANENT
            redirect. (True means the default pattern 'http:{}'.)
        tag_error : bool | str
            Adds a tag by the given pattern if the url resolved to a HTTP error.
            (True means the default pattern 'http:{}'.)
        del_error : int{} | range, optional
            Do not add the bookmark if HTTP response status is in the given set or range.
            Also prevents the bookmark from being added on a network error.

        Returns
        -------
        int
            DB index of new bookmark on success, None on failure.
        """

        # Return error for empty URL
        if not url:
            LOGERR('Invalid URL')
            return None

        # Ensure that the URL does not exist in DB already
        id = self.get_rec_id(url)
        if id:
            LOGERR('URL [%s] already exists at index %d', url, id)
            return None

        if fetch:
            # Fetch data
            result = fetch_data(url)
            if result.bad:
                print('Malformed URL\n')
            elif result.mime:
                LOGDBG('HTTP HEAD requested')
            elif not result.title and title_in is None:
                print('No title\n')
            else:
                LOGDBG('Title: [%s]', result.title)
        else:
            result = FetchResult(url, fetch_status=200)
            LOGDBG('ptags: [%s]', result.tags(redirect=tag_redirect, error=tag_error))

        url = (result.url if url_redirect else url)
        title = (title_in if title_in is not None else result.title)

        # Fix up tags, if broken
        tags_exclude = set(taglist((tags_except or '').split(DELIM)))
        tags_fetched = result.tags(keywords=tags_fetch, redirect=tag_redirect, error=tag_error)
        tags = taglist_str((tags_in or '') + DELIM + tags_fetched,
                           lambda ss: [s for s in ss if s not in tags_exclude])
        LOGDBG('tags: [%s]', tags)

        # Process description
        desc = (desc if desc is not None else result.desc) or ''

        try:
            assert not del_error or result.fetch_status is not None, 'Network error'
            assert not del_error or result.fetch_status not in del_error, f'HTTP error {result.fetch_status}'
            flagset = FLAG_NONE
            if immutable:
                flagset |= FLAG_IMMUTABLE

            qry = 'INSERT INTO bookmarks(URL, metadata, tags, desc, flags) VALUES (?, ?, ?, ?, ?)'
            with self.lock:
                self.cur.execute(qry, (url, title, tags, desc, flagset))
                if not delay_commit:
                    self.conn.commit()
                if self.chatty:
                    self.print_rec(self.cur.lastrowid)
                return self.cur.lastrowid
        except Exception as e:
            LOGERR('add_rec(): %s', e)
            return None

    def append_tag_at_index(self, index, tags_in, delay_commit=False):
        """Append tags to bookmark tagset at index.

        Parameters
        ----------
        index : int | int[] | int{} | range, optional
            DB index of the record. 0 or empty indicates all records.
        tags_in : str
            Comma-separated tags to add manually.
        delay_commit : bool
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        if tags_in is None or tags_in == DELIM:
            return True
        indices = (None if not index else [index] if isinstance(index, int) else index)

        with self.lock:
            if not indices:
                resp = read_in('Append the tags to ALL bookmarks? (y/n): ')
                if resp != 'y':
                    return False

                self.cur.execute('SELECT id, tags FROM bookmarks ORDER BY id ASC')
            else:
                placeholder = ', '.join(['?'] * len(indices))
                self.cur.execute(f'SELECT id, tags FROM bookmarks WHERE id IN ({placeholder}) ORDER BY id ASC', tuple(indices))

            resultset = self.cur.fetchall()
            if resultset:
                query = 'UPDATE bookmarks SET tags = ? WHERE id = ?'
                for row in resultset:
                    tags = row[1] + tags_in[1:]
                    tags = parse_tags([tags])
                    self.cur.execute(query, (tags, row[0],))
                    if self.chatty and not delay_commit:
                        self.print_rec(row[0])
            else:
                return False

            if not delay_commit:
                self.conn.commit()

        return True

    def delete_tag_at_index(self, index, tags_in, delay_commit=False, chatty=True):
        """Delete tags from bookmark tagset at index.

        Parameters
        ----------
        index : int | int[] | int{} | range, optional
            DB index of bookmark record. 0 or empty indicates all records.
        tags_in : str
            Comma-separated tags to delete manually.
        delay_commit : bool
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.
        chatty: bool
            Skip confirmation when set to False.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        if tags_in is None or tags_in == DELIM:
            return True

        tags_to_delete = tags_in.strip(DELIM).split(DELIM)
        indices = (None if not index else [index] if isinstance(index, int) else index)

        if len(indices or []) != 1:
            if not indices and chatty:
                resp = read_in('Delete the tag(s) from ALL bookmarks? (y/n): ')
                if resp != 'y':
                    return False

            query = "UPDATE bookmarks SET tags = replace(tags, ?, ?) WHERE tags LIKE ? ESCAPE '`'"
            if indices:
                query += ' AND id IN ({})'.format(', '.join(['?'] * len(indices)))

            count = 0
            with self.lock:
                for tag in tags_to_delete:
                    tag = delim_wrap(tag)
                    args = (tag, DELIM, '%'+like_escape(tag, '`')+'%') + tuple(indices or [])
                    self.cur.execute(query, args)
                    count += self.cur.rowcount

                if count > 0 and not delay_commit:
                    self.conn.commit()
                    if self.chatty:
                        print('%d record(s) updated' % count)

            return True

        # Process a single index
        # Use SELECT and UPDATE to handle multiple tags at once
        with self.lock:
            query = 'SELECT id, tags FROM bookmarks WHERE id = ? LIMIT 1'
            self.cur.execute(query, list(indices))
            resultset = self.cur.fetchall()
            if not resultset:
                return False

            query = 'UPDATE bookmarks SET tags = ? WHERE id = ?'
            for row in resultset:
                tags = row[1]

                for tag in tags_to_delete:
                    tags = tags.replace(delim_wrap(tag), DELIM)

                self.cur.execute(query, (parse_tags([tags]), row[0],))
                if self.chatty and not delay_commit:
                    self.print_rec(row[0])

                if not delay_commit:
                    self.conn.commit()

        return True

    def update_rec(
            self,
            index: Optional[int | Sequence[int] | Set[int] | range],  # Optional[IntOrInts]
            url: Optional[str] = None,
            title_in: Optional[str] = None,
            tags_in: Optional[str] = None,
            desc: Optional[str] = None,
            immutable: Optional[bool] = None,
            threads: int = 4,
            url_redirect: bool = False,
            tag_redirect: bool | str = False,
            tag_error: bool | str = False,
            del_error: Optional[Set[int] | range] = None,             # Optional[IntSet]
            export_on: Optional[Set[int] | range] = None,             # Optional[IntSet]
            retain_order: bool = False) -> bool:
        """Update an existing record at (each) index.

        Update all records if index is 0 or empty, and url is not specified.
        URL is an exception because URLs are unique in DB.

        Parameters
        ----------
        index : int | int[] | int{} | range, optional
            DB index(es) of record(s). 0 or empty value indicates all records.
        url : str, optional
            Bookmark address.
        title_in : str, optional
            Title to add manually.
        tags_in : str, optional
            Comma-separated tags to add manually. Must start and end with comma.
            Prefix with '+,' to append to current tags.
            Prefix with '-,' to delete from current tags.
        desc : str, optional
            Description of bookmark.
        immutable : bool, optional
            Disable title fetch from web if True. Default is None (no change).
        threads : int
            Number of threads to use to refresh full DB. Default is 4.
        url_redirect : bool
            Update the URL to one produced after following all PERMANENT redirects.
            (This could fail if the new URL is bookmarked already.)
        tag_redirect : bool | str
            Adds a tag by the given pattern if the url resolved to a PERMANENT
            redirect. (True means the default pattern 'http:{}'.)
        tag_error : bool | str
            Adds a tag by the given pattern if the url resolved to a HTTP error.
            (True means the default pattern 'http:{}'.)
        del_error : int{} | range, optional
            Delete the bookmark if HTTP response status is in the given set or range.
            Does NOT cause deletion of the bookmark on a network error.
        export_on : int{} | range, optional
            Limit the export to URLs returning one of given HTTP codes; store old URLs.
        retain_order : bool
            If True, bookmark deletion will not result in their order being changed
            (multiple indices will be updated instead).

        Returns
        -------
        bool
            True on success, False on failure. (Deletion by del_error counts as success.)
        """

        arguments = []  # type: List[Any]
        query = 'UPDATE bookmarks SET'
        tag_modified = False
        ret = True
        indices = (None if not index else [index] if isinstance(index, int) else index)
        index = indices and list(indices or [])[0]
        single = len(indices or []) == 1
        export_on, self._to_export = (export_on or set()), ({} if export_on else None)
        tags_in = (tags_in or None if not tags_in or re.match('[+-],', tags_in) else delim_wrap(tags_in))

        if url and not single:
            LOGERR('All URLs cannot be same')
            return False

        if tags_in in ('+,', '-,'):
            LOGERR('Please specify a tag')
            return False

        if indices and min(indices) > (self.get_max_id() or 0):  # none of the indices exist in DB?
            return False

        # Update description if passed as an argument
        if desc is not None:
            query += ' desc = ?,'
            arguments += (desc,)

        # Update immutable flag if passed as argument
        if immutable is not None:
            if immutable:
                query += ' flags = flags | ?,'
                arguments += (FLAG_IMMUTABLE,)
            else:
                query += ' flags = flags & ?,'
                arguments += (~FLAG_IMMUTABLE,)

        # Update title
        #
        # 1. If --title has no arguments, delete existing title
        # 2. If --title has arguments, update existing title
        # 3. If --title option is omitted at cmdline:
        #    If URL is passed, update the title from web using the URL
        # 4. If no other argument (url, tag, comment, immutable) passed,
        #    update title from web using DB URL (if title is mutable)
        fetch_title = {url, title_in, tags_in, desc, immutable} == {None}
        network_test = url_redirect or tag_redirect or tag_error or del_error or export_on or fetch_title
        if url and title_in is None:
            network_test = False
            _url = url or self.get_rec_by_id(index).url
            result = fetch_data(_url)
            if result.bad:
                print('Malformed URL')
            elif result.mime:
                LOGDBG('HTTP HEAD requested')
            elif not result.title:
                print('No title')
            else:
                LOGDBG('Title: [%s]', result.title)

            if result.desc and not desc:
                query += ' desc = ?,'
                arguments += (result.desc,)

            if url_redirect and result.url != _url:
                url = result.url

            if result.fetch_status in export_on:  # storing the old URL
                self._to_export[url or _url] = _url
        else:
            result = FetchResult(url, title_in)

        if result.title is not None:
            query += ' metadata = ?,'
            arguments += (result.title,)

        # Update URL if passed as argument
        if url:
            query += ' URL = ?,'
            arguments += (url,)

        if result.fetch_status in (del_error or []):
            if result.fetch_status in export_on:  # storing the old record
                self._to_export[url] = self.get_rec_by_id(index)
            LOGERR('HTTP error %s', result.fetch_status)
            return self.delete_rec(index, retain_order=retain_order)

        if not indices and (arguments or tags_in):
            resp = read_in('Update ALL bookmarks? (y/n): ')
            if resp != 'y':
                return False

        if network_test:  # doing this before updates to backup records to-be-deleted in their original state
            custom_tags = (tags_in if (tags_in or '').startswith(DELIM) else None)
            ret = ret and self.refreshdb(indices, threads, url_redirect=url_redirect, tag_redirect=tag_redirect,
                                         tag_error=tag_error, del_error=del_error, export_on=export_on,
                                         update_title=fetch_title, custom_url=url, custom_tags=custom_tags, delay_delete=True)

        # Update tags if passed as argument
        _tags = result.tags(keywords=False, redirect=tag_redirect, error=tag_error)
        if tags_in or _tags:
            if not tags_in or tags_in.startswith('+,'):
                tags = taglist_str((tags_in or '')[1:] + _tags)
                chatty = self.chatty
                self.chatty = False
                ret = self.append_tag_at_index(indices, tags)
                self.chatty = chatty
                tag_modified = True
            elif tags_in.startswith('-,'):
                chatty = self.chatty
                self.chatty = False
                ret = self.delete_tag_at_index(indices, tags_in[1:])
                if _tags:
                    self.append_tag_at_index(indices, _tags)
                self.chatty = chatty
                tag_modified = True
            elif not network_test:  # rely on custom_tags to avoid overwriting fetch-status tags
                query += ' tags = ?,'
                arguments += (taglist_str(tags_in + _tags),)

        if not arguments:  # no arguments => nothing to update
            if (tag_modified or network_test) and self.chatty:
                self.print_rec(indices)
            self.commit_delete(retain_order=retain_order)
            return ret

        query = query[:-1]
        if indices:  # Only specified indices
            query += ' WHERE id IN ({})'.format(', '.join(['?'] * len(indices)))
            arguments += tuple(indices)

        LOGDBG('update_rec query: "%s", args: %s', query, arguments)

        with self.lock:
            try:
                self.cur.execute(query, arguments)
                self.conn.commit()
                if self.cur.rowcount > 0 and self.chatty:
                    self.print_rec(index)
                elif self.cur.rowcount == 0:
                    if single:
                        LOGERR('No matching index %d', index)
                    else:
                        LOGERR('No matches found')
                    return False
            except sqlite3.IntegrityError:
                LOGERR('URL already exists')
                return False
            except sqlite3.OperationalError as e:
                LOGERR(e)
                return False
            finally:
                self.commit_delete(retain_order=retain_order)

        return True

    def refreshdb(
            self,
            index: Optional[int | Sequence[int] | Set[int] | range],  # Optional[IntOrInts]
            threads: int,
            url_redirect: bool = False,
            tag_redirect: bool | str = False,
            tag_error: bool | str = False,
            del_error: Optional[Set[int] | range] = None,             # Optional[IntSet]
            export_on: Optional[Set[int] | range] = None,             # Optional[IntSet]
            update_title: bool = True,
            custom_url: Optional[str] = None,
            custom_tags: Optional[str] = None,
            delay_delete: bool = False,
            retain_order: bool = False) -> bool:
        """Refresh ALL (or specified) records in the database.

        Fetch title for each bookmark from the web and update the records.
        Doesn't update the title if fetched title is empty.

        Notes
        -----
            This API doesn't change DB index, URL or tags of a bookmark.
            (Unless one or more fetch-status parameters are supplied.)
            This API is verbose.

        Parameters
        ----------
        index : int | int[] | int{} | range, optional
            DB index(es) of record(s) to update. 0 or empty value indicates all records.
        threads: int
            Number of threads to use to refresh full DB. Default is 4.
        url_redirect : bool
            Update the URL to one produced after following all PERMANENT redirects.
            (This could fail if the new URL is bookmarked already.)
        tag_redirect : bool | str
            Adds a tag by the given pattern if the url resolved to a PERMANENT
            redirect. (True means the default pattern 'http:{}'.)
        tag_error : bool | str
            Adds a tag by the given pattern if the url resolved to a HTTP error.
            (True means the default pattern 'http:{}'.)
        del_error : int{} | range, optional
            Delete the bookmark if HTTP response status is in the given set or range.
        export_on : int{} | range, optional
            Limit the export to URLs returning one of given HTTP codes; store old URLs.
        update_title : bool
            Update titles/descriptions. (Can be turned off for network testing.)
        custom_url : str, optional
            Override URL to fetch. (Use for network testing of a single record before updating it.)
        custom_tags : str, optional
            Overwrite all tags. (Use to combine network testing with tags overwriting.)
        delay_delete : bool
            Delay scheduled deletions by del_error. (Use for network testing during update.)
        retain_order : bool
            If True, bookmark deletion will not result in their order being changed
            (multiple indices will be updated instead).

        Returns
        -------
        bool
            True on success, False on failure. (Deletion by del_error counts as success.)
        """

        indices = (None if not index else [index] if isinstance(index, int) else index)
        index = indices and list(indices)[0]
        export_on, self._to_export = (export_on or set()), ({} if export_on else None)
        self._to_delete = []

        if not update_title and not (url_redirect or tag_redirect or tag_error or del_error or export_on):
            LOGERR('Noop update request')
            return False
        if custom_url and len(indices or []) != 1:
            LOGERR('custom_url is only supported for a singular index')
            return False

        with self.lock:
            if not indices:
                self.cur.execute('SELECT id, url, tags, flags FROM bookmarks ORDER BY id ASC')
            else:
                placeholder = ', '.join(['?'] * len(indices))
                self.cur.execute(f'SELECT id, url, tags, flags FROM bookmarks WHERE id IN ({placeholder}) ORDER BY id ASC',
                                 tuple(indices))

            resultset = self.cur.fetchall()
            recs = len(resultset)
            if not recs:
                LOGERR('No matching index or title immutable or empty DB')
                return False

        # Set up strings to be printed
        if self.colorize:
            bad_url_str = '\x1b[1mIndex %d: Malformed URL\x1b[0m\n'
            mime_str = '\x1b[1mIndex %d: HTTP HEAD requested\x1b[0m\n'
            blank_url_str = '\x1b[1mIndex %d: No title\x1b[0m\n'
            success_str = 'Title: [%s]\n\x1b[92mIndex %d: updated\x1b[0m\n'
        else:
            bad_url_str = 'Index %d: Malformed URL\n'
            mime_str = 'Index %d: HTTP HEAD requested\n'
            blank_url_str = 'Index %d: No title\n'
            success_str = 'Title: [%s]\nIndex %d: updated\n'

        done = {'value': 0}  # count threads completed
        processed = {'value': 0}  # count number of records processed

        # An additional call to generate default headers
        # gen_headers() is called within fetch_data()
        # However, this initial call to setup headers
        # ensures there is no race condition among the
        # initial threads to setup headers
        if not MYHEADERS:
            gen_headers()

        def refresh(thread_idx, cond):
            """Inner function to fetch titles and update records.

            Parameters
            ----------
            thread_idx : int
                Thread index/ID.
            cond : threading condition object.
            """

            _count = 0

            while True:
                query = 'UPDATE bookmarks SET'
                arguments = []

                with cond:
                    if resultset:
                        id, url, tags, flags = resultset.pop()
                    else:
                        break

                result = fetch_data(custom_url or url, http_head=(flags & FLAG_IMMUTABLE) > 0)
                _count += 1

                with cond:
                    if result.bad:
                        print(bad_url_str % id)
                        if custom_tags:
                            self.cur.execute('UPDATE bookmarks SET tags = ? WHERE id = ?', (custom_tags, id))
                        continue

                    if result.fetch_status in (del_error or []):
                        if result.fetch_status in export_on:
                            self._to_export[url] = self.get_rec_by_id(id, lock=False)
                        LOGERR('HTTP error %s', result.fetch_status)
                        self._to_delete += [id]
                        if result.mime and self.chatty:
                            print(mime_str % id)
                        if custom_tags:
                            self.cur.execute('UPDATE bookmarks SET tags = ? WHERE id = ?', (custom_tags, id))
                        continue

                    if result.mime:
                        if self.chatty:
                            print(mime_str % id)
                        if custom_tags:
                            self.cur.execute('UPDATE bookmarks SET tags = ? WHERE id = ?', (custom_tags, id))
                        continue

                    if not result.title:
                        LOGERR(blank_url_str, id)
                    elif update_title:
                        query += ' metadata = ?,'
                        arguments += (result.title,)

                    if update_title and result.desc:
                        query += ' desc = ?,'
                        arguments += (result.desc,)

                    _url = url
                    if url_redirect and result.url != url:
                        query += ' url = ?,'
                        arguments += (result.url,)
                        _url = result.url

                    if result.fetch_status in export_on:
                        self._to_export[_url] = url

                    _tags = result.tags(keywords=False, redirect=tag_redirect, error=tag_error)
                    if _tags:
                        query += ' tags = ?,'
                        arguments += (taglist_str((custom_tags or tags) + DELIM + _tags),)
                    elif custom_tags:
                        query += ' tags = ?,'
                        arguments += (taglist_str(custom_tags),)

                    if not arguments:  # nothing to update
                        continue

                    query = query[:-1] + ' WHERE id = ?'
                    arguments += (id,)
                    LOGDBG('refreshdb query: "%s", args: %s', query, arguments)

                    self.cur.execute(query, arguments)

                    # Save after fetching 32 titles per thread
                    if _count % 32 == 0:
                        self.conn.commit()

                    if self.chatty:
                        print(success_str % (result.title, id))

                if INTERRUPTED:
                    break

            LOGDBG('Thread %d: processed %d', threading.get_ident(), _count)
            with cond:
                done['value'] += 1
                processed['value'] += _count
                cond.notify()

        with self.lock:  # preventing external concurrent access
            cond = threading.Condition()
            with cond:  # preventing concurrent access between workers
                threads = min(threads, recs)

                for i in range(threads):
                    thread = threading.Thread(target=refresh, args=(i, cond))
                    thread.start()

                while done['value'] < threads:
                    cond.wait()
                    LOGDBG('%d threads completed', done['value'])

                # Guard: records found == total records processed
                if recs != processed['value']:
                    LOGERR('Records: %d, processed: %d !!!', recs, processed['value'])

            if delay_delete:
                self.conn.commit()
            else:
                self.commit_delete(retain_order=retain_order)

        return True

    def commit_delete(self, apply: bool = True, retain_order: bool = False):
        """Commit delayed delete commands."""
        if apply and self._to_delete is not None:
            with self.lock:
                for id in sorted(set(self._to_delete), reverse=True):
                    self.delete_rec(id, delay_commit=True, chatty=False, retain_order=retain_order)
                self.conn.commit()
                self.cur.execute('VACUUM')
        self._to_delete = None

    def edit_update_rec(self, index, immutable=None):
        """Edit in editor and update a record.

        Parameters
        ----------
        index : int
            DB index of the record.
            Last record, if index is -1.
        immutable : bool, optional
            Disable title fetch from web if True. Default is None (no change).

        Returns
        -------
        bool
            True if updated, else False.
        """

        editor = get_system_editor()
        if editor == 'none':
            LOGERR('EDITOR must be set to use index with -w')
            return False

        if index == -1:
            # Edit the last records
            index = self.get_max_id()
            if not index:
                LOGERR('Empty database')
                return False

        rec = self.get_rec_by_id(index)
        if not rec:
            LOGERR('No matching index %d', index)
            return False

        # If reading from DB, show empty title and desc as empty lines. We have to convert because
        # even in case of add with a blank title or desc, '' is used as initializer to show '-'.
        result = edit_rec(editor, rec.url, rec.title or None, rec.tags_raw, rec.desc or None)
        if result is not None:
            url, title, tags, desc = result
            return self.update_rec(index, url, title, tags, desc, immutable)

        if immutable is not None:
            return self.update_rec(index, immutable=immutable)

        return False

    def list_using_id(self, ids=[], order=['+id']):
        """List entries in the DB using the specified id list.

        Parameters
        ----------
        ids : list of ids/ranges in string form
        order : list of strings
          Order description (fields from JSON export or DB, prepended with '+'/'-' for ASC/DESC).

        Returns
        -------
        list
        """
        q0 = 'SELECT * FROM bookmarks'
        if ids:
            q0 += ' WHERE id in ('
            for idx in ids:
                if '-' not in idx:
                    q0 += idx + ','
                else:
                    val = idx.split('-')
                    if val[0]:
                        _range = list(map(int, val))
                        _range[1] += 1
                        part_ids = range(*_range)
                    else:
                        end = int(val[1])
                        qtemp = 'SELECT id FROM bookmarks ORDER BY id DESC LIMIT {0}'.format(end)
                        with self.lock:
                            self.cur.execute(qtemp, [])
                            part_ids = chain.from_iterable(self.cur.fetchall())
                    q0 += ','.join(map(str, part_ids))
            q0 = q0.strip(',')
            q0 += ')'

        try:
            return self._fetch(q0 + f' ORDER BY {self._order(order)}')
        except sqlite3.OperationalError as e:
            LOGERR(e)
            return []

    def _search_tokens(self, keyword: str, deep=False, regex=False, markers=False):
        """Converts a keyword into a list of tokens, based on search parameters.
        A token is a varied-length tuple of following values: (SQL field, deep, *SQL params)."""
        deep = not regex and deep
        if not markers or (re.sub(r'^\*', '', keyword) and not re.match(r'^[.:>#]', keyword)):
            s = (keyword if not markers else re.sub(r'^\*', '', keyword))
            if not s:
                return []
            tags = ([s] if regex and not markers else taglist(s.split(DELIM)))
            return [('metadata', deep, s), ('url', deep, s), ('desc', deep, s)] + (tags and [('tags', deep, *tags)])
        if re.match(r'^\..', keyword):  # checking prefix + ensuring keyword[1:] is not empty
            return [('metadata', deep, keyword[1:])]
        if re.match(r'^:.', keyword):
            return [('url', deep, keyword[1:])]
        if re.match(r'^>.', keyword):
            return [('desc', deep, keyword[1:])]
        if re.match(r'^#,?[^,]', keyword):
            tags = ([re.sub(r'^#,?', '', keyword)] if regex else taglist(keyword[1:].split(DELIM)))
            return tags and [('tags', not keyword.startswith('#,'), *tags)]
        return []

    def _search_clause(self, tokens, regex=False) -> Tuple[str, List[str]]:
        """Converts a list of tokens into an SQL clause. (See also: BukuDb._search_tokens().)
        If regex is True, the token is treated as a raw regex and the paired deep parameter is ignored."""
        border = lambda k, c: (',' if k == 'tags' else r'\b' if c.isalnum() else '')

        args, clauses = [], []
        if regex:
            for field, deep, param in tokens:
                clauses += [field + ' REGEXP ?']
                args += [param]
        else:
            for field, deep, *params in tokens:
                _clauses = []
                for param in params:
                    if deep:
                        _clauses += [field + " LIKE ('%' || ? || '%')"]
                    else:
                        _clauses += [field + ' REGEXP ?']
                        param = border(field, param[0]) + re.escape(param) + border(field, param[-1])
                    args += [param]
                clauses += (_clauses if len(_clauses) < 2 else [f'({" AND ".join(_clauses)})'])
        return ' OR '.join(clauses), args

    def searchdb(
            self,
            keywords: List[str],
            all_keywords: bool = False,
            deep: bool = False,
            regex: bool = False,
            markers: bool = False,
            order: List[str] = ['+id'],
    ) -> List[BookmarkVar]:
        """Search DB for entries where tags, URL, or title fields match keywords.

        Parameters
        ----------
        keywords : list of str
            Keywords to search.
        order : list of str
            Order description (fields from JSON export or DB, prepended with '+'/'-' for ASC/DESC).
            Note: this applies to fields with the same number of matched keywords.
        all_keywords : bool
            False (default value) to return records matching ANY keyword.
            True to return records matching ALL keywords. This also enables special
            behaviour when keywords in (['blank'], ['immutable']).
        deep : bool
            True to search for matching substrings. Default is False.
        markers : bool
            True to use prefix markers for different fields. Default is False.
        regex : bool
            Match a regular expression if True. Default is False.
            Overrides deep, all_keywords, and comma matching in tags with markers.

        Returns
        -------
        list
            List of search results.
        """
        _order = self._order(order)
        clauses, qargs = [], []
        for keyword in keywords:
            tokens = self._search_tokens(keyword, deep=deep, markers=markers)
            clause, args = self._search_clause(tokens, regex=regex)
            if clause and args:
                clauses += [f'({clause})']
                qargs += args
        if not qargs:
            return []

        _count = lambda x: f'CASE WHEN {x} THEN 1 ELSE 0 END'
        if regex:
            query = ('SELECT id, url, metadata, tags, desc, flags\nFROM (SELECT *, (' +
                     '\n    + '.join(map(_count, clauses)) +
                     f') AS score\n  FROM bookmarks WHERE score > 0 ORDER BY score DESC, {_order})')
        elif all_keywords:
            if keywords == ['blank']:
                qargs, query = [DELIM], "SELECT * FROM bookmarks WHERE metadata = '' OR tags = ?"
            elif keywords == ['immutable']:
                qargs, query = [], 'SELECT * FROM bookmarks WHERE flags & 1 == 1'
            else:
                query = 'SELECT id, url, metadata, tags, desc, flags FROM bookmarks WHERE ' + '\n  AND '.join(clauses)
            query += f'\nORDER BY {_order}'
        elif not all_keywords:
            query = ('SELECT id, url, metadata, tags, desc, flags\nFROM (SELECT *, (' +
                     '\n    + '.join(map(_count, clauses)) +
                     f') AS score\n  FROM bookmarks WHERE score > 0 ORDER BY score DESC, {_order})')
        else:
            LOGERR('Invalid search option')
            return []

        LOGDBG('query: "%s", args: %s', query, qargs)

        try:
            return self._fetch(query, *qargs)
        except sqlite3.OperationalError as e:
            LOGERR(e)
            return []

    def search_by_tag(self, tags: Optional[str], order: List[str] = ['+id']) -> List[BookmarkVar]:
        """Search bookmarks for entries with given tags.

        Parameters
        ----------
        tags : str
            String of tags to search for.
            Retrieves entries matching ANY tag if tags are
            delimited with ','.
            Retrieves entries matching ALL tags if tags are
            delimited with '+'.
        order : list of str
            Order description (fields from JSON export or DB, prepended with '+'/'-' for ASC/DESC).
            Note: this applies to fields with the same number of matched tags.

        Returns
        -------
        list
            List of search results.
        """

        _order = self._order(order)
        LOGDBG(tags)
        if tags is None or tags == DELIM or tags == '':
            return []

        qargs, search_operator, excluded_tags = prep_tag_search(tags)
        if search_operator is None:
            LOGERR("Cannot use both '+' and ',' in same search")
            return []

        LOGDBG('tags: %s', qargs)
        LOGDBG('search_operator: %s', search_operator)
        LOGDBG('excluded_tags: %s', excluded_tags)

        if search_operator == 'AND':
            query = ('SELECT id, url, metadata, tags, desc, flags FROM bookmarks WHERE (' +
                     f' {search_operator} '.join("tags LIKE '%' || ? || '%'" for tag in qargs) +
                     ')' + ('' if not excluded_tags else ' AND tags NOT REGEXP ?') +
                     f' ORDER BY {_order}')
        else:
            query = ('SELECT id, url, metadata, tags, desc, flags FROM (SELECT *, ' +
                     ' + '.join("CASE WHEN tags LIKE '%' || ? || '%' THEN 1 ELSE 0 END" for tag in qargs) +
                     ' AS score FROM bookmarks WHERE score > 0' +
                     ('' if not excluded_tags else ' AND tags NOT REGEXP ?') +
                     f' ORDER BY score DESC, {_order})')
        if excluded_tags:
            qargs += [excluded_tags]

        LOGDBG('query: "%s", args: %s', query, qargs)
        return self._fetch(query, *qargs)

    def search_keywords_and_filter_by_tags(
            self,
            keywords: List[str],
            all_keywords: bool = False,
            deep: bool = False,
            regex: bool = False,
            stag: Optional[List[str]] = None,
            without: Optional[List[str]] = None,
            markers: bool = False,
            order: List[str] = ['+id']) -> List[BookmarkVar]:
        """Search bookmarks for entries with keywords and specified
        criteria while filtering out entries with matching tags.

        Parameters
        ----------
        keywords : list of str
            Keywords to search.
        without : list of str
            Keywords to exclude; ignored if empty. Default is None.
        all_keywords : bool
            True to return records matching ALL keywords.
            False to return records matching ANY keyword. (This is the default.)
        deep : bool
            True to search for matching substrings. Default is False
        markers: bool
            True to use prefix markers for different fields. Default is False.
        regex : bool
            Match a regular expression if True. Default is False.
        stag : list of str
            Strings of tags to search for. Default is None.
            Retrieves entries matching ANY tag if tags are
            delimited with ','.
            Retrieves entries matching ALL tags if tags are
            delimited with '+'.

        Returns
        -------
        list
            List of search results.
        """

        results = self.searchdb(keywords, all_keywords=all_keywords, deep=deep, regex=regex, markers=markers, order=order)
        results = (results if not stag else filter_from(results, self.search_by_tag(''.join(stag))))
        return self.exclude_results_from_search(results, without, deep=deep, markers=markers)

    def exclude_results_from_search(self, search_results, without, deep=False, markers=False):
        """Excludes records that match keyword search using without parameters

        Parameters
        ----------
        search_results : list
            List of search results.
        without : list of str
            Keywords to exclude. If empty, returning search_results unchanged.
        deep : bool
            True to search for matching substrings. Default is False.
        markers: bool
            True to use prefix markers for different fields. Default is False.

        Returns
        -------
        list
            List of search results.
        """

        if not without:
            return search_results
        return filter_from(search_results, self.searchdb(without, deep=deep, markers=markers), exclude=True)

    def swap_recs(self, index1: int, index2: int, *, lock: bool = True, delay_commit: bool = False):
        """Swaps two records with given indices

        Parameters
        ----------
        index1 : int
            Index of the 1st record to be exchanged.
        index2 : int
            Index of the 2nd record to be exchanged.
        lock : bool
            Whether to restrict concurrent access (True by default).
        delay_commit : bool
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.

        Returns
        -------
        bool
            True on success, False on failure.
        """
        if lock:
            with self.lock:
                return self.swap_recs(index1, index2, lock=False, delay_commit=delay_commit)

        max_id = self.get_max_id()
        if not max_id or index1 == index2 or not all(0 < x <= max_id for x in [index1, index2]):
            return False

        self.cur.executemany('UPDATE bookmarks SET id = ? WHERE id = ?',
                             [(max_id+1, index1), (index1, index2), (index2, max_id+1)])
        if not delay_commit:
            self.conn.commit()
        return True

    def compactdb(self, index: int, delay_commit: bool = False, upto: Optional[int] = None, retain_order: bool = False):
        """When an entry at index is deleted, move the
        last entry in DB to index, if index is lesser.

        Parameters
        ----------
        index : int
            DB index of deleted entry.
        delay_commit : bool
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.
        upto : int, optional
            If specified, multiple indices are moved at once.
        retain_order: bool
            Shift indices of multiple records by 1 instead of replacing
            the deleted record with the last one. Default is False.
        """

        # Return if the last index left in DB was just deleted
        max_id = self.get_max_id()
        if not max_id or (upto and upto < index):
            return

        # NOOP if the just deleted index was the last one
        if max_id > index:
            with self.lock:
                if retain_order or (upto or 0) > index:
                    step = (max(max_id - upto, upto + 1 - index) if not retain_order else
                            1 if not upto else upto + 1 - index)
                    self.cur.execute('UPDATE bookmarks SET id = id-? WHERE id >= ?', (step, index+step))
                    msg = f'Indices {index+step}-{max_id} moved to {index}-{max_id-step}'
                else:
                    self.cur.execute('UPDATE bookmarks SET id = ? WHERE id = ?', (index, max_id))
                    msg = f'Index {max_id} moved to {index}'
                if not delay_commit:
                    self.conn.commit()
                    self.cur.execute('VACUUM')
            if self.chatty:
                print(msg)

    def delete_rec(
            self,
            index: int = None,
            low: int = 0,
            high: int = 0,
            is_range: bool = False,
            delay_commit: bool = False,
            chatty: Optional[bool] = None,
            retain_order: bool = False,
    ) -> bool:
        """Delete a single record or remove the table if index is 0.

        Parameters
        ----------
        index : int, optional
            DB index of deleted entry.
        low : int
            Actual lower index of range.
        high : int
            Actual higher index of range.
        is_range : bool
            A range is passed using low and high arguments.
            An index is ignored if is_range is True.
        delay_commit : bool
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.
        chatty : Optional[bool]
            Override for self.chatty
        retain_order: bool
            Shift indices of multiple records instead of replacing
            the deleted record with the last one. Default is False.

        Raises
        ------
        TypeError
            If any of index, low, or high variable is not integer.

        Returns
        -------
        bool
            True on success, False on failure.

        Examples
        --------
        >>> from tempfile import NamedTemporaryFile
        >>> import buku
        >>> sdb = buku.BukuDb(dbfile=NamedTemporaryFile().name)  # single record database
        >>> sdb.add_rec('https://example.com')
        1
        >>> sdb.delete_rec(1)
        Index 1 deleted
        True

        Delete record with default range.

        >>> sdb = buku.BukuDb(dbfile=NamedTemporaryFile().name)
        >>> sdb.add_rec('https://example.com')
        1
        >>> sdb.delete_rec(is_range=True)  # doctest: +SKIP
        Remove ALL bookmarks? (y/n): y
        All bookmarks deleted
        True

        Running the function without any parameter will raise TypeError.

        >>> sdb = buku.BukuDb(dbfile=NamedTemporaryFile().name)
        >>> sdb.add_rec('https://example.com')
        1
        >>> sdb.delete_rec()
        Traceback (most recent call last):
        ...
        TypeError: index, low, or high variable is not integer

        Negative number on `high` and `low` parameters when is_range is True
        will log error and return False

        >>> edb = buku.BukuDb(dbfile=NamedTemporaryFile().name)
        >>> edb.delete_rec(low=-1, high=-1, is_range=True)
        False

        Remove the table

        >>> sdb = buku.BukuDb(dbfile=NamedTemporaryFile().name)
        >>> sdb.delete_rec(0)  # doctest: +SKIP
        Remove ALL bookmarks? (y/n): y
        All bookmarks deleted
        True
        """
        chatty = (chatty if chatty is not None else self.chatty)
        params = [low, high]
        if not is_range:
            params.append(index)
        if any(map(lambda x: not isinstance(x, int), params)):
            raise TypeError('index, low, or high variable is not integer')

        if is_range:  # Delete a range of indices
            if low < 0 or high < 0:
                LOGERR('Negative range boundary')
                return False

            if low > high:
                low, high = high, low

            # If range starts from 0, delete all records
            if low == 0:
                return self.cleardb()

            try:
                if chatty:
                    with self.lock:
                        self.cur.execute('SELECT COUNT(*) from bookmarks where id '
                                         'BETWEEN ? AND ?', (low, high))
                        count = self.cur.fetchone()
                    if count[0] < 1:
                        print('Index %d-%d: 0 deleted' % (low, high))
                        return False

                    if self.print_rec(0, low, high, True) is True:
                        resp = input('Delete these bookmarks? (y/n): ')
                        if resp != 'y':
                            return False

                query = 'DELETE from bookmarks where id BETWEEN ? AND ?'
                with self.lock:
                    self.cur.execute(query, (low, high))
                    print('Index %d-%d: %d deleted' % (low, high, self.cur.rowcount))
                    if not self.cur.rowcount:
                        return False

                # Compact DB in a single operation for the range
                # Delayed commit is forced
                with self.lock:
                    self.compactdb(low, upto=high, delay_commit=True, retain_order=retain_order)
                    if not delay_commit:
                        self.conn.commit()
                        self.cur.execute('VACUUM')
            except IndexError:
                LOGERR('No matching index')
                return False
        elif index == 0:  # Remove the table
            return self.cleardb()
        else:  # Remove a single entry
            try:
                if chatty:
                    with self.lock:
                        self.cur.execute('SELECT COUNT(*) FROM bookmarks WHERE '
                                         'id = ? LIMIT 1', (index,))
                        count = self.cur.fetchone()
                    if count[0] < 1:
                        LOGERR('No matching index %d', index)
                        return False

                    if self.print_rec(index) is True:
                        resp = input('Delete this bookmark? (y/n): ')
                        if resp != 'y':
                            return False

                with self.lock:
                    query = 'DELETE FROM bookmarks WHERE id = ?'
                    self.cur.execute(query, (index,))
                    if self.cur.rowcount == 1:
                        print('Index %d deleted' % index)
                        self.compactdb(index, delay_commit=True, retain_order=retain_order)
                        if not delay_commit:
                            self.conn.commit()
                            self.cur.execute('VACUUM')
                    else:
                        LOGERR('No matching index %d', index)
                        return False
            except IndexError:
                LOGERR('No matching index %d', index)
                return False
            except sqlite3.OperationalError as e:
                LOGERR(e)
                return False

        return True

    def delete_resultset(self, results, retain_order=False):
        """Delete search results in descending order of DB index.

        Indices are expected to be unique and in ascending order.

        Notes
        -----
            This API forces a delayed commit.

        Parameters
        ----------
        results : list of tuples
            List of results to delete from DB.
        retain_order: bool
            Shift indices of multiple records instead of replacing
            the deleted record with the last one. Default is False.

        Returns
        -------
        bool
            True on success, False on failure.
        """
        if self.chatty:
            resp = read_in('Delete the search results? (y/n): ')
            if resp != 'y':
                return False

        # delete records in reverse order
        ids = sorted(set(x[0] for x in results))
        with self.lock:
            for pos, id in reversed(list(enumerate(ids))):
                self.delete_rec(id, delay_commit=True, retain_order=retain_order)

                # Commit at every 200th removal, counting from the end
                if pos % 200 == 0:
                    self.conn.commit()
                    self.cur.execute('VACUUM')

        return True

    def delete_rec_all(self, delay_commit=False):
        """Removes all records in the Bookmarks table.

        Parameters
        ----------
        delay_commit : bool
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        try:
            with self.lock:
                self.cur.execute('DELETE FROM bookmarks')
                if not delay_commit:
                    self.conn.commit()
                    self.cur.execute('VACUUM')
            return True
        except Exception as e:
            LOGERR('delete_rec_all(): %s', e)
            return False

    def cleardb(self):
        """Drops the bookmark table if it exists.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        resp = read_in('Remove ALL bookmarks? (y/n): ')
        if resp != 'y':
            print('No bookmarks deleted')
            return False

        if self.delete_rec_all():
            print('All bookmarks deleted')
            return True

        return False

    def print_rec(self, index: Optional[int | Sequence[int] | Set[int] | range] = 0,  # Optional[IntOrInts]
                  low: int = 0, high: int = 0, is_range: bool = False, order: List[str] = []) -> bool:
        """Print bookmark details at index or all bookmarks if index is 0.

        A negative index behaves like tail, if title is blank show "Untitled".

        Empty database check will run when `index` < 0 and `is_range` is False.

        Parameters
        -----------
        index : int | int[] | int{} | range, optional
            DB index(es) of record(s) to print. 0 or empty prints all records.
            Negative value prints out last `index` rows.
        low : int
            Actual lower index of range.
        high : int
            Actual higher index of range.
        is_range : bool
            A range is passed using low and high arguments.
            An index is ignored if is_range is True.
        order : list of str
            Order description (fields from JSON export or DB, prepended with '+'/'-' for ASC/DESC).

        Returns
        -------
        bool
            True on success, False on failure.

        Examples
        --------
        >>> import buku
        >>> from tempfile import NamedTemporaryFile
        >>> edb = buku.BukuDb(dbfile=NamedTemporaryFile().name)  # empty database
        >>> edb.print_rec()
        True

        Print negative index on empty database will log error and return False

        >>> edb.print_rec(-3)
        False

        print non empty database with default argument.

        >>> sdb = buku.BukuDb(dbfile=NamedTemporaryFile().name)  # single record database
        >>> sdb.add_rec('https://example.com')
        1
        >>> assert sdb.print_rec()
        1. Example Domain
           > https://example.com
        <BLANKLINE>

        Negative number on `high` and `low` parameters when is_range is True
        will log error and return False

        >>> sdb.print_rec(low=-1, high=-1, is_range=True)
        False
        >>> edb.print_rec(low=-1, high=-1, is_range=True)
        False
        """
        if isinstance(index, range) and index.step == 1 and index.start != 0:  # low=0 triggers custom behaviour
            return self.print_rec(None, is_range=True, low=index.start, high=index.stop-1, order=order)

        if not is_range and isinstance(index, int) and index < 0:
            # Show the last n records
            _id = self.get_max_id()
            if not _id:
                LOGERR('Empty database')
                return False

            low = (1 if _id <= -index else _id + index + 1)
            return self.print_rec(None, is_range=True, low=low, high=_id, order=order)

        _order = self._order(order)
        if is_range:
            if low < 0 or high < 0:
                LOGERR('Negative range boundary')
                return False

            if low > high:
                low, high = high, low

            try:
                # If range starts from 0 print all records
                with self.lock:
                    if low == 0:
                        query = f'SELECT * from bookmarks ORDER BY {_order}'
                        resultset = self.cur.execute(query)
                    else:
                        query = f'SELECT * from bookmarks where id BETWEEN ? AND ? ORDER BY {_order}'
                        resultset = self.cur.execute(query, (low, high))
            except IndexError:
                LOGERR('Index out of range')
                return False
        elif index:  # Show record at index
            try:
                if isinstance(index, int):
                    results = self._fetch('SELECT * FROM bookmarks WHERE id = ? LIMIT 1', index)
                else:
                    placeholder = ', '.join(['?'] * len(index))
                    results = self._fetch(f'SELECT * FROM bookmarks WHERE id IN ({placeholder}) ORDER BY {_order}', *index)
            except IndexError:
                results = None
            if not results:
                LOGERR('No matching index %s', index)
                return False

            single_record = len(results) == 1
            if self.json is None:
                print_rec_with_filter(results, self.field_filter)
            elif self.json:
                write_string_to_file(format_json(results, single_record, field_filter=self.field_filter), self.json)
            else:
                print_json_safe(results, single_record, field_filter=self.field_filter)

            return True
        else:  # Show all entries
            with self.lock:
                self.cur.execute(f'SELECT * FROM bookmarks ORDER BY {_order}')
                resultset = self.cur.fetchall()

        if not resultset:
            LOGERR('0 records')
            return True

        if self.json is None:
            print_rec_with_filter(resultset, self.field_filter)
        elif self.json:
            write_string_to_file(format_json(resultset, field_filter=self.field_filter), self.json)
        else:
            print_json_safe(resultset, field_filter=self.field_filter)

        return True

    def get_tag_all(self):
        """Get list of tags in DB.

        Returns
        -------
        tuple
            (list of unique tags sorted alphabetically,
             dictionary of {tag: usage_count}).
        """

        tags = []
        unique_tags = []
        dic = {}
        qry = 'SELECT DISTINCT tags, COUNT(tags) FROM bookmarks GROUP BY tags'
        with self.lock:
            for row in self.cur.execute(qry):
                tagset = row[0].strip(DELIM).split(DELIM)
                for tag in tagset:
                    if tag not in tags:
                        dic[tag] = row[1]
                        tags += (tag,)
                    else:
                        dic[tag] += row[1]

        if not tags:
            return tags, dic

        if tags[0] == '':
            unique_tags = sorted(tags[1:])
        else:
            unique_tags = sorted(tags)

        return unique_tags, dic

    def suggest_similar_tag(self, tagstr):
        """Show list of tags those go together in DB.

        Parameters
        ----------
        tagstr : str
            Original tag string.

        Returns
        -------
        str
            DELIM separated string of tags.
        """

        tags = tagstr.split(',')
        if not len(tags):
            return tagstr

        qry = 'SELECT DISTINCT tags FROM bookmarks WHERE tags LIKE ?'
        tagset = set()
        for tag in tags:
            if tag == '':
                continue

            with self.lock:
                self.cur.execute(qry, ('%' + delim_wrap(tag) + '%',))
                results = self.cur.fetchall()
            for row in results:
                # update tagset with unique tags in row
                tagset |= set(row[0].strip(DELIM).split(DELIM))

        # remove user supplied tags from tagset
        tagset.difference_update(tags)

        if not len(tagset):
            return tagstr

        unique_tags = sorted(tagset)

        print('similar tags:\n')
        for count, tag in enumerate(unique_tags):
            print('%d. %s' % (count + 1, tag))

        selected_tags = input('\nselect: ').split()
        print()
        if not selected_tags:
            return tagstr

        tags = [tagstr]
        for index in selected_tags:
            try:
                tags.append(delim_wrap(unique_tags[int(index) - 1]))
            except Exception as e:
                LOGERR(e)
                continue

        return parse_tags(tags)

    def replace_tag(self, orig: str, new: List[str] = []):
        """Replace original tag by new tags in all records.

        Remove original tag if new tag is empty.

        Parameters
        ----------
        orig : str
            Original tag.
        new : list
            Replacement tags.

        Raises
        -------
        ValueError: Invalid input(s) provided.
        RuntimeError: Tag deletion failed.

        """

        if DELIM in orig:
            raise ValueError("Original tag cannot contain delimiter ({}).".format(DELIM))

        orig = delim_wrap(orig)
        newtags = taglist_str(DELIM.join(new))

        if orig == newtags:
            raise ValueError("Original and replacement tags are the same.")

        # Remove original tag from DB if new tagset reduces to delimiter
        if newtags == DELIM:
            if not self.delete_tag_at_index(0, orig, chatty=self.chatty):
                raise RuntimeError("Tag deletion failed.")

        # Update bookmarks with original tag
        with self.lock:
            query = 'SELECT id, tags FROM bookmarks WHERE tags LIKE ?'
            self.cur.execute(query, ('%' + orig + '%',))
            results = self.cur.fetchall()
            if results:
                query = 'UPDATE bookmarks SET tags = ? WHERE id = ?'
                for row in results:
                    tags = row[1].replace(orig, newtags)
                    tags = parse_tags([tags])
                    self.cur.execute(query, (tags, row[0],))
                    print('Index %d updated' % row[0])

                self.conn.commit()

    def get_tagstr_from_taglist(self, id_list, taglist):
        """Get a string of delimiter-separated (and enclosed) string
        of tags from a dictionary of tags by matching ids.

        The inputs are the outputs from BukuDb.get_tag_all().

        Parameters
        ----------
        id_list : list
            List of ids.
        taglist : list
            List of tags.
        Returns
        -------
        str
            Delimiter separated and enclosed list of tags.
        """

        tags = DELIM

        for id in id_list:
            if is_int(id) and int(id) > 0:
                tags += taglist[int(id) - 1] + DELIM
            elif '-' in id:
                vals = [int(x) for x in id.split('-')]
                if vals[0] > vals[-1]:
                    vals[0], vals[-1] = vals[-1], vals[0]

                for _id in range(vals[0], vals[-1] + 1):
                    tags += taglist[_id - 1] + DELIM

        return tags

    def set_tag(self, cmdstr, taglist):
        """Append, overwrite, remove tags using the symbols >>, > and << respectively.

        Parameters
        ----------
        cmdstr : str
            Command pattern.
        taglist : list
            List of tags.

        Returns
        -------
        int
            Number of indices updated on success, -1 on failure, -2 on no symbol found.
        """

        if not cmdstr or not taglist:
            return -1

        flag = 0  # 0: invalid, 1: append, 2: overwrite, 3: remove
        index = cmdstr.find('>>')
        if index == -1:
            index = cmdstr.find('>')
            if index != -1:
                flag = 2
            else:
                index = cmdstr.find('<<')
                if index != -1:
                    flag = 3
        else:
            flag = 1

        if not flag:
            return -2

        tags = DELIM
        id_list = cmdstr[:index].split()
        try:
            tags = self.get_tagstr_from_taglist(id_list, taglist)
            if tags == DELIM and flag != 2:
                return -1
        except ValueError:
            return -1

        if flag != 2:
            index += 1

        with self.lock:
            update_count = 0
            query = 'UPDATE bookmarks SET tags = ? WHERE id = ?'
            try:
                db_id_list = cmdstr[index + 1:].split()
                for id in db_id_list:
                    if is_int(id) and int(id) > 0:
                        if flag == 1:
                            if self.append_tag_at_index(id, tags, True):
                                update_count += 1
                        elif flag == 2:
                            tags = parse_tags([tags])
                            self.cur.execute(query, (tags, id,))
                            update_count += self.cur.rowcount
                        else:
                            self.delete_tag_at_index(id, tags, True)
                            update_count += 1
                    elif '-' in id:
                        vals = [int(x) for x in id.split('-')]
                        if vals[0] > vals[-1]:
                            vals[0], vals[-1] = vals[-1], vals[0]

                        for _id in range(vals[0], vals[-1] + 1):
                            if flag == 1:
                                if self.append_tag_at_index(_id, tags, True):
                                    update_count += 1
                            elif flag == 2:
                                tags = parse_tags([tags])
                                self.cur.execute(query, (tags, _id,))
                                update_count += self.cur.rowcount
                            else:
                                if self.delete_tag_at_index(_id, tags, True):
                                    update_count += 1
                    else:
                        return -1
            except ValueError:
                return -1
            except sqlite3.IntegrityError:
                return -1

            try:
                self.conn.commit()
            except Exception as e:
                LOGERR(e)
                return -1

        return update_count

    def browse_by_index(self, index=0, low=0, high=0, is_range=False):
        """Open URL at index or range of indices in browser.

        Parameters
        ----------
        index : int
            Index to browse. 0 opens a random bookmark.
        low : int
            Actual lower index of range.
        high : int
            Higher index of range.
        is_range : bool
            A range is passed using low and high arguments.
            If True, index is ignored. Default is False.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        if is_range:
            if low < 0 or high < 0:
                LOGERR('Negative range boundary')
                return False

            if low > high:
                low, high = high, low

            try:
                # If range starts from 0 throw an error
                if low <= 0:
                    raise IndexError

                qry = 'SELECT URL from bookmarks where id BETWEEN ? AND ?'
                with self.lock:
                    for row in self.cur.execute(qry, (low, high)):
                        browse(row[0])
                return True
            except IndexError:
                LOGERR('Index out of range')
                return False

        if index < 0:
            LOGERR('Invalid index %d', index)
            return False

        if index == 0:
            max_id = self.get_max_id()
            if not max_id:
                print('No bookmarks added yet ...')
                return False

            index = random.randint(1, max_id)
            LOGDBG('Opening random index %d', index)

        qry = 'SELECT URL FROM bookmarks WHERE id = ? LIMIT 1'
        try:
            with self.lock:
                for row in self.cur.execute(qry, (index,)):
                    browse(row[0])
                    return True
            LOGERR('No matching index %d', index)
        except IndexError:
            LOGERR('No matching index %d', index)

        return False

    def exportdb(self, filepath: str, resultset: Optional[List[BookmarkVar]] = None,
                 order: List[str] = ['id'], pick: Optional[int] = None) -> bool:
        """Export DB bookmarks to file.
        Exports full DB, if resultset is None.
        Additionally, if run after a (batch) update with export_on, only export those records.

        If destination file name ends with '.db', bookmarks are
        exported to a buku database file.
        If destination file name ends with '.md', bookmarks are
        exported to a Markdown file.
        If destination file name ends with '.org' bookmarks are
        exported to an org file.
        If destination file name ends with '.xbel' bookmarks are
        exported to a XBEL file.
        If destination file name ends with '.rss'/'.atom' bookmarks are
        exported to an RSS file.
        Otherwise, bookmarks are exported to a Firefox bookmarks.html
        formatted file.

        Parameters
        ----------
        filepath : str
            Path to export destination file.
        resultset : list of tuples
            List of results to export. Use `None` to get current DB.
            Ignored if run after a (batch) update with export_on.
        order : list of str
            Order description (fields from JSON export or DB, prepended with '+'/'-' for ASC/DESC).
        pick : int, optional
            Reduce the export to a random subset of up to given (positive) size. Default is None.


        Returns
        -------
        bool
            True on success, False on failure.
        """

        count = 0

        if not resultset:
            resultset = self.get_rec_all(order=order)
            if not resultset:
                print('No records found')
                return False

        old = self._to_export or {}
        if self._to_export is not None:
            _resultset = dict(old)
            _resultset.update({x.url: x for x in resultset if x.url in old})
            resultset = self._sort(_resultset.values(), order)
            self._to_export = None
            if not resultset:
                print('No records to export')
                return False

        if pick and pick < len(resultset):
            resultset = self._sort(random.sample(resultset, pick), order)

        if os.path.exists(filepath):
            resp = read_in(filepath + ' exists. Overwrite? (y/n): ')
            if resp != 'y':
                return False

            if filepath.endswith('.db'):
                os.remove(filepath)

        if filepath.endswith('.db'):
            outdb = BukuDb(dbfile=filepath)
            qry = 'INSERT INTO bookmarks(URL, metadata, tags, desc, flags) VALUES (?, ?, ?, ?, ?)'
            for row in resultset:
                _old = old.get(row.url)
                _add = (f' (OLD URL = {_old})' if isinstance(_old, str) and _old != row.url else
                        ' (DELETED)' if _old is row else '')
                title = ((row.title or '') + _add if _add else row.title)
                outdb.cur.execute(qry, (row.url, title, row.tags_raw, row.desc, row.flags))
                count += 1
            outdb.conn.commit()
            outdb.close()
            print('%s exported' % count)
            return True

        with open(filepath, mode='w', encoding='utf-8') as outfp:
            res = {}  # type: Dict
            if filepath.endswith('.md'):
                res = convert_bookmark_set(resultset, 'markdown', old)
                count += res['count']
                outfp.write(res['data'])
            elif filepath.endswith('.org'):
                res = convert_bookmark_set(resultset, 'org', old)
                count += res['count']
                outfp.write(res['data'])
            elif filepath.endswith('.xbel'):
                res = convert_bookmark_set(resultset, 'xbel', old)
                count += res['count']
                outfp.write(res['data'])
            elif filepath.endswith('.rss') or filepath.endswith('.atom'):
                res = convert_bookmark_set(resultset, 'rss', old)
                count += res['count']
                outfp.write(res['data'])
            else:
                res = convert_bookmark_set(resultset, 'html', old)
                count += res['count']
                outfp.write(res['data'])
            print('%s exported' % count)
            return True
        return False

    def traverse_bm_folder(self, sublist, unique_tag, folder_name, add_parent_folder_as_tag):
        """Traverse bookmark folders recursively and find bookmarks.

        Parameters
        ----------
        sublist : list
            List of child entries in bookmark folder.
        unique_tag : str
            Timestamp tag in YYYYMonDD format.
        folder_name : str
            Name of the parent folder.
        add_parent_folder_as_tag : bool
            True if bookmark parent folders should be added as tags else False.

        Returns
        -------
        tuple
            Bookmark record data.
        """

        for item in sublist:
            if item['type'] == 'folder':
                next_folder_name = folder_name + DELIM + strip_delim(item['name'])
                yield from self.traverse_bm_folder(
                        item['children'],
                        unique_tag,
                        next_folder_name,
                        add_parent_folder_as_tag)
            elif item['type'] == 'url':
                try:
                    if is_nongeneric_url(item['url']):
                        continue
                except KeyError:
                    continue

                tags = ''
                if add_parent_folder_as_tag:
                    tags += folder_name
                if unique_tag:
                    tags += DELIM + unique_tag
                yield (item['url'], item['name'], parse_tags([tags]), None, 0, True, False)

    def load_chrome_database(self, path, unique_tag, add_parent_folder_as_tag):
        """Open Chrome Bookmarks JSON file and import data.

        Parameters
        ----------
        path : str
            Path to Google Chrome bookmarks file.
        unique_tag : str
            Timestamp tag in YYYYMonDD format.
        add_parent_folder_as_tag : bool
            True if bookmark parent folders should be added as tags else False.
        """

        with open(path, 'r', encoding="utf8") as datafile:
            data = json.load(datafile)

        roots = data['roots']
        for entry in roots:
            # Needed to skip 'sync_transaction_version' key from roots
            if isinstance(roots[entry], str):
                continue
            for item in self.traverse_bm_folder(
                    roots[entry]['children'],
                    unique_tag,
                    roots[entry]['name'],
                    add_parent_folder_as_tag):
                self.add_rec(*item)

    def load_firefox_database(self, path, unique_tag, add_parent_folder_as_tag):
        """Connect to Firefox sqlite db and import bookmarks into BukuDb.

        Parameters
        ----------
        path : str
            Path to Firefox bookmarks sqlite database.
        unique_tag : str
            Timestamp tag in YYYYMonDD format.
        add_parent_folder_as_tag : bool
            True if bookmark parent folders should be added as tags else False.
        """

        # Connect to input DB
        conn = sqlite3.connect('file:%s?mode=ro' % path, uri=True)

        cur = conn.cursor()
        res = cur.execute('SELECT DISTINCT fk, parent, title FROM moz_bookmarks WHERE type=1')
        # get id's and remove duplicates
        for row in res.fetchall():
            # get the url
            res = cur.execute('SELECT url FROM moz_places where id={}'.format(row[0]))
            url = res.fetchone()[0]
            if is_nongeneric_url(url):
                continue

            # get tags
            res = cur.execute('SELECT parent FROM moz_bookmarks WHERE '
                              'fk={} AND title IS NULL'.format(row[0]))
            bm_tag_ids = [tid for item in res.fetchall() for tid in item]

            bookmark_tags = []
            for bm_tag_id in bm_tag_ids:
                res = cur.execute('SELECT title FROM moz_bookmarks WHERE id={}'.format(bm_tag_id))
                bookmark_tags.append(res.fetchone()[0])

            if add_parent_folder_as_tag:
                # add folder name
                parent_id = row[1]
                while parent_id:
                    res = cur.execute('SELECT title,parent FROM moz_bookmarks '
                                      'WHERE id={}'.format(parent_id))
                    parent = res.fetchone()
                    if parent:
                        title, parent_id = parent
                        bookmark_tags.append(title)

            if unique_tag:
                # add timestamp tag
                bookmark_tags.append(unique_tag)

            formatted_tags = [DELIM + strip_delim(tag) for tag in bookmark_tags]
            tags = parse_tags(formatted_tags)

            # get the title
            title = row[2] or ''

            self.add_rec(url, title, tags, None, 0, True, False)
        try:
            cur.close()
            conn.close()
        except Exception as e:
            LOGERR(e)

    def load_edge_database(self, path, unique_tag, add_parent_folder_as_tag):
        """Open Edge Bookmarks JSON file and import data.

        Parameters
        ----------
        path : str
            Path to Microsoft Edge bookmarks file.
        unique_tag : str
            Timestamp tag in YYYYMonDD format.
        add_parent_folder_as_tag : bool
            True if bookmark parent folders should be added as tags else False.
        """

        with open(path, 'r', encoding="utf8") as datafile:
            data = json.load(datafile)

        roots = data['roots']
        for entry in roots:
            # Needed to skip 'sync_transaction_version' key from roots
            if isinstance(roots[entry], str):
                continue
            for item in self.traverse_bm_folder(
                    roots[entry]['children'],
                    unique_tag,
                    roots[entry]['name'],
                    add_parent_folder_as_tag):
                self.add_rec(*item)

    def auto_import_from_browser(self, firefox_profile=None):
        """Import bookmarks from a browser default database file.

        Supports Firefox, Google Chrome, Vivaldi, and Microsoft Edge.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        if sys.platform.startswith(('linux', 'freebsd', 'openbsd')):
            gc_bm_db_path = '~/.config/google-chrome/Default/Bookmarks'
            cb_bm_db_path = '~/.config/chromium/Default/Bookmarks'
            vi_bm_db_path = '~/.config/vivaldi/Default/Bookmarks'
            me_bm_db_path = '~/.config/microsoft-edge/Default/Bookmarks'
            default_ff_folder = '~/.mozilla/firefox'
        elif sys.platform == 'darwin':
            gc_bm_db_path = '~/Library/Application Support/Google/Chrome/Default/Bookmarks'
            cb_bm_db_path = '~/Library/Application Support/Chromium/Default/Bookmarks'
            vi_bm_db_path = '~/Library/Application Support/Vivaldi/Default/Bookmarks'
            me_bm_db_path = '~/Library/Application Support/Microsoft Edge/Default/Bookmarks'
            default_ff_folder = '~/Library/Application Support/Firefox'
        elif sys.platform == 'win32':
            gc_bm_db_path = os.path.expandvars('%LOCALAPPDATA%/Google/Chrome/User Data/Default/Bookmarks')
            cb_bm_db_path = os.path.expandvars('%LOCALAPPDATA%/Chromium/User Data/Default/Bookmarks')
            vi_bm_db_path = os.path.expandvars('%LOCALAPPDATA%/Vivaldi/User Data/Default/Bookmarks')
            me_bm_db_path = os.path.expandvars('%LOCALAPPDATA%/Microsoft/Edge/User Data/Default/Bookmarks')
            default_ff_folder = os.path.expandvars('%APPDATA%/Mozilla/Firefox/')
        else:
            LOGERR('buku does not support {} yet'.format(sys.platform))
            self.close_quit(1)
            return  # clarifying execution interrupt for the linter

        ff_bm_db_paths = get_firefox_db_paths(default_ff_folder, firefox_profile)

        if self.chatty:
            resp = input('Generate auto-tag (YYYYMonDD)? (y/n): ')
            if resp == 'y':
                newtag = gen_auto_tag()
            else:
                newtag = None
            resp = input('Add parent folder names as tags? (y/n): ')
        else:
            newtag = None
            resp = 'y'
        add_parent_folder_as_tag = resp == 'y'

        with self.lock:
            resp = 'y'

            chrome_based = {'Google Chrome': gc_bm_db_path, 'Chromium': cb_bm_db_path, 'Vivaldi': vi_bm_db_path}
            for name, path in chrome_based.items():
                try:
                    if os.path.isfile(os.path.expanduser(path)):
                        if self.chatty:
                            resp = input(f'Import bookmarks from {name}? (y/n): ')
                        if resp == 'y':
                            bookmarks_database = os.path.expanduser(path)
                            if not os.path.exists(bookmarks_database):
                                raise FileNotFoundError
                            self.load_chrome_database(bookmarks_database, newtag, add_parent_folder_as_tag)
                except Exception as e:
                    LOGERR(e)
                    print(f'Could not import bookmarks from {name}')

            try:
                ff_bm_db_paths = {k: s for k, s in ff_bm_db_paths.items() if os.path.isfile(os.path.expanduser(s))}
                for idx, (name, ff_bm_db_path) in enumerate(ff_bm_db_paths.items(), start=1):
                    if self.chatty:
                        profile = ('' if len(ff_bm_db_paths) < 2 else
                                   f' profile {name} [{idx}/{len(ff_bm_db_paths)}]')
                        resp = input(f'Import bookmarks from Firefox{profile}? (y/n): ')
                    if resp == 'y':
                        bookmarks_database = os.path.expanduser(ff_bm_db_path)
                        if not os.path.exists(bookmarks_database):
                            raise FileNotFoundError
                        self.load_firefox_database(bookmarks_database, newtag, add_parent_folder_as_tag)
                        break
            except Exception as e:
                LOGERR(e)
                print('Could not import bookmarks from Firefox.')

            try:
                if os.path.isfile(os.path.expanduser(me_bm_db_path)):
                    if self.chatty:
                        resp = input('Import bookmarks from microsoft edge? (y/n): ')
                    if resp == 'y':
                        bookmarks_database = os.path.expanduser(me_bm_db_path)
                        if not os.path.exists(bookmarks_database):
                            raise FileNotFoundError
                        self.load_edge_database(bookmarks_database, newtag, add_parent_folder_as_tag)
            except Exception as e:
                LOGERR(e)
                print('Could not import bookmarks from microsoft-edge')

            self.conn.commit()

        if newtag:
            print('\nAuto-generated tag: %s' % newtag)

    def importdb(self, filepath, tacit=False):
        """Import bookmarks from an HTML or a Markdown file.

        Supports Firefox, Google Chrome, and IE exported HTML bookmarks.
        Supports XBEL standard bookmarks.
        Supports RSS files with extension '.rss', '.atom'.
        Supports Markdown files with extension '.md', '.org'.
        Supports importing bookmarks from another buku database file.

        Parameters
        ----------
        filepath : str
            Path to file to import.
        tacit : bool
            If True, no questions asked and folder names are automatically
            imported as tags from bookmarks HTML.
            If True, automatic timestamp tag is NOT added.
            Default is False.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        if filepath.endswith('.db'):
            return self.mergedb(filepath)

        newtag = None
        append_tags_resp = 'y'
        if not tacit:
            if input('Generate auto-tag (YYYYMonDD)? (y/n): ') == 'y':
                newtag = gen_auto_tag()
            append_tags_resp = input('Append tags when bookmark exist? (y/n): ')

        items = []
        if filepath.endswith('.md'):
            items = import_md(filepath=filepath, newtag=newtag)
        elif filepath.endswith('org'):
            items = import_org(filepath=filepath, newtag=newtag)
        elif filepath.endswith('rss') or filepath.endswith('atom'):
            items = import_rss(filepath=filepath, newtag=newtag)
        elif filepath.endswith('json'):
            if not tacit:
                resp = input('Add parent folder names as tags? (y/n): ')
            else:
                resp = 'y'
            add_bookmark_folder_as_tag = resp == 'y'
            try:
                with open(filepath, 'r', encoding='utf-8') as datafile:
                    data = json.load(datafile)

                items = import_firefox_json(data, add_bookmark_folder_as_tag, newtag)
            except ValueError as e:
                LOGERR("ff_json: JSON Decode Error: {}".format(e))
                return False
            except Exception as e:
                LOGERR(e)
                return False
        elif filepath.endswith('xbel'):
            try:
                with open(filepath, mode='r', encoding='utf-8') as infp:
                    soup = BeautifulSoup(infp, 'html.parser')
            except ImportError:
                LOGERR('Beautiful Soup not found')
                return False
            except Exception as e:
                LOGERR(e)
                return False

            add_parent_folder_as_tag = False
            use_nested_folder_structure = False
            if not tacit:
                resp = input("""Add bookmark's parent folder as tag?
a: add all parent folders of the bookmark
n: don't add parent folder as tag
(a/[n]): """)
            else:
                resp = 'y'

            if resp == 'a':
                add_parent_folder_as_tag = True
                use_nested_folder_structure = True

            items = import_xbel(soup, add_parent_folder_as_tag, newtag, use_nested_folder_structure)
            infp.close()
        else:
            try:
                with open(filepath, mode='r', encoding='utf-8') as infp:
                    soup = BeautifulSoup(infp, 'html.parser')
            except ImportError:
                LOGERR('Beautiful Soup not found')
                return False
            except Exception as e:
                LOGERR(e)
                return False

            add_parent_folder_as_tag = False
            use_nested_folder_structure = False
            if not tacit:
                resp = input("""Add bookmark's parent folder as tag?
y: add single, direct parent folder
a: add all parent folders of the bookmark
n: don't add parent folder as tag
(y/a/[n]): """)
            else:
                resp = 'y'

            if resp in ('y', 'a'):
                add_parent_folder_as_tag = True
                if resp == 'a':
                    use_nested_folder_structure = True

            items = import_html(soup, add_parent_folder_as_tag, newtag, use_nested_folder_structure)
            infp.close()

        with self.lock:
            for item in items:
                add_rec_res = self.add_rec(*item)
                if not add_rec_res and append_tags_resp == 'y':
                    rec_id = self.get_rec_id(item[0])
                    self.append_tag_at_index(rec_id, item[2])

            self.conn.commit()

        if newtag:
            print('\nAuto-generated tag: %s' % newtag)

        return True

    def mergedb(self, path):
        """Merge bookmarks from another buku database file.

        Parameters
        ----------
        path : str
            Path to DB file to merge.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        try:
            # Connect to input DB
            indb_conn = sqlite3.connect('file:%s?mode=ro' % path, uri=True)

            indb_cur = indb_conn.cursor()
            indb_cur.execute('SELECT * FROM bookmarks')
        except Exception as e:
            LOGERR(e)
            return False

        resultset = indb_cur.fetchall()
        if resultset:
            with self.lock:
                for row in bookmark_vars(resultset):
                    self.add_rec(row.url, row.title, row.tags_raw, row.desc, row.flags, True, False)

                self.conn.commit()

        try:
            indb_cur.close()
            indb_conn.close()
        except Exception:
            pass

        return True

    def tnyfy_url(
            self,
            index: Optional[int] = None,
            url: Optional[str] = None,
            shorten: bool = True) -> Optional[str]:
        """Shorten/expand a URL using the tny.im service.

        Tny.im is no longer available; don't use this method.
        """
        warn('\'BukuDb.tnyfy_url()\' no longer works due to the takedown of tny.im service.', DeprecationWarning)

    def browse_cached_url(self, arg):
        """Open URL at index or URL.

        Parameters
        ----------
        arg : str
            Index or url to browse

        Returns
        -------
        str
            Wayback Machine URL, None if not cached
        """

        from urllib.parse import quote_plus

        if is_int(arg):
            rec = self.get_rec_by_id(int(arg))
            if not rec:
                LOGERR('No matching index %d', int(arg))
                return None
            url = rec[1]
        else:
            url = arg

        # Try fetching cached page from Wayback Machine
        api_url = 'https://archive.org/wayback/available?url=' + quote_plus(url)
        manager = get_PoolManager()
        resp = manager.request('GET', api_url)
        respobj = json.loads(resp.data)
        try:
            if (
                    len(respobj['archived_snapshots']) and
                    respobj['archived_snapshots']['closest']['available'] is True):
                manager.clear()
                return respobj['archived_snapshots']['closest']['url']
        except Exception:
            pass
        finally:
            manager.clear()

        LOGERR('Uncached')
        return None

    def fixtags(self):
        """Undocumented API to fix tags set in earlier versions.

        Functionalities:

        1. Remove duplicate tags
        2. Sort tags
        3. Use lower case to store tags
        """

        to_commit = False
        with self.lock:
            self.cur.execute('SELECT id, tags FROM bookmarks ORDER BY id ASC')
            resultset = self.cur.fetchall()
            query = 'UPDATE bookmarks SET tags = ? WHERE id = ?'
            for row in resultset:
                oldtags = row[1]
                if oldtags == DELIM:
                    continue

                tags = parse_tags([oldtags])
                if tags == oldtags:
                    continue

                self.cur.execute(query, (tags, row[0],))
                to_commit = True

            if to_commit:
                self.conn.commit()

    def close(self):
        """Close a DB connection."""

        if self.conn is not None:
            try:
                self.cur.close()
                self.conn.close()
            except Exception:
                # ignore errors here, we're closing down
                pass

    def close_quit(self, exitval=0):
        """Close a DB connection and exit.

        Parameters
        ----------
        exitval : int
            Program exit value.
        """

        if self.conn is not None:
            try:
                self.cur.close()
                self.conn.close()
            except Exception:
                # ignore errors here, we're closing down
                pass
        sys.exit(exitval)


class ExtendedArgumentParser(argparse.ArgumentParser):
    """Extend classic argument parser."""

    def __init__(self, *args, **kwargs):
        self._nodefaults, self._unset = None, object()
        super().__init__(*args, **kwargs)
        self._nodefaults = argparse.ArgumentParser(*args, **kwargs)

    def _add_argument(self, old_add_arg, nodefaults, *args, **kwargs):
        old_add_arg(*args, **kwargs)
        kwargs = dict(kwargs)
        kwargs.pop('type', None)
        kwargs.pop('choices', None)
        kwargs['default'] = self._unset
        nodefaults and nodefaults.add_argument(*args, **kwargs)

    def add_argument(self, *args, **kwargs):
        self._add_argument(super().add_argument, self._nodefaults, *args, **kwargs)

    def add_argument_group(self, *args, **kwargs):
        group = super().add_argument_group(*args, **kwargs)
        nodefaults = self._nodefaults and self._nodefaults.add_argument_group(*args, **kwargs)
        old_add_arg = group.add_argument
        group.add_argument = lambda *a, **kw: self._add_argument(old_add_arg, nodefaults, *a, **kw)
        return group

    def parse_args(self, *args, **kwargs):
        result = super().parse_args(*args, **kwargs)
        nodefaults = self._nodefaults.parse_args(*args, **kwargs)
        params = {k for k in dir(nodefaults) if not k.startswith('_')}
        setattr(result, '_passed', {k for k in params if getattr(nodefaults, k) != self._unset})
        return result

    @staticmethod
    def program_info(file=sys.stdout):
        """Print program info.

        Parameters
        ----------
        file : file
            File to write program info to. Default is sys.stdout.
        """
        if sys.platform == 'win32' and file == sys.stdout:
            file = sys.stderr

        file.write('''
SYMBOLS:
      >                    url
      +                    comment
      #                    tags

Version %s
Copyright © 2015-2025 %s
License: %s
Webpage: https://github.com/jarun/buku
''' % (__version__, __author__, __license__))

    @staticmethod
    def prompt_help(file=sys.stdout):
        """Print prompt help.

        Parameters
        ----------
        file : file
            File to write program info to. Default is sys.stdout.
        """
        file.write('''
PROMPT KEYS:
    1-N                    browse search result indices and/or ranges
    R [N]                  print out N random search results
                           (or random bookmarks if negative or N/A)
    ^ id1 id2              swap two records at specified indices
    O [id|range [...]]     open search results/indices in GUI browser
                           toggle try GUI browser if no arguments
    a                      open all results in browser
    s keyword [...]        search for records with ANY keyword
    S keyword [...]        search for records with ALL keywords
    d                      match substrings ('pen' matches 'opened')
    m                      search with markers - search string is split
                           into keywords by prefix markers, which determine
                           what field the keywords is searched in:
                           '.', '>' or ':' - title, description or URL
                           '#'/'#,' - tags (comma-separated, partial/full match)
                           '*' - all fields (can be omitted in the 1st keyword)
                           note: tag marker is not affected by 'd' (deep search)
    v fields               change sorting order (default is '+index')
                           multiple comma/space separated fields can be specified
    r expression           run a regex search
    t [tag, ...]           search by tags; show taglist, if no args
    g taglist id|range [...] [>>|>|<<] [record id|range ...]
                           append, set, remove (all or specific) tags
                           search by taglist id(s) if records are omitted
    n                      show next page of search results
    N                      show previous page of search results
    o id|range [...]       browse bookmarks by indices and/or ranges
    p id|range [...]       print bookmarks by indices and/or ranges
    w [editor|id]          edit and add or update a bookmark
    c id                   copy url at search result index to clipboard
    DB [name]              check existing DB list or switch to another DB
                           (use full/dir path to switch folders)
                           '~.' can be used as shortcut for default DB
    ?                      show this help
    q, ^D, double Enter    exit buku

''')

    @staticmethod
    def is_colorstr(arg):
        """Check if a string is a valid color string.

        Parameters
        ----------
        arg : str
            Color string to validate.

        Returns
        -------
        str
            Same color string that was passed as an argument.

        Raises
        ------
        ArgumentTypeError
            If the arg is not a valid color string.
        """
        try:
            assert len(arg) == 5
            for c in arg:
                assert c in COLORMAP
        except AssertionError as e:
            raise argparse.ArgumentTypeError('%s is not a valid color string' % arg) from e
        return arg

    # Help
    def print_help(self, file=sys.stdout):
        """Print help prompt.

        Parameters
        ----------
        file : file
            File to write program info to. Default is sys.stdout.
        """
        super().print_help(file)
        self.program_info(file)


# ----------------
# Helper functions
# ----------------


ConverterResult = TypedDict('ConverterResult', {'data': str, 'count': int}) if TypedDict else Dict[str, Any]


def convert_tags_to_org_mode_tags(tags: str) -> str:
    """convert buku tags to org-mode compatible tags."""
    if tags != DELIM:
        buku_tags = tags.split(DELIM)[1:-1]
        buku_tags = [re.sub(r'[^a-zA-Z0-9_@]', ' ', tag) for tag in buku_tags]
        buku_tags = [re.sub(r'\s+', ' ', tag) for tag in buku_tags]
        buku_tags = taglist(x.replace(' ', '_') for x in buku_tags)
        if buku_tags:
            return ' :{}:\n'.format(':'.join(buku_tags))
    return '\n'


def convert_bookmark_set(
        bookmark_set: List[BookmarkVar],
        export_type: str,
        old: Optional[Dict[str, str | BookmarkVar]] = None) -> ConverterResult:  # type: ignore
    """Convert list of bookmark set into multiple data format.

    Parameters
    ----------
        bookmark_set: bookmark set
        export_type: one of supported type: markdown, html, org, XBEL
        old: cached values of deleted records/replaced URLs to save

    Returns
    -------
        converted data and count of converted bookmark set
    """
    import html
    assert export_type in ['markdown', 'html', 'org', 'xbel', 'rss']
    #  compatibility
    resultset = bookmark_vars(bookmark_set)
    old = old or {}

    def title(row):
        _old = old.get(row.url)
        _add = (f' (OLD URL = {_old})' if isinstance(_old, str) and _old != row.url else
                ' (DELETED)' if _old == row else '')
        return (row.title or '') + _add

    count = 0
    out = ''
    if export_type == 'markdown':
        for row in resultset:
            _title = title(row)
            out += (f'- <{row.url}>' if not _title else f'- [{_title}]({row.url})')

            if row.tags:
                out += ' <!-- TAGS: {} -->\n'.format(row.tags)
            else:
                out += '\n'

            count += 1
    elif export_type == 'org':
        for row in resultset:
            _title = title(row)
            out += (f'* [[{row.url}]]' if not _title else f'* [[{row.url}][{_title}]]')
            out += convert_tags_to_org_mode_tags(row.tags_raw)
            count += 1
    elif export_type == 'xbel':
        timestamp = str(int(time.time()))
        out = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE xbel PUBLIC \
"+//IDN python.org//DTD XML Bookmark Exchange Language 1.0//EN//XML" \
"http://pyxml.sourceforge.net/topics/dtds/xbel.dtd">\n\n'
            '<xbel version="1.0">\n')

        for row in resultset:
            out += '    <bookmark href="%s"' % (html.escape(row.url)).encode('ascii', 'xmlcharrefreplace').decode('utf-8')
            if row.tags:
                out += ' TAGS="' + html.escape(row.tags).encode('ascii', 'xmlcharrefreplace').decode('utf-8') + '"'
            out += '>\n        <title>{}</title>'\
                .format(html.escape(title(row)).encode('ascii', 'xmlcharrefreplace').decode('utf-8'))
            if row.desc:
                out += '\n        <desc>{}</desc>'.format(html.escape(row.desc).encode('ascii', 'xmlcharrefreplace').decode('utf-8'))
            out += '\n    </bookmark>\n'
            count += 1

        out += '</xbel>'
    elif export_type == 'rss':
        out = (
            '<feed xmlns="http://www.w3.org/2005/Atom">\n'
            '    <title>Bookmarks</title>\n'
            '    <generator uri="https://github.com/jarun/buku">buku</generator>\n'
        )

        for row in resultset:
            out += '    <entry>\n'
            out += '        <title>' + title(row) + '</title>\n'
            _url = html.escape(row.url).encode('ascii', 'xmlcharrefreplace').decode('utf-8')
            out += '        <link href="%s" rel="alternate" type="text/html"/>\n' % _url
            out += '        <id>%s</id>\n' % row.id
            for tag in (t for t in row.tags.split(',') if t):
                _tag = html.escape(tag).encode('ascii', 'xmlcharrefreplace').decode('utf-8')
                out += '        <category term="%s"/>\n' % _tag
            if row.desc:
                _desc = html.escape(row.desc).encode('ascii', 'xmlcharrefreplace').decode('utf-8')
                out += '        <content type="html"> <![CDATA[ <p>%s</p> ]]> </content>\n' % _desc
            out += '    </entry>\n'
            count += 1

        out += '</feed>'
    elif export_type == 'html':
        timestamp = str(int(time.time()))
        out = (
            '<!DOCTYPE NETSCAPE-Bookmark-file-1>\n\n'
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
            '<TITLE>Bookmarks</TITLE>\n'
            '<H1>Bookmarks</H1>\n\n'
            '<DL><p>\n'
            '    <DT><H3 ADD_DATE="{0}" LAST_MODIFIED="{0}" '
            'PERSONAL_TOOLBAR_FOLDER="true">buku bookmarks</H3>\n'
            '    <DL><p>\n'.format(timestamp))

        for row in resultset:
            out += '        <DT><A HREF="%s" ADD_DATE="%s" LAST_MODIFIED="%s"' % (row.url, timestamp, timestamp)
            if row.tags:
                out += ' TAGS="' + row.tags + '"'
            out += '>{}</A>\n'.format(title(row))
            if row.desc:
                out += '        <DD>' + row.desc + '\n'
            count += 1

        out += '    </DL><p>\n</DL><p>'

    return {'data': out, 'count': count}


def get_firefox_profile_names(path):
    """List folder and detect default Firefox profile names for all installs.

    Returns
    -------
    profiles : [str]
        All default Firefox profile names.
    """
    from configparser import ConfigParser, NoOptionError

    profiles = []
    profile_path = os.path.expanduser(os.path.join(path, 'profiles.ini'))
    if os.path.exists(profile_path):
        config = ConfigParser()
        config.read(profile_path)

        install_names = [section for section in config.sections() if section.startswith('Install')]
        for name in install_names:
            try:
                profiles += [config.get(name, 'default')]
            except NoOptionError:
                pass
        if profiles:
            return profiles

        profiles_names = [section for section in config.sections() if section.startswith('Profile')]
        for name in profiles_names:
            try:
                # If profile is default
                if config.getboolean(name, 'default'):
                    profiles += [config.get(name, 'path')]
                    continue
            except NoOptionError:
                pass
            try:
                # alternative way to detect default profile
                if config.get(name, 'name').lower() == "default":
                    profiles += [config.get(name, 'path')]
            except NoOptionError:
                pass

        return profiles

    # There are no default profiles
    LOGDBG('get_firefox_profile_names(): {} does not exist'.format(path))
    return profiles

def get_firefox_db_paths(default_ff_folder, specified=None):
    profiles = ([specified] if specified else get_firefox_profile_names(default_ff_folder))
    _profile_path = lambda s: (s if os.path.isabs(s) else os.path.join(default_ff_folder, s))
    return {s: os.path.join(_profile_path(s), 'places.sqlite') for s in profiles}


def walk(root):
    """Recursively iterate over JSON.

    Parameters
    ----------
    root : JSON element
        Base node of the JSON data.
    """

    for element in root['children']:
        if element['type'] == 'url':
            url = element['url']
            title = element['name']
            yield (url, title, None, None, 0, True)
        else:
            walk(element)


def import_md(filepath: str, newtag: Optional[str]):
    """Parse bookmark Markdown file.

    Parameters
    ----------
    filepath : str
        Path to Markdown file.
    newtag : str, optional
        New tag for bookmarks in Markdown file.

    Returns
    -------
    tuple
        Parsed result.
    """
    # Supported Markdown format: `[title](url) <!-- TAGS: tags -->` (or `<url> <!-- TAGS: tags -->`)
    _named_link, _raw_link = r'\[(?P<title>.*)\]\((?P<url>.+)\)', r'\<(?P<url_raw>[^!>][^>]*)\>'
    pattern = re.compile(r'(%s|%s)(\s+<!-- TAGS: (?P<tags>.*) -->)?' % (_named_link, _raw_link))
    with open(filepath, mode='r', encoding='utf-8') as infp:
        for line in infp:
            if match := pattern.search(line):
                title = match.group('title') or ''
                url = match.group('url') or match.group('url_raw')

                if is_nongeneric_url(url):
                    continue

                tags = DELIM.join(s for s in [newtag, match.group('tags')] if s)
                tags = parse_tags([tags])

                yield (url, title, delim_wrap(tags), None, 0, True, False)

def import_rss(filepath: str, newtag: Optional[str]):
    """Parse bookmark RSS file.

    Parameters
    ----------
    filepath : str
        Path to RSS file.
    newtag : str, optional
        New tag for bookmarks in RSS file.

    Returns
    tuple
        Parsed result.
    """

    with open(filepath, mode='r', encoding='utf-8') as infp:
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        root = ET.fromstring(infp.read())
        for entry in root.findall('atom:entry', ns):
            title = entry.find('atom:title', ns).text
            url = entry.find('atom:link', ns).attrib['href']
            tags = ','.join([tag.attrib['term'] for tag in entry.findall('atom:category', ns)])
            if newtag is not None:
                tags = newtag + ',' + tags
            desc = entry.find('atom:content', ns)
            desc = desc.text if desc is not None else None
            yield (url, title, delim_wrap(tags), desc, 0, True, False)

def import_org(filepath: str, newtag: Optional[str]):
    """Parse bookmark org file.

    Parameters
    ----------
    filepath : str
        Path to org file.
    newtag : str, optional
        New tag for bookmarks in org file.

    Returns
    -------
    tuple
        Parsed result.
    """
    def get_org_tags(tag_string):
        """Extracts tags from Org

        Parameters
        ----------
        tag_string: str
             string of tags in Org-format

        Syntax: Org splits tags with colons. If colons are part of a buku-tag, this is indicated by using
                multiple colons in org. If a buku-tag starts or ends with a colon, this is indicated by a
                preceding or trailing whitespace

        Returns
        -------
        list
            List of tags
        """
        tag_list_raw = [s for s in re.split(r'(?<!\:)\:', tag_string) if s]
        tag_list_cleaned = []
        for i, tag in enumerate(tag_list_raw):
            if tag.startswith(":"):
                if tag_list_raw[i-1] == ' ':
                    tag_list_cleaned.append(tag.strip())
                else:
                    new_item = tag_list_cleaned[-1] + tag
                    del tag_list_cleaned[-1]
                    tag_list_cleaned.append(new_item.strip())
            elif tag != ' ':
                tag_list_cleaned.append(tag.strip())
        return tag_list_cleaned

    # Supported OrgMode format: `[[url][title]] :tags:` (or `[[url]] :tags:`)
    _url, _maybe_title = r'(?P<url>((?!\]\[).)+?)', r'(\]\[(?P<title>.+))?'
    pattern = re.compile(r'\[\[%s%s\]\](?P<tags>\s+:.*:)?' % (_url, _maybe_title))
    with open(filepath, mode='r', encoding='utf-8') as infp:
        for line in infp:
            if match := pattern.search(line):
                title = match.group('title') or ''
                url = match.group('url')

                if is_nongeneric_url(url):
                    continue

                tags = list(dict.fromkeys(get_org_tags(match.group('tags') or '')))
                tags_string = DELIM.join(tags)
                if newtag and newtag.lower() not in tags:
                    tags_string = (newtag + DELIM) + tags_string

                yield (url, title, delim_wrap(tags_string), None, 0, True, False)

def import_firefox_json(json, add_bookmark_folder_as_tag=False, unique_tag=None):
    """Open Firefox JSON export file and import data.
    Ignore 'SmartBookmark'  and 'Separator'  entries.

    Needed/used fields out of the JSON schema of the bookmarks:

    title              : the name/title of the entry
    tags               : ',' separated tags for the bookmark entry
    typeCode           : 1 - uri, 2 - subfolder, 3 - separator
    annos/{name,value} : following annotation entries are used
        name : Places/SmartBookmark            : identifies smart folder, ignored
        name : bookmarkPropereties/description :  detailed bookmark entry description
    children           : for subfolders, recurse into the child entries

    Parameters
    ----------
    path : str
        Path to Firefox JSON bookmarks file.
    unique_tag : str
        Timestamp tag in YYYYMonDD format.
    add_bookmark_folder_as_tag : bool
        True if bookmark parent folder should be added as tags else False.
    """

    class TypeCode(Enum):
        """ Format
            typeCode
                1 : uri        (type=text/x-moz-place)
                2 : subfolder  (type=text/x-moz-container)
                3 : separator  (type=text/x-moz-separator)
        """
        uri = 1
        folder = 2
        separator = 3

    def is_smart(entry):
        result = False
        try:
            d = [anno for anno in entry['annos'] if anno['name'] == "Places/SmartBookmark"]
            result = bool(len(d))
        except Exception:
            result = False

        return result

    def extract_desc(entry):
        try:
            d = [
                anno for anno in entry['annos']
                if anno['name'] == "bookmarkProperties/description"
            ]
            return d[0]['value']
        except Exception:
            LOGDBG("ff_json: No description found for entry: {} {}".format(entry['uri'], entry['title']))
            return ""

    def extract_tags(entry):
        tags = []
        try:
            tags = entry['tags'].split(',')
        except Exception:
            LOGDBG("ff_json: No tags found for entry: {} {}".format(entry['uri'], entry['title']))

        return tags

    def iterate_children(parent_folder, entry_list):
        for bm_entry in entry_list:
            entry_title = bm_entry['title'] if 'title' in bm_entry else "<no title>"

            try:
                typeCode = bm_entry['typeCode']
            except Exception:
                LOGDBG("ff_json: item without typeCode found, ignoring: {}".format(entry_title))
                continue

            LOGDBG("ff_json: processing typeCode '{}', title '{}'".format(typeCode, entry_title))
            if TypeCode.uri.value == typeCode:
                try:
                    if is_smart(bm_entry):
                        LOGDBG("ff_json: SmartBookmark found, ignoring: {}".format(entry_title))
                        continue

                    if is_nongeneric_url(bm_entry['uri']):
                        LOGDBG("ff_json: Non-Generic URL found, ignoring: {}".format(entry_title))
                        continue

                    desc = extract_desc(bm_entry)
                    bookmark_tags = extract_tags(bm_entry)

                    # if parent_folder is not "None"
                    if add_bookmark_folder_as_tag and parent_folder:
                        bookmark_tags.append(parent_folder)

                    if unique_tag:
                        bookmark_tags.append(unique_tag)

                    formatted_tags = [DELIM + tag for tag in bookmark_tags]
                    tags = parse_tags(formatted_tags)

                    LOGDBG("ff_json: Entry found: {}, {}, {}, {} " .format(bm_entry['uri'], entry_title, tags, desc))
                    yield (bm_entry['uri'], entry_title, tags, desc, 0, True, False)

                except Exception as e:
                    LOGERR("ff_json: Error parsing entry '{}' Exception '{}'".format(entry_title, e))

            elif TypeCode.folder.value == typeCode:

                # ignore special bookmark folders
                if 'root' in bm_entry and bm_entry['root'] in IGNORE_FF_BOOKMARK_FOLDERS:
                    LOGDBG("ff_json: ignoring root folder: {}" .format(entry_title))
                    entry_title = None

                if "children" in bm_entry:
                    yield from iterate_children(entry_title, bm_entry['children'])
                else:
                    # if any of the properties does not exist, bail out silently
                    LOGDBG("ff_json: No 'children' found in bookmark folder - skipping: {}".format(entry_title))

            elif TypeCode.separator.value == typeCode:
                # ignore separator
                pass
            else:
                LOGDBG("ff_json: Unknown typeCode found : {}".format(typeCode))

    if "children" in json:
        main_entry_list = json['children']
    else:
        LOGDBG("ff_json: No children in Root entry found")
        return []

    yield from iterate_children(None, main_entry_list)

def import_xbel(html_soup: BeautifulSoup, add_parent_folder_as_tag: bool, newtag: str, use_nested_folder_structure: bool = False):
    """Parse bookmark XBEL.

    Parameters
    ----------
    html_soup : BeautifulSoup object
        BeautifulSoup representation of bookmark HTML.
    add_parent_folder_as_tag : bool
        True if bookmark parent folders should be added as tags else False.
    newtag : str
        A new unique tag to add to imported bookmarks.
    use_nested_folder_structure: bool
        True if all bookmark parent folder should be added, not just direct parent else False
        add_parent_folder_as_tag must be True for this flag to have an effect

    Returns
    -------
    tuple
        Parsed result.
    """

    # compatibility
    soup = html_soup

    for tag in soup.find_all('bookmark'):
        # Extract comment from <desc> tag
        try:
            if is_nongeneric_url(tag['href']):
                continue
        except KeyError:
            continue

        title_tag = tag.title.string

        desc = None
        comment_tag = tag.find_next_sibling('desc')

        if comment_tag:
            desc = comment_tag.find(text=True, recursive=False)

        if add_parent_folder_as_tag:
            # add parent folder as tag
            if use_nested_folder_structure:
                # New method that would generalize for else case to
                # structure of folders
                # folder
                #   title (folder name)
                #   folder
                #       title
                #           bookmark (could be h3, and continue recursively)
                parents = tag.find_parents('folder')
                for parent in parents:
                    header = parent.find_previous_sibling('title')
                    if header:
                        if tag.has_attr('tags'):
                            tag['tags'] += (DELIM + header.text)
                        else:
                            tag['tags'] = header.text
            else:
                # could be its folder or not
                possible_folder = tag.find_previous('title')
                # get list of tags within that folder
                tag_list = tag.parent.parent.find_parent('folder')

                if ((possible_folder) and possible_folder.parent in list(tag_list.parents)):
                    # then it's the folder of this bookmark
                    if tag.has_attr('tags'):
                        tag['tags'] += (DELIM + possible_folder.text)
                    else:
                        tag['tags'] = possible_folder.text

        # add unique tag if opted
        if newtag:
            if tag.has_attr('tags'):
                tag['tags'] += (DELIM + newtag)
            else:
                tag['tags'] = newtag

        yield (
            tag['href'], title_tag,
            parse_tags([tag['tags']]) if tag.has_attr('tags') else None,
            desc if not desc else desc.strip(), 0, True, False
        )

def import_html(html_soup: BeautifulSoup, add_parent_folder_as_tag: bool, newtag: str, use_nested_folder_structure: bool = False):
    """Parse bookmark HTML.

    Parameters
    ----------
    html_soup : BeautifulSoup object
        BeautifulSoup representation of bookmark HTML.
    add_parent_folder_as_tag : bool
        True if bookmark parent folders should be added as tags else False.
    newtag : str
        A new unique tag to add to imported bookmarks.
    use_nested_folder_structure: bool
        True if all bookmark parent folder should be added, not just direct parent else False
        add_parent_folder_as_tag must be True for this flag to have an effect

    Returns
    -------
    tuple
        Parsed result.
    """

    # compatibility
    soup = html_soup

    for tag in soup.find_all('a'):
        # Extract comment from <dd> tag
        try:
            if is_nongeneric_url(tag['href']):
                continue
        except KeyError:
            continue

        desc = None
        comment_tag = tag.find_next_sibling('dd')

        if comment_tag:
            desc = comment_tag.find(string=True, recursive=False)

        if add_parent_folder_as_tag:
            # New method that would generalize for else case to
            # structure of folders
            # dt
            #   h3 (folder name)
            #   dl
            #       dt
            #           a (could be h3, and continue recursively)
            parents = tag.find_parents('dl')
            for parent in (parents if use_nested_folder_structure else parents[:1]):
                header = parent.find_previous_sibling('h3')
                if header:
                    if tag.has_attr('tags'):
                        tag['tags'] += (DELIM + strip_delim(header.text))
                    else:
                        tag['tags'] = strip_delim(header.text)

        # add unique tag if opted
        if newtag:
            if tag.has_attr('tags'):
                tag['tags'] += (DELIM + strip_delim(newtag))
            else:
                tag['tags'] = strip_delim(newtag)

        yield (
            tag['href'], tag.string,
            parse_tags([tag['tags']]) if tag.has_attr('tags') else None,
            desc if not desc else desc.strip(), 0, True, False
        )


def get_netloc(url):
    """Get the netloc token, or None."""

    try:
        netloc = urlparse(url).netloc
        if not netloc and not urlparse(url).scheme:
            # Try to prepend '//' and get netloc
            netloc = urlparse('//' + url).netloc
        return netloc or None
    except Exception as e:
        LOGERR('%s, URL: %s', e, url)
        return None


def is_bad_url(url):
    """Check if URL is malformed.

    .. Note:: This API is not bulletproof but works in most cases.

    Parameters
    ----------
    url : str
        URL to scan.

    Returns
    -------
    bool
        True if URL is malformed, False otherwise.
    """

    netloc = get_netloc(url)
    if not netloc:
        return True

    LOGDBG('netloc: %s', netloc)

    # netloc cannot start or end with a '.'
    if netloc.startswith('.') or netloc.endswith('.'):
        return True

    # netloc should have at least one '.'
    return '.' not in netloc


def is_nongeneric_url(url):
    """Returns True for URLs which are non-http and non-generic.

    Parameters
    ----------
    url : str
        URL to scan.

    Returns
    -------
    bool
        True if URL is a non-generic URL, False otherwise.
    """

    ignored_prefix = [
        'about:',
        'apt:',
        'chrome://',
        'file://',
        'place:',
        'vivaldi://',
    ]

    for prefix in ignored_prefix:
        if url.startswith(prefix):
            return True

    return False


def is_ignored_mime(url):
    """Check if URL links to ignored MIME.

    .. Note:: Only a 'HEAD' request is made for these URLs.

    Parameters
    ----------
    url : str
        URL to scan.

    Returns
    -------
    bool
        True if URL links to ignored MIME, False otherwise.
    """

    for mime in SKIP_MIMES:
        if url.lower().endswith(mime):
            LOGDBG('matched MIME: %s', mime)
            return True

    return False


def is_unusual_tag(tagstr):
    """Identify unusual tags with word to comma ratio > 3.

    Parameters
    ----------
    tagstr : str
        tag string to check.

    Returns
    -------
    bool
        True if valid tag else False.
    """

    if not tagstr:
        return False

    nwords = len(tagstr.split())
    ncommas = tagstr.count(',') + 1

    if nwords / ncommas > 3:
        return True

    return False


def parse_decoded_page(page):
    """Fetch title, description and keywords from decoded HTML page.

    Parameters
    ----------
    page : str
        Decoded HTML page.

    Returns
    -------
    tuple
        (title, description, keywords).
    """

    title = ''
    desc = ''
    keys = ''

    soup = BeautifulSoup(page, 'html5lib')

    try:
        title = soup.find('title').text.strip().replace('\n', ' ')
        if title:
            title = re.sub(r'\s{2,}', ' ', title)
    except Exception as e:
        LOGDBG(e)

    description = (soup.find('meta', attrs={'name':'description'}) or
                   soup.find('meta', attrs={'name':'Description'}) or
                   soup.find('meta', attrs={'property':'description'}) or
                   soup.find('meta', attrs={'property':'Description'}) or
                   soup.find('meta', attrs={'name':'og:description'}) or
                   soup.find('meta', attrs={'name':'og:Description'}) or
                   soup.find('meta', attrs={'property':'og:description'}) or
                   soup.find('meta', attrs={'property':'og:Description'}))
    try:
        if description:
            desc = description.get('content').strip()
            if desc:
                desc = re.sub(r'\s{2,}', ' ', desc)
    except Exception as e:
        LOGDBG(e)

    keywords = (soup.find('meta', attrs={'name':'keywords'}) or
                soup.find('meta', attrs={'name':'Keywords'}))
    try:
        if keywords:
            keys = keywords.get('content').strip().replace('\n', ' ')
            keys = re.sub(r'\s{2,}', ' ', re.sub(r'\s*,\s*', ',', keys))
            if is_unusual_tag(keys):
                if keys not in (title, desc):
                    LOGDBG('keywords to description: %s', keys)
                    if desc:
                        desc = desc + '\n## ' + keys
                    else:
                        desc = '* ' + keys

                keys = ''
    except Exception as e:
        LOGDBG(e)

    LOGDBG('title: %s', title)
    LOGDBG('desc : %s', desc)
    LOGDBG('keys : %s', keys)

    return (title, desc, keys and keys.strip(DELIM))


def get_data_from_page(resp):
    """Detect HTTP response encoding and invoke parser with decoded data.

    Parameters
    ----------
    resp : HTTP response
        Response from GET request.

    Returns
    -------
    tuple
        (title, description, keywords).
    """

    try:
        charset = EncodingDetector.find_declared_encoding(resp.data, is_html=True)

        if not charset and 'content-type' in resp.headers:
            m = email.message.Message()
            m['content-type'] = resp.headers['content-type']
            if m.get_param('charset') is not None:
                charset = m.get_param('charset')

        if charset:
            LOGDBG('charset: %s', charset)
            title, desc, keywords = parse_decoded_page(resp.data.decode(charset, errors='replace'))
        else:
            title, desc, keywords = parse_decoded_page(resp.data.decode(errors='replace'))

        return (title, desc, keywords)
    except Exception as e:
        LOGERR(e)
        return (None, None, None)


def extract_auth(url):
    """Convert an url into an (auth, url) tuple [the returned URL will contain no auth part]."""
    _url = urlparse(url)
    if _url.username is None:  # no '@' in netloc
        return None, url
    auth = _url.username + ('' if _url.password is None else f':{_url.password}')
    return auth, url.replace(auth + '@', '')

def gen_headers():
    """Generate headers for network connection."""

    global MYHEADERS, MYPROXY

    MYHEADERS = {
        'Accept-Encoding': 'gzip,deflate',
        'User-Agent': USER_AGENT,
        'Accept': '*/*',
        'Cookie': '',
        'DNT': '1'
    }

    MYPROXY = os.environ.get('https_proxy')
    if MYPROXY:
        try:
            auth, MYPROXY = extract_auth(MYPROXY)
        except Exception as e:
            LOGERR(e)
            return

        # Strip username and password (if present) and update headers
        if auth:
            auth_headers = make_headers(basic_auth=auth)
            MYHEADERS.update(auth_headers)

        LOGDBG('proxy: [%s]', MYPROXY)


def get_PoolManager():
    """Creates a pool manager with proxy support, if applicable.

    Returns
    -------
    ProxyManager or PoolManager
        ProxyManager if https_proxy is defined, PoolManager otherwise.
    """
    ca_certs = os.getenv('BUKU_CA_CERTS', default=CA_CERTS)
    if MYPROXY:
        return urllib3.ProxyManager(MYPROXY, num_pools=1, headers=MYHEADERS, timeout=15,
                                    cert_reqs='CERT_REQUIRED', ca_certs=ca_certs)

    return urllib3.PoolManager(
        num_pools=1,
        headers=MYHEADERS,
        timeout=15,
        cert_reqs='CERT_REQUIRED',
        ca_certs=ca_certs)


def network_handler(
        url: str,
        http_head: bool = False
) -> Tuple[str, str, str, int, int]:
    """Handle server connection and redirections.

    Deprecated; use fetch_data() instead.

    Returns
    -------
    tuple
        (title, description, tags, recognized mime, bad url)
    """
    warn('\'buku.network_handler()\' is deprecated; use \'buku.fetch_data()\' instead.', DeprecationWarning)
    result = fetch_data(url, http_head)
    return (result.title, result.desc, result.keywords, int(result.mime), int(result.bad))


def fetch_data(
        url: str,
        http_head: bool = False
) -> FetchResult:
    """Handle server connection and redirections.

    Parameters
    ----------
    url : str
        URL to fetch.
    http_head : bool
        If True, send only HTTP HEAD request. Default is False.

    Returns
    -------
    FetchResult
        (url, title, desc, keywords, mime, bad, fetch_status)
    """

    page_status = None
    page_url = url
    page_title = ''
    page_desc = ''
    page_keys = ''
    exception = False

    if is_nongeneric_url(url) or is_bad_url(url):
        return FetchResult(url, bad=True)

    if is_ignored_mime(url) or http_head:
        method = 'HEAD'
    else:
        method = 'GET'

    if not MYHEADERS:
        gen_headers()

    try:
        manager = get_PoolManager()

        while True:
            resp = manager.request(method, url, retries=Retry(redirect=10))
            page_status = resp.status

            if resp.status == 200:
                if method == 'GET':
                    for retry in resp.retries.history:
                        if retry.status not in PERMANENT_REDIRECTS:
                            break
                        page_status, page_url = retry.status, retry.redirect_location
                    page_title, page_desc, page_keys = get_data_from_page(resp)
            elif resp.status == 403 and url.endswith('/'):
                # HTTP response Forbidden
                # Handle URLs in the form of https://www.domain.com/
                # which fail when trying to fetch resource '/'
                # retry without trailing '/'

                LOGDBG('Received status 403: retrying...')
                # Remove trailing /
                url = url[:-1]
                resp.close()
                continue
            else:
                page_title, page_desc, page_keys = get_data_from_page(resp)
                LOGERR('[%s] %s', resp.status, resp.reason)

            if resp:
                resp.close()

            break
    except Exception as e:
        LOGERR('fetch_data(): %s', e)
        exception = True

    if manager:
        manager.clear()
    if exception:
        return FetchResult(url)
    if method == 'HEAD':
        return FetchResult(url, mime=True, fetch_status=page_status)

    return FetchResult(page_url, title=page_title, desc=page_desc, keywords=page_keys, fetch_status=page_status)


def parse_tags(keywords=[], *, edit_input=False):
    """Format and get tag string from tokens.

    Parameters
    ----------
    keywords : list
        List of tags to parse. Default is empty list.
    edit_input : bool
        Whether the taglist is an edit input (i.e. may start with '+'/'-').
        Defaults to False.

    Returns
    -------
    str
        Comma-delimited string of tags.
    DELIM : str
        If no keywords, returns the delimiter.
    None
        If keywords is None.
    """

    if keywords is None:
        return None

    tagstr = ' '.join(s for s in keywords if s)
    if not tagstr:
        return DELIM

    if edit_input and keywords[0] in ('+', '-'):
        return keywords[0] + parse_tags(keywords[1:])

    # Cleanse and get the tags
    marker = tagstr.find(DELIM)
    tags = DELIM

    while marker >= 0:
        token = tagstr[0:marker]
        tagstr = tagstr[marker + 1:]
        marker = tagstr.find(DELIM)
        token = token.strip()
        if token == '':
            continue

        tags += token + DELIM

    tagstr = tagstr.strip()
    if tagstr != '':
        tags += tagstr + DELIM

    LOGDBG('keywords: %s', keywords)
    LOGDBG('parsed tags: [%s]', tags)

    if tags == DELIM:
        return tags

    # sorted unique tags in lowercase, wrapped with delimiter
    return taglist_str(tags)


def prep_tag_search(tags: str) -> Tuple[List[str], Optional[str], Optional[str]]:
    """Prepare list of tags to search and determine search operator.

    Parameters
    ----------
    tags : str
        String list of tags to search.

    Returns
    -------
    tuple
        (list of formatted tags to search,
         a string indicating query search operator (either OR or AND),
         a regex string of tags or None if ' - ' delimiter not in tags).
    """

    exclude_only = False

    # tags may begin with `- ` if only exclusion list is provided
    if tags.startswith('- '):
        tags = ' ' + tags
        exclude_only = True

    # tags may start with `+ ` etc., tricky test case
    if tags.startswith(('+ ', ', ')):
        tags = tags[2:]

    # tags may end with ` -` etc., tricky test case
    if tags.endswith((' -', ' +', ' ,')):
        tags = tags[:-2]

    # tag exclusion list can be separated by comma (,), so split it first
    excluded_tags = None
    if ' - ' in tags:
        tags, excluded_tags = tags.split(' - ', 1)

        excluded_taglist = [delim_wrap(re.escape(t.strip())) for t in excluded_tags.split(',')]
        # join with pipe to construct regex string
        excluded_tags = '|'.join(excluded_taglist)

    if exclude_only:
        search_operator = 'OR'
        tags_ = ['']
    else:
        # do not allow combination of search logics in tag inclusion list
        if ' + ' in tags and ',' in tags:
            return [], None, None

        search_operator = 'OR'
        tag_delim = ','
        if ' + ' in tags:
            search_operator = 'AND'
            tag_delim = ' + '

        tags_ = [delim_wrap(t.strip()) for t in tags.split(tag_delim)]

    return tags_, search_operator, excluded_tags


def gen_auto_tag():
    """Generate a tag in Year-Month-Date format.

    Returns
    -------
    str
        New tag as YYYYMonDD.
    """

    t = time.localtime()
    return '%d%s%02d' % (t.tm_year, calendar.month_abbr[t.tm_mon], t.tm_mday)


def edit_at_prompt(obj, nav, suggest=False):
    """Edit and add or update a bookmark.

    Parameters
    ----------
    obj : BukuDb instance
        A valid instance of BukuDb class.
    nav : str
        Navigation command argument passed at prompt by user.
    suggest : bool
        If True, suggest similar tags on new bookmark addition.
    """

    if nav == 'w':
        editor = get_system_editor()
        if not is_editor_valid(editor):
            return
    elif is_int(nav[2:]):
        obj.edit_update_rec(int(nav[2:]))
        return
    else:
        editor = nav[2:]

    result = edit_rec(editor, '', None, DELIM, None)
    if result is not None:
        url, title, tags, desc = result
        if suggest:
            tags = obj.suggest_similar_tag(tags)
        obj.add_rec(url, title, tags, desc)


def show_taglist(obj):
    """Additional prompt to show unique tag list.

    Parameters
    ----------
    obj : BukuDb instance
        A valid instance of BukuDb class.
    """

    unique_tags, dic = obj.get_tag_all()
    if not unique_tags:
        count = 0
        print('0 tags')
    else:
        count = 1
        for tag in unique_tags:
            print('%6d. %s (%d)' % (count, tag, dic[tag]))
            count += 1
        print()


def prompt(obj, results, noninteractive=False, deep=False, listtags=False, suggest=False, num=10, markers=False, order=['+id']):
    """Show each matching result from a search and prompt.

    Parameters
    ----------
    obj : BukuDb instance
        A valid instance of BukuDb class.
    results : list
        Search result set from a DB query.
    noninteractive : bool
        If True, does not seek user input. Shows all results. Default is False.
    deep : bool
        Use deep search. Default is False.
    markers : bool
        Use search-with-markers. Default is False.
    listtags : bool
        If True, list all tags.
    suggest : bool
        If True, suggest similar tags on edit and add bookmark.
    order : list of str
        Order description (fields from JSON export or DB, prepended with '+'/'-' for ASC/DESC).
    num : int
        Number of results to show per page. Default is 10.
    """

    if not isinstance(obj, BukuDb):
        LOGERR('Not a BukuDb instance')
        return
    bdb = obj

    new_results = bool(results)
    nav = ''
    cur_index = next_index = prev_index = 0

    if listtags:
        show_taglist(obj)

    try:
        columns, _ = os.get_terminal_size()
    except OSError:
        columns = 0

    if noninteractive:
        try:
            for i, row in enumerate(results):
                print_single_rec(row, i + 1, columns)
        except Exception as e:
            LOGERR(e)
        return

    skip_print = False
    while True:
        if (new_results or nav in ['n', 'N']) and not skip_print:
            _total_results = len(results or [])
            cur_index = next_index              # used elsewhere as "most recent page start index"
            if not results:
                print('0 results')
                new_results = False
            elif cur_index >= _total_results and nav != 'N':
                print('No more results')
                new_results = False
            else:
                if nav == 'N':
                    cur_index = min(cur_index, prev_index)
                prev_index = max(0, cur_index - num)
                next_index = min(cur_index + num, _total_results)
                print()
                for i in range(cur_index, next_index):
                    print_single_rec(results[i], i + 1, columns)
                print('%d-%d/%d' % (cur_index + 1, next_index, _total_results))
        skip_print = False

        try:
            prompt_suffix = ''
            if bdb.dbfile != os.path.realpath(os.path.join(BukuDb.get_default_dbdir(), 'bookmarks.db')):
                prompt_suffix = (f'[{bdb.dbname}] ' if not bdb.colorize else
                                 f'\001\x1b[7\002m[{bdb.dbname}]\001\x1b[0m\002 ')
            nav = read_in(PROMPTMSG + prompt_suffix)
            if not nav:
                nav = read_in(PROMPTMSG + prompt_suffix)
                if not nav:
                    # Quit on double enter
                    break
            nav = nav.strip()
        except EOFError:
            return

        # show the next set of results from previous search
        if nav in ('n', 'N'):
            continue

        if (m := re.match(r'^R(?: (-)?([0-9]+))?$', nav.rstrip())) and (n := int(m[2] or 1)) > 0:
            skip_print = True
            if results and not m[1]:  # from search results
                picked = random.sample(results, min(n, len(results)))
            else:                     # from all bookmarks
                ids = range(1, 1 + (bdb.get_max_id() or 0))
                picked = bdb.get_rec_all_by_ids(random.sample(ids, min(n, len(ids))))
            for row in bdb._sort(picked, order):
                print_single_rec(row, columns=columns)
            continue

        if (m := re.match(r'^\^ ([1-9][0-9]*) ([1-9][0-9]*)$', nav.rstrip())):
            index1, index2 = map(int, m.group(1, 2))
            if bdb.swap_recs(index1, index2):
                bdb.print_rec({index1, index2})
            else:
                print('Failed to swap records #%d and #%d' % (index1, index2))
            continue

        # search ANY match with new keywords
        if nav.startswith('s '):
            keywords = (nav[2:].split() if not markers else split_by_marker(nav[2:]))
            results = bdb.searchdb(keywords, deep=deep, markers=markers, order=order)
            new_results = True
            cur_index = next_index = 0
            continue

        # search ALL match with new keywords
        if nav.startswith('S '):
            keywords = (nav[2:].split() if not markers else split_by_marker(nav[2:]))
            results = bdb.searchdb(keywords, all_keywords=True, deep=deep, markers=markers, order=order)
            new_results = True
            cur_index = next_index = 0
            continue

        # regular expressions search with new keywords
        if nav.startswith('r '):
            keywords = (nav[2:].split() if not markers else split_by_marker(nav[2:]))
            results = bdb.searchdb(keywords, all_keywords=True, regex=True, markers=markers, order=order)
            new_results = True
            cur_index = next_index = 0
            continue

        # tag search with new keywords
        if nav.startswith('t '):
            results = bdb.search_by_tag(nav[2:], order=order)
            new_results = True
            cur_index = next_index = 0
            continue

        # quit with 'q'
        if nav == 'q':
            return

        # No new results fetched beyond this point
        new_results = False

        # toggle deep search with 'd', search-with-markers with 'm'
        if nav == 'd':
            deep = not deep
            print('deep search', ('on' if deep else 'off'))
            continue
        if nav == 'm':
            markers = not markers
            print('search-with-markers', ('on' if markers else 'off'))
            continue

        if nav.startswith('v '):  # letters 's' and 'o' are taken already
            _fields = {'metadata': 'title', **JSON_FIELDS}
            _order = bdb._ordering(filter(None, re.split(r'[,\s]+', nav[2:].strip())))
            order = [('+' if asc else '-') + _fields.get(s, s) for s, asc in _order]
            print('order', ', '.join(order))
            continue

        # Toggle GUI browser with 'O'
        if nav == 'O':
            browse.override_text_browser = not browse.override_text_browser
            print('text browser override toggled')
            continue

        # Show help with '?'
        if nav == '?':
            ExtendedArgumentParser.prompt_help(sys.stdout)
            continue

        # Edit and add or update
        if nav == 'w' or nav.startswith('w '):
            edit_at_prompt(bdb, nav, suggest)
            continue

        # Append or overwrite tags
        if nav.startswith('g '):
            unique_tags, dic = obj.get_tag_all()
            _count = bdb.set_tag(nav[2:], unique_tags)
            if _count == -1:
                print('Invalid input')
            elif _count == -2:
                try:
                    tagid_list = nav[2:].split()
                    tagstr = bdb.get_tagstr_from_taglist(tagid_list, unique_tags)
                    tagstr = tagstr.strip(DELIM)
                    results = bdb.search_by_tag(tagstr)
                    new_results = True
                    cur_index = next_index = 0
                except Exception:
                    print('Invalid input')
            else:
                print('%d updated' % _count)
            continue

        # Print bookmarks by DB index
        if nav.startswith('p '):
            try:
                ids = parse_range(nav[2:].split(), maxidx=bdb.get_max_id() or 0)
                ids and bdb.print_rec(ids, order=order)
            except ValueError:
                print('Invalid input')
            continue

        # Browse bookmarks by DB index
        if nav.startswith('o '):
            id_list = nav[2:].split()
            try:
                for id in id_list:
                    if is_int(id):
                        bdb.browse_by_index(int(id))
                    elif '-' in id:
                        vals = [int(x) for x in id.split('-')]
                        bdb.browse_by_index(0, vals[0], vals[-1], True)
                    else:
                        print('Invalid input')
            except ValueError:
                print('Invalid input')
            continue

        # Copy URL to clipboard
        if nav.startswith('c ') and nav[2:].isdigit():
            index = int(nav[2:]) - 1
            if index < 0 or index >= next_index:
                print('No matching index')
                continue
            copy_to_clipboard(content=results[index + cur_index][1].encode('utf-8'))
            continue

        # open all results and re-prompt with 'a'
        if nav == 'a':
            for index in range(cur_index, next_index):
                browse(results[index][1])
            continue

        # list tags with 't'
        if nav == 't':
            show_taglist(bdb)
            continue

        if (nav+' ').startswith('DB '):
            dbpath, dbfile = os.path.split(bdb.dbfile)
            if nav == 'DB':
                print(f'Available DB files (in {dbpath}):')
                for s in sorted(s for s in os.listdir(dbpath) if s.endswith('.db')):
                    print(('*' if s == dbfile else ' '), s.removesuffix('.db'))
            else:
                s = os.path.expanduser(re.sub(r'^DB\s+', '', nav))
                path = os.path.join(dbpath, (s if s != '~.' else BukuDb.get_default_dbdir()))  # relative to current dir
                newpath, newfile = os.path.split(path+'/' if os.path.isdir(path) else path)
                newfile, (_, ext) = newfile or 'bookmarks', os.path.splitext(newfile)
                if not ext or os.path.isfile(os.path.join(newpath, newfile+'.db')):
                    newfile += '.db'
                newdb = os.path.join(newpath, newfile)
                try:
                    if not os.path.exists(newdb):
                        print(f'DB file is being created at {newdb}')
                    _bdb = bdb
                    bdb = BukuDb(json=bdb.json, field_filter=bdb.field_filter, colorize=bdb.colorize, dbfile=newdb)
                    _bdb.close()
                    results, new_results = [], False
                    cur_index = next_index = prev_index = 0
                    print(f'Loaded DB file at {bdb.dbfile}')
                except Exception:
                    print(f'Failed to open DB file at {newdb}')
            continue

        toggled = False
        # Open in GUI browser
        if nav.startswith('O '):
            if not browse.override_text_browser:
                browse.override_text_browser = True
                toggled = True
            nav = nav[2:]

        # iterate over white-space separated indices
        for nav in nav.split():
            if is_int(nav):
                index = int(nav) - 1
                if index < 0 or index >= next_index:
                    print('No matching index %s' % nav)
                    continue
                browse(results[index][1])
            elif '-' in nav:
                try:
                    vals = [int(x) for x in nav.split('-')]
                    if vals[0] > vals[-1]:
                        vals[0], vals[-1] = vals[-1], vals[0]

                    for _id in range(vals[0]-1, vals[-1]):
                        if 0 <= _id < next_index:
                            browse(results[_id][1])
                        else:
                            print('No matching index %d' % (_id + 1))
                except ValueError:
                    print('Invalid input')
                    break
            else:
                print('Invalid input')
                break

        if toggled:
            browse.override_text_browser = False


def copy_to_clipboard(content):
    """Copy content to clipboard

    Parameters
    ----------
    content : str
        Content to be copied to clipboard
    """

    # try copying the url to clipboard using native utilities
    copier_params = []
    if sys.platform.startswith(('linux', 'freebsd', 'openbsd')):
        if shutil.which('xsel') is not None:
            copier_params = ['xsel', '-b', '-i']
        elif shutil.which('xclip') is not None:
            copier_params = ['xclip', '-selection', 'clipboard']
        elif shutil.which('wl-copy') is not None:
            copier_params = ['wl-copy']
        # If we're using Termux (Android) use its 'termux-api'
        # add-on to set device clipboard.
        elif shutil.which('termux-clipboard-set') is not None:
            copier_params = ['termux-clipboard-set']
    elif sys.platform == 'darwin':
        copier_params = ['pbcopy']
    elif sys.platform == 'win32':
        copier_params = ['clip']

    if copier_params:
        Popen(copier_params, stdin=PIPE, stdout=DEVNULL, stderr=DEVNULL).communicate(content)
        return

    # If native clipboard utilities are absent, try to use terminal multiplexers
    # tmux
    if os.getenv('TMUX_PANE'):
        copier_params = ['tmux', 'set-buffer']
        Popen(
            copier_params + [content],
            stdin=DEVNULL,
            stdout=DEVNULL,
            stderr=DEVNULL
        ).communicate()
        print('URL copied to tmux buffer.')
        return

    # GNU Screen paste buffer
    if os.getenv('STY'):
        copier_params = ['screen', '-X', 'readbuf', '-e', 'utf8']
        tmpfd, tmppath = tempfile.mkstemp()
        try:
            with os.fdopen(tmpfd, 'wb') as fp:
                fp.write(content)
            copier_params.append(tmppath)
            Popen(copier_params, stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL).communicate()
        finally:
            os.unlink(tmppath)
        return

    print('Failed to locate suitable clipboard utility')
    return


def print_rec_with_filter(records, field_filter=0):
    """Print records filtered by field.

    User determines which fields in the records to display
    by using the --format option.

    Parameters
    ----------
    records : list or sqlite3.Cursor object
        List of bookmark records to print
    field_filter : int
        Integer indicating which fields to print. Default is 0 ("all fields").
    """

    try:
        records = bookmark_vars(records)
        fields = FIELD_FILTER.get(field_filter)
        if fields:
            pattern = '\t'.join('%s' for k in fields)
            for row in records:
                print(pattern % tuple(getattr(row, k) for k in fields))
        else:
            try:
                columns, _ = os.get_terminal_size()
            except OSError:
                columns = 0
            for row in records:
                print_single_rec(row, columns=columns)
    except BrokenPipeError:
        sys.stdout = os.fdopen(1)
        sys.exit(1)


def print_single_rec(row: BookmarkVar, idx: int=0, columns: int=0):  # NOQA
    """Print a single DB record.

    Handles both search results and individual record.

    Parameters
    ----------
    row : tuple
        Tuple representing bookmark record data.
    idx : int
        Search result index. If 0, print with DB index.
        Default is 0.
    columns : int
        Number of columns to wrap comments to.
        Default is 0.
    """

    str_list = []
    row = BookmarkVar(*row)  # ensuring named tuple

    # Start with index and title
    if idx != 0:
        id_title_res = ID_STR % (idx, row.title or 'Untitled', row.id)
    else:
        id_title_res = ID_DB_STR % (row.id, row.title or 'Untitled')
        # Indicate if record is immutable
        if row.immutable:
            id_title_res = MUTE_STR % (id_title_res,)
        else:
            id_title_res += '\n'

    try:
        print(id_title_res, end='')
        print(URL_STR % (row.url,), end='')
        if columns == 0:
            if row.desc:
                print(DESC_STR % (row.desc,), end='')
            if row.tags:
                print(TAG_STR % (row.tags,), end='')
            print()
            return

        INDENT = 5
        fillwidth = columns - INDENT
        desc_lines = [s for line in row.desc.splitlines()
                        for s in textwrap.wrap(line, width=fillwidth) or ['']]
        TR = str.maketrans(',-', '-,')  # we want breaks after commas rather than hyphens
        tag_lines = textwrap.wrap(row.tags.translate(TR), width=fillwidth)

        for idx, line in enumerate(desc_lines):
            if idx == 0:
                print(DESC_STR % line, end='')
            else:
                print(DESC_WRAP % (' ' * INDENT, line))

        for idx, line in enumerate(tag_lines):
            if idx == 0:
                print(TAG_STR % line.translate(TR), end='')
            else:
                print(TAG_WRAP % (' ' * INDENT, line.translate(TR)))
        print()
    except UnicodeEncodeError:
        str_list = []
        str_list.append(id_title_res)
        str_list.append(URL_STR % (row.url,))
        if row.desc:
            str_list.append(DESC_STR % (row.desc,))
        if row.tags:
            str_list.append(TAG_STR % (row.tags,))
        sys.stdout.buffer.write((''.join(str_list) + '\n').encode('utf-8'))
    except BrokenPipeError:
        sys.stdout = os.fdopen(1)
        sys.exit(1)


def write_string_to_file(content: str, filepath: str):
    """Writes given content to file

    Parameters
    ----------
    content : str
    filepath : str

    Returns
    -------
    None
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        LOGERR(e)


def format_json(resultset, single_record=False, field_filter=0):
    """Return results in JSON format.

    Parameters
    ----------
    resultset : list
        Search results from DB query.
    single_record : bool
        If True, indicates only one record. Default is False.
    field_filter : int
        Indicates format for displaying bookmarks. Default is 0 ("all fields").

    Returns
    -------
    json
        Record(s) in JSON format.
    """

    resultset = bookmark_vars(resultset)
    fields = [(k, JSON_FIELDS.get(k, k)) for k in FIELD_FILTER.get(field_filter, ALL_FIELDS)]
    marks = [{field: getattr(row, k) for k, field in fields} for row in resultset]
    if single_record:
        marks = marks[-1] if marks else {}

    return json.dumps(marks, sort_keys=True, indent=4)


def print_json_safe(resultset, single_record=False, field_filter=0):
    """Prints json results and handles IOError

    Parameters
    ----------
    resultset : list
        Search results from DB query.
    single_record : bool
        If True, indicates only one record. Default is False.
    field_filter : int
        Indicates format for displaying bookmarks. Default is 0 ("all fields").

    Returns
    -------
    None
    """

    try:
        print(format_json(resultset, single_record, field_filter))
    except IOError:
        try:
            sys.stdout.close()
        except IOError:
            pass
        try:
            sys.stderr.close()
        except IOError:
            pass


def is_int(string):
    """Check if a string is a digit.

    string : str
        Input string to check.

    Returns
    -------
    bool
        True on success, False on exception.
    """

    try:
        int(string)
        return True
    except Exception:
        return False


def browse(url):
    """Duplicate stdin, stdout and open URL in default browser.

    .. Note:: Duplicates stdin and stdout in order to
              suppress showing errors on the terminal.

    Parameters
    ----------
    url : str
        URL to open in browser.

    Attributes
    ----------
    suppress_browser_output : bool
        True if a text based browser is detected.
        Must be initialized (as applicable) to use the API.
    override_text_browser : bool
        If True, tries to open links in a GUI based browser.
    """

    if not urlparse(url).scheme:
        # Prefix with 'http://' if no scheme
        # Otherwise, opening in browser fails anyway
        # We expect http to https redirection
        # will happen for https-only websites
        LOGERR('Scheme missing in URI, trying http')
        url = 'http://' + url

    browser = webbrowser.get()
    if browse.override_text_browser:
        browser_output = browse.suppress_browser_output
        for name in [b for b in webbrowser._tryorder if b not in TEXT_BROWSERS]:
            browser = webbrowser.get(name)
            LOGDBG(browser)

            # Found a GUI browser, suppress browser output
            browse.suppress_browser_output = True
            break
    if sys.platform == 'win32':  # GUI apps have no terminal IO on Windows
        browse.suppress_browser_output = False

    if browse.suppress_browser_output:
        _stderr = os.dup(2)
        os.close(2)
        _stdout = os.dup(1)
        if "microsoft" not in platform.uname()[3].lower():
            os.close(1)
        fd = os.open(os.devnull, os.O_RDWR)
        os.dup2(fd, 2)
        os.dup2(fd, 1)
    try:
        if sys.platform != 'win32':
            browser.open(url, new=2)
        else:
            # On Windows, the webbrowser module does not fork.
            # Use threads instead.
            def browserthread():
                webbrowser.open(url, new=2)

            t = threading.Thread(target=browserthread)
            t.start()
    except Exception as e:
        LOGERR('browse(): %s', e)
    finally:
        if browse.suppress_browser_output:
            os.close(fd)
            os.dup2(_stderr, 2)
            os.dup2(_stdout, 1)

    if browse.override_text_browser:
        browse.suppress_browser_output = browser_output


def check_upstream_release():
    """Check and report the latest upstream release version."""

    if MYPROXY is None:
        gen_headers()

    ca_certs = os.getenv('BUKU_CA_CERTS', default=CA_CERTS)
    if MYPROXY:
        manager = urllib3.ProxyManager(
            MYPROXY,
            num_pools=1,
            headers=MYHEADERS,
            cert_reqs='CERT_REQUIRED',
            ca_certs=ca_certs
        )
    else:
        manager = urllib3.PoolManager(num_pools=1,
                                      headers={'User-Agent': USER_AGENT},
                                      cert_reqs='CERT_REQUIRED',
                                      ca_certs=ca_certs)

    try:
        r = manager.request(
            'GET',
            'https://api.github.com/repos/jarun/buku/releases?per_page=1',
            headers={'User-Agent': USER_AGENT}
        )
    except Exception as e:
        LOGERR(e)
        return

    if r.status == 200:
        latest = json.loads(r.data.decode(errors='replace'))[0]['tag_name']
        if latest == 'v' + __version__:
            print('This is the latest release')
        else:
            print('Latest upstream release is %s' % latest)
    else:
        LOGERR('[%s] %s', r.status, r.reason)

    manager.clear()


def regexp(expr, item):
    """Perform a regular expression search.

    Parameters
    ----------
    expr : regex
        Regular expression to search for.
    item : str
        Item on which to perform regex search.

    Returns
    -------
    bool
        True if result of search is not None, else False.
    """

    if expr is None or item is None:
        LOGDBG('expr: [%s], item: [%s]', expr, item)
        return False

    return re.search(expr, item, re.IGNORECASE) is not None


def delim_wrap(token):
    """Returns token string wrapped in delimiters.

    Parameters
    ----------
    token : str
        String item to wrap with DELIM.

    Returns
    -------
    str
        Token string wrapped by DELIM.
    """

    if token is None or token.strip() == '':
        return DELIM

    if token[0] != DELIM:
        token = DELIM + token

    if token[-1] != DELIM:
        token = token + DELIM

    return token


def read_in(msg):
    """A wrapper to handle input() with interrupts disabled.

    Parameters
    ----------
    msg : str
        String to pass to to input().
    """

    disable_sigint_handler()
    message = None
    try:
        message = input(msg)
    except KeyboardInterrupt:
        print('Interrupted.')

    enable_sigint_handler()
    return message


def sigint_handler(signum, frame):
    """Custom SIGINT handler.

    .. Note:: Neither signum nor frame are used in
              this custom handler. However, they are
              required parameters for signal handlers.

    Parameters
    ----------
    signum : int
        Signal number.
    frame : frame object or None.
    """

    global INTERRUPTED

    INTERRUPTED = True
    print('\nInterrupted.', file=sys.stderr)

    # Do a hard exit from here
    os._exit(1)

DEFAULT_HANDLER = signal.signal(signal.SIGINT, sigint_handler)


def disable_sigint_handler():
    """Disable signint handler."""
    signal.signal(signal.SIGINT, DEFAULT_HANDLER)


def enable_sigint_handler():
    """Enable sigint handler."""
    signal.signal(signal.SIGINT, sigint_handler)

# ---------------------
# Editor mode functions
# ---------------------


def get_system_editor():
    """Returns default system editor is $EDITOR is set."""

    return os.environ.get('EDITOR', 'none')


def is_editor_valid(editor):
    """Check if the editor string is valid.

    Parameters
    ----------
    editor : str
        Editor string.

    Returns
    -------
    bool
        True if string is valid, else False.
    """

    if editor == 'none':
        LOGERR('EDITOR is not set')
        return False

    if editor == '0':
        LOGERR('Cannot edit index 0')
        return False

    return True


def to_temp_file_content(url, title_in, tags_in, desc):
    """Generate temporary file content string.

    Parameters
    ----------
    url : str
        URL to open.
    title_in : str
        Title to add manually.
    tags_in : str
        Comma-separated tags to add manually.
    desc : str
        String description.

    Returns
    -------
    str
        Lines as newline separated string.

    Raises
    ------
    AttributeError
        when tags_in is None.
    """

    strings = [('# Lines beginning with "#" will be stripped.\n'
                '# Add URL in next line (single line).'), ]

    # URL
    if url is not None:
        strings += (url,)

    # TITLE
    strings += (('# Add TITLE in next line (single line). '
                 'Leave blank to web fetch, "-" for no title.'),)
    if title_in is None:
        title_in = ''
    elif title_in == '':
        title_in = '-'
    strings += (title_in,)

    # TAGS
    strings += ('# Add comma-separated TAGS in next line (single line).',)
    strings += (tags_in.strip(DELIM),) if not None else ''

    # DESC
    strings += ('# Add COMMENTS in next line(s). Leave blank to web fetch, "-" for no comments.',)
    if desc is None:
        strings += ('\n',)
    elif desc == '':
        strings += ('-',)
    else:
        strings += (desc,)
    return '\n'.join(strings)


def parse_temp_file_content(content):
    """Parse and return temporary file content.

    Parameters
    ----------
    content : str
        String of content.

    Returns
    -------
    tuple
        (url, title, tags, comments)

        url: URL to open
        title: string title to add manually
        tags: string of comma-separated tags to add manually
        comments: string description
    """

    content = content.split('\n')
    content = [c for c in content if not c or c[0] != '#']
    if not content or content[0].strip() == '':
        print('Edit aborted')
        return None

    url = content[0]
    title = None
    if len(content) > 1:
        title = content[1]

    if title == '':
        title = None
    elif title == '-':
        title = ''

    tags = DELIM
    if len(content) > 2:
        tags = parse_tags([content[2]])

    comments = []
    if len(content) > 3:
        comments = list(content[3:])
        # need to remove all empty line that are at the end
        # and not those in the middle of the text
        for i in range(len(comments) - 1, -1, -1):
            if comments[i].strip() != '':
                break

        if i == -1:
            comments = []
        else:
            comments = comments[0:i+1]

    comments = '\n'.join(comments)
    if comments == '':
        comments = None
    elif comments == '-':
        comments = ''

    return url, title, tags, comments


def edit_rec(editor, url, title_in, tags_in, desc):
    """Edit a bookmark record.

    Parameters
    ----------
    editor : str
        Editor to open.
    URL : str
        URL to open.
    title_in : str
        Title to add manually.
    tags_in : str
        Comma-separated tags to add manually.
    desc : str
        Bookmark description.

    Returns
    -------
    tuple
        Parsed results from parse_temp_file_content().
    """

    temp_file_content = to_temp_file_content(url, title_in, tags_in, desc)

    fd, tmpfile = tempfile.mkstemp(prefix='buku-edit-')
    os.close(fd)

    try:
        with open(tmpfile, 'w+', encoding='utf-8') as fp:
            fp.write(temp_file_content)
            fp.flush()
            LOGDBG('Edited content written to %s', tmpfile)

        cmd = editor.split(' ')
        cmd += (tmpfile,)
        subprocess.call(cmd)

        with open(tmpfile, 'r', encoding='utf-8') as f:
            content = f.read()

        os.remove(tmpfile)
    except FileNotFoundError:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)
            LOGERR('Cannot open editor')
        else:
            LOGERR('Cannot open tempfile')
        return None

    parsed_content = parse_temp_file_content(content)
    return parsed_content


def setup_logger(LOGGER):
    """Setup logger with color.

    Parameters
    ----------
    LOGGER : logger object
        Logger to colorize.
    """

    def decorate_emit(fn):
        def new(*args):
            levelno = args[0].levelno

            if levelno == logging.DEBUG:
                color = '\x1b[35m'
            elif levelno == logging.ERROR:
                color = '\x1b[31m'
            elif levelno == logging.WARNING:
                color = '\x1b[33m'
            elif levelno == logging.INFO:
                color = '\x1b[32m'
            elif levelno == logging.CRITICAL:
                color = '\x1b[31m'
            else:
                color = '\x1b[0m'

            args[0].msg = '{}[{}]\x1b[0m {}'.format(color, args[0].levelname, args[0].msg)
            return fn(*args)
        return new

    sh = logging.StreamHandler()
    sh.emit = decorate_emit(sh.emit)
    LOGGER.addHandler(sh)


def piped_input(argv, pipeargs=None):
    """Handle piped input.

    Parameters
    ----------
    pipeargs : str
    """
    if not sys.stdin.isatty():
        pipeargs += argv
        print('buku: waiting for input (unexpected? try --nostdin)')
        for s in sys.stdin:
            pipeargs += s.split()


def setcolors(args):
    """Get colors from user and separate into 'result' list for use in arg.colors.

    Parameters
    ----------
    args : str
        Color string.
    """
    Colors = collections.namedtuple('Colors', ' ID_srch, ID_STR, URL_STR, DESC_STR, TAG_STR')
    colors = Colors(*[COLORMAP[c] for c in args])
    id_col = colors.ID_srch
    id_str_col = colors.ID_STR
    url_col = colors.URL_STR
    desc_col = colors.DESC_STR
    tag_col = colors.TAG_STR
    result = [id_col, id_str_col, url_col, desc_col, tag_col]
    return result


def unwrap(text):
    """Unwrap text."""
    lines = text.split('\n')
    result = ''
    for i in range(len(lines) - 1):
        result += lines[i]
        if not lines[i]:
            # Paragraph break
            result += '\n\n'
        elif lines[i + 1]:
            # Next line is not paragraph break, add space
            result += ' '
    # Handle last line
    result += lines[-1] if lines[-1] else '\n'
    return result


def check_stdout_encoding():
    """Make sure stdout encoding is utf-8.

    If not, print error message and instructions, then exit with
    status 1.

    This function is a no-op on win32 because encoding on win32 is
    messy, and let's just hope for the best. /s
    """
    if sys.platform == 'win32':
        return

    # Use codecs.lookup to resolve text encoding alias
    encoding = codecs.lookup(sys.stdout.encoding).name
    if encoding != 'utf-8':
        locale_lang, locale_encoding = locale.getlocale()
        if locale_lang is None:
            locale_lang = '<unknown>'
        if locale_encoding is None:
            locale_encoding = '<unknown>'
        ioencoding = os.getenv('PYTHONIOENCODING', 'not set')
        sys.stderr.write(unwrap(textwrap.dedent("""\
        stdout encoding '{encoding}' detected. ddgr requires utf-8 to
        work properly. The wrong encoding may be due to a non-UTF-8
        locale or an improper PYTHONIOENCODING. (For the record, your
        locale language is {locale_lang} and locale encoding is
        {locale_encoding}; your PYTHONIOENCODING is {ioencoding}.)

        Please set a UTF-8 locale (e.g., en_US.UTF-8) or set
        PYTHONIOENCODING to utf-8.
        """.format(
            encoding=encoding,
            locale_lang=locale_lang,
            locale_encoding=locale_encoding,
            ioencoding=ioencoding,
        ))))
        sys.exit(1)


def monkeypatch_textwrap_for_cjk():
    """Monkeypatch textwrap for CJK wide characters.
    """
    try:
        if textwrap.wrap.patched:
            return
    except AttributeError:
        pass
    psl_textwrap_wrap = textwrap.wrap

    def textwrap_wrap(text, width=70, **kwargs):
        width = max(width, 2)
        # We first add a U+0000 after each East Asian Fullwidth or East
        # Asian Wide character, then fill to width - 1 (so that if a NUL
        # character ends up on a new line, we still have one last column
        # to spare for the preceding wide character). Finally we strip
        # all the NUL characters.
        #
        # East Asian Width: https://www.unicode.org/reports/tr11/
        return [
            line.replace('\0', '')
            for line in psl_textwrap_wrap(
                ''.join(
                    ch + '\0' if unicodedata.east_asian_width(ch) in ('F', 'W') else ch
                    for ch in unicodedata.normalize('NFC', text)
                ),
                width=width - 1,
                **kwargs
            )
        ]

    def textwrap_fill(text, width=70, **kwargs):
        return '\n'.join(textwrap_wrap(text, width=width, **kwargs))
    textwrap.wrap = textwrap_wrap
    textwrap.fill = textwrap_fill
    textwrap.wrap.patched = True
    textwrap.fill.patched = True


def parse_range(tokens: Optional[str | Sequence[str] | Set[str]],  # Optional[str | Values[str]]
                valid: Optional[Callable[[int], bool]] = None,
                maxidx: int = None) -> Optional[Set[int]]:
    """Convert a token or sequence/set of token into a set of indices.

    Raises a ValueError on invalid token. Returns None if passed None as tokens.

    Parameters
    ----------
    tokens : str | str[] | str{}, optional
        String(s) containing an index (#), or a range (#-#), or a comma-separated list thereof.
    valid : (int) -> bool, optional
        Additional check for invalid indices (default is None).
    maxidx : int, optional
        When specified, negative indices are valid and parsed as tail-ranges.

    Returns
    -------
    Optional[Set[int]]
        None if tokens is None, otherwise parsed indices as unordered set.
    """
    if tokens is None:
        return None
    result = set()
    for token in ([tokens] if isinstance(tokens, str) else tokens):
        for idx in token.split(','):
            if is_int(idx):
                result |= ({int(idx)} if not idx.startswith('-') or maxidx is None else
                           set(range(maxidx, max(0, maxidx + int(idx)), -1)))
            elif '-' in idx:
                l, r = map(int, idx.split('-'))
                if l > r:
                    l, r = r, l
                if maxidx is not None:
                    r = min(r, maxidx)
                result |= set(range(l, r + 1))
            elif idx:
                raise ValueError(f'Invalid token: {idx}')
    if valid and any(not valid(idx) for idx in result):
        raise ValueError('Not a valid range')
    return result


# main starts here
def main(argv=sys.argv[1:], *, program_name=os.path.basename(sys.argv[0])):
    """Main."""
    global ID_STR, ID_DB_STR, MUTE_STR, URL_STR, DESC_STR, DESC_WRAP, TAG_STR, TAG_WRAP, PROMPTMSG
    # readline should not be loaded when buku is used as a library
    import readline
    if sys.platform == 'win32':
        try:
            import colorama
            colorama.just_fix_windows_console()  # noop on non-Windows systems
        except ImportError:
            pass

    title_in = None
    tags_in = None
    desc_in = None
    pipeargs = []
    colorstr_env = os.getenv('BUKU_COLORS')

    if argv == ['--db']:
        for s in sorted(s for s in os.listdir(BukuDb.get_default_dbdir()) if s.endswith('.db')):
            print(s.removesuffix('.db'))
        return

    if argv and argv[0] != '--nostdin':
        try:
            piped_input(argv, pipeargs)
        except KeyboardInterrupt:
            pass

        # If piped input, set argument vector
        if pipeargs:
            argv = pipeargs

    # Setup custom argument parser
    argparser = ExtendedArgumentParser(
        prog=program_name,
        description='''Bookmark manager like a text-based mini-web.

POSITIONAL ARGUMENTS:
      KEYWORD              search keywords''',
        formatter_class=argparse.RawTextHelpFormatter,
        usage='''buku [OPTIONS] [KEYWORD [KEYWORD ...]]''',
        add_help=False)
    hide = argparse.SUPPRESS

    argparser.add_argument('keywords', nargs='*', metavar='KEYWORD', help=hide)

    # ---------------------
    # GENERAL OPTIONS GROUP
    # ---------------------

    general_grp = argparser.add_argument_group(
        title='GENERAL OPTIONS',
        description='''    -a, --add URL [+|-] [tag, ...]
                         bookmark URL with comma-separated tags
                         (prepend tags with '+' or '-' to use fetched tags)
    -u, --update [...]   update fields of an existing bookmark
                         accepts indices and ranges
                         refresh title and desc if no edit options
                         if no arguments:
                         - update results when used with search
                         - otherwise refresh all titles and desc
    -w, --write [editor|index]
                         edit and add a new bookmark in editor
                         else, edit bookmark at index in EDITOR
                         edit last bookmark, if index=-1
                         if no args, edit new bookmark in EDITOR
    -d, --delete [...]   remove bookmarks from DB
                         accepts indices or a single range
                         if no arguments:
                         - delete results when used with search
                         - otherwise delete all bookmarks
    --retain-order       prevents reordering after deleting a bookmark
    -h, --help           show this information and exit
    -v, --version        show the program version and exit''')
    addarg = general_grp.add_argument
    addarg('-a', '--add', nargs='+', help=hide)
    addarg('-u', '--update', nargs='*', help=hide)
    addarg('-w', '--write', nargs='?', const=get_system_editor(), help=hide)
    addarg('-d', '--delete', nargs='*', help=hide)
    addarg('--retain-order', action='store_true', default=False, help=hide)
    addarg('-h', '--help', action='store_true', help=hide)
    addarg('-v', '--version', action='version', version=__version__, help=hide)

    # ------------------
    # EDIT OPTIONS GROUP
    # ------------------

    edit_grp = argparser.add_argument_group(
        title='EDIT OPTIONS',
        description='''    --url keyword        bookmark link
    --tag [+|-] [...]    comma-separated tags
                         clear bookmark tagset, if no arguments
                         '+' appends to, '-' removes from tagset
    --title [...]        bookmark title; if no arguments:
                         -a: do not set title, -u: clear title
    -c, --comment [...]  notes or description of the bookmark
                         clears description, if no arguments
    --immutable N        disable web-fetch during auto-refresh
                         N=0: mutable (default), N=1: immutable
    --swap N M           swap two records at specified indices''')
    addarg = edit_grp.add_argument
    addarg('--url', nargs=1, help=hide)
    addarg('--tag', nargs='*', help=hide)
    addarg('--title', nargs='*', help=hide)
    addarg('-c', '--comment', nargs='*', help=hide)
    addarg('--immutable', type=int, choices={0, 1}, help=hide)
    addarg('--swap', nargs=2, type=int, help=hide)
    _bool = lambda x: x if x is None else bool(x)
    _immutable = lambda args: _bool(args.immutable)

    # --------------------
    # SEARCH OPTIONS GROUP
    # --------------------

    search_grp = argparser.add_argument_group(
        title='SEARCH OPTIONS',
        description='''    -s, --sany [...]     find records with ANY matching keyword
                         this is the default search option
    -S, --sall [...]     find records matching ALL the keywords
                         special keywords -
                         "blank": entries with empty title/tag
                         "immutable": entries with locked title
    --deep               match substrings ('pen' matches 'opens')
    --markers            search for keywords in specific fields
                         based on (optional) prefix markers:
                         '.' - title, '>' - description, ':' - URL,
                         '#' - tags (comma-separated, PARTIAL matches)
                         '#,' - tags (comma-separated, EXACT matches)
                         '*' - any field (same as no prefix)
    -r, --sreg expr      run a regex search
    -t, --stag [tag [,|+] ...] [- tag, ...]
                         search bookmarks by tags
                         use ',' to find entries matching ANY tag
                         use '+' to find entries matching ALL tags
                         excludes entries with tags after ' - '
                         list all tags, if no search keywords
    -x, --exclude [...]  omit records matching specified keywords
    --random [N]         output random bookmarks out of the selection (default 1)
    --order fields [...] comma-separated list of fields to order the output by
                         (prepend with '+'/'-' to choose sort direction)''')
    addarg = search_grp.add_argument
    addarg('-s', '--sany', nargs='*', help=hide)
    addarg('-S', '--sall', nargs='*', help=hide)
    addarg('-r', '--sreg', nargs='*', help=hide)
    addarg('--deep', action='store_true', help=hide)
    addarg('--markers', action='store_true', help=hide)
    addarg('-t', '--stag', nargs='*', help=hide)
    addarg('-x', '--exclude', nargs='*', help=hide)
    addarg('--random', nargs='?', type=int, const=1, help=hide)
    addarg('--order', nargs='+', help=hide)

    # ------------------------
    # ENCRYPTION OPTIONS GROUP
    # ------------------------

    crypto_grp = argparser.add_argument_group(
        title='ENCRYPTION OPTIONS',
        description='''    -l, --lock [N]       encrypt DB in N (default 8) # iterations
    -k, --unlock [N]     decrypt DB in N (default 8) # iterations''')
    addarg = crypto_grp.add_argument
    addarg('-k', '--unlock', nargs='?', type=int, const=8, help=hide)
    addarg('-l', '--lock', nargs='?', type=int, const=8, help=hide)

    # ----------------
    # POWER TOYS GROUP
    # ----------------

    power_grp = argparser.add_argument_group(
        title='POWER TOYS',
        description='''    --ai                 auto-import bookmarks from web browsers
                         Firefox, Chrome, Chromium, Vivaldi, Edge
                         (Firefox profile can be specified using
                         environment variable FIREFOX_PROFILE)
    -e, --export file    export bookmarks to Firefox format HTML
                         export XBEL, if file ends with '.xbel'
                         export Markdown, if file ends with '.md'
                         format: [title](url) <!-- TAGS -->
                         export Orgfile, if file ends with '.org'
                         format: *[[url][title]] :tags:
                         export rss feed if file ends with '.rss'/'.atom'
                         export buku DB, if file ends with '.db'
                         combines with search results, if opted
    -i, --import file    import bookmarks from file
                         supports .html .xbel .json .md .org .rss .atom .db
    -p, --print [...]    show record details by indices, ranges
                         print all bookmarks, if no arguments
                         -n shows the last n results (like tail)
    -f, --format N       limit fields in -p or JSON search output
                         N=1: URL; N=2: URL, tag; N=3: title;
                         N=4: URL, title, tag; N=5: title, tag;
                         N0 (10, 20, 30, 40, 50) omits DB index
    -j, --json [file]    JSON formatted output for -p and search.
                         prints to stdout if argument missing.
                         otherwise writes to given file
    --colors COLORS      set output colors in five-letter string
    --nc                 disable color output
    -n, --count N        show N results per page (default 10)
    --np                 do not show the subprompt, run and exit
    -o, --open [...]     browse bookmarks by indices and ranges
                         open a random bookmark, if no arguments
    --oa                 browse all search results immediately
    --replace old new    replace old tag with new tag everywhere
                         delete old tag, if new tag not specified
    --url-redirect       when fetching an URL, use the resulting
                         URL from following *permanent* redirects
                         (when combined with --export, the old URL
                         is included as additional metadata)
    --tag-redirect [tag] when fetching an URL that causes permanent
                         redirect, add a tag in specified pattern
                         (using 'http:{}' if not specified)
    --tag-error [tag]    when fetching an URL that causes an HTTP
                         error, add a tag in specified pattern
                         (using 'http:{}' if not specified)
    --del-error [...]    when fetching an URL causes any (given)
                         HTTP error, delete/do not add it
    --export-on [...]    export records affected by the above
                         options, including removed info
                         (requires --update and --export; specific
                         HTTP response filter can be provided)
    --cached index|URL   browse a cached page from Wayback Machine
    --offline            add a bookmark without connecting to web
    --suggest            show similar tags when adding bookmarks
    --tacit              reduce verbosity, skip some confirmations
    --nostdin            do not wait for input (must be first arg)
    --threads N          max network connections in full refresh
                         default N=4, min N=1, max N=10
    -V                   check latest upstream version available
    -g, --debug          show debug information and verbose logs''')
    addarg = power_grp.add_argument
    addarg('--ai', action='store_true', help=hide)
    addarg('-e', '--export', nargs=1, help=hide)
    addarg('-i', '--import', nargs=1, dest='importfile', help=hide)
    addarg('-p', '--print', nargs='*', help=hide)
    addarg('-f', '--format', type=int, default=0, choices={1, 2, 3, 4, 5, 10, 20, 30, 40, 50}, help=hide)
    addarg('-j', '--json', nargs='?', default=None, const='', help=hide)
    addarg('--colors', dest='colorstr', type=argparser.is_colorstr, metavar='COLORS', help=hide)
    addarg('--nc', action='store_true', help=hide)
    addarg('-n', '--count', nargs='?', const=10, type=int, default=0, help=hide)
    addarg('--np', action='store_true', help=hide)
    addarg('-o', '--open', nargs='*', help=hide)
    addarg('--oa', action='store_true', help=hide)
    addarg('--replace', nargs='+', help=hide)
    addarg('--url-redirect', action='store_true', help=hide)
    addarg('--tag-redirect', nargs='?', const=True, default=False, help=hide)
    addarg('--tag-error', nargs='?', const=True, default=False, help=hide)
    addarg('--del-error', nargs='*', help=hide)
    addarg('--export-on', nargs='*', help=hide)
    addarg('--cached', nargs=1, help=hide)
    addarg('--offline', action='store_true', help=hide)
    addarg('--suggest', action='store_true', help=hide)
    addarg('--tacit', action='store_true', help=hide)
    addarg('--nostdin', action='store_true', help=hide)
    addarg('--threads', type=int, default=4, choices=range(1, 11), help=hide)
    addarg('-V', dest='upstream', action='store_true', help=hide)
    addarg('-g', '--debug', action='store_true', help=hide)
    # Undocumented APIs
    # Fix uppercase tags allowed in releases before v2.7
    addarg('--fixtags', action='store_true', help=hide)
    # App-use only, not for manual usage
    addarg('--db', nargs=1, default=[None], help=hide)

    # Parse the arguments
    args = argparser.parse_args(argv)

    # Show help and exit if help requested
    if args.help:
        argparser.print_help()
        sys.exit(0)

    # By default, buku uses ANSI colors. As Windows does not really use them,
    # we'd better check for known working console emulators first. Currently,
    # only ConEmu is supported. If the user does not use ConEmu, colors are
    # disabled unless --colors or %BUKU_COLORS% is specified.
    if sys.platform == 'win32' and os.environ.get('ConemuDir') is None:
        if args.colorstr is None and colorstr_env is not None:
            args.nc = True

    # Handle NO_COLOR as well:
    if os.environ.get('NO_COLOR') is not None:
        args.nc = True

    # Handle color output preference
    if args.nc:
        logging.basicConfig(format='[%(levelname)s] %(message)s')
    else:
        # Set colors
        if colorstr_env is not None:
            # Someone set BUKU_COLORS.
            colorstr = colorstr_env
        elif args.colorstr is not None:
            colorstr = args.colorstr
        else:
            colorstr = 'oKlxm'

        ID = setcolors(colorstr)[0] + '%d. ' + COLORMAP['x']
        ID_DB_dim = COLORMAP['z'] + '[%s]\n' + COLORMAP['x']
        ID_STR = ID + setcolors(colorstr)[1] + '%s ' + COLORMAP['x'] + ID_DB_dim
        ID_DB_STR = ID + setcolors(colorstr)[1] + '%s' + COLORMAP['x']
        MUTE_STR = '%s \x1b[2m(L)\x1b[0m\n'
        URL_STR = COLORMAP['j'] + '   > ' + setcolors(colorstr)[2] + '%s\n' + COLORMAP['x']
        DESC_STR = COLORMAP['j'] + '   + ' + setcolors(colorstr)[3] + '%s\n' + COLORMAP['x']
        DESC_WRAP = COLORMAP['j'] + setcolors(colorstr)[3] + '%s%s' + COLORMAP['x']
        TAG_STR = COLORMAP['j'] + '   # ' + setcolors(colorstr)[4] + '%s\n' + COLORMAP['x']
        TAG_WRAP = COLORMAP['j'] + setcolors(colorstr)[4] + '%s%s' + COLORMAP['x']

        # Enable color in logs
        setup_logger(LOGGER)

        # Enable prompt with reverse video
        PROMPTMSG = '\001\x1b[7\002mbuku (? for help)\001\x1b[0m\002 '

    # Enable browser output in case of a text based browser
    if os.getenv('BROWSER') in TEXT_BROWSERS:
        browse.suppress_browser_output = False
    else:
        browse.suppress_browser_output = True

    # Overriding text browsers is disabled by default
    browse.override_text_browser = False

    # Handle DB name (--db value without extension and path separators)
    _db = args.db[0]
    if _db and not os.path.dirname(_db) and not os.path.splitext(_db)[1]:
        _db = os.path.join(BukuDb.get_default_dbdir(), _db + '.db')

    # Fallback to prompt if no arguments
    if args._passed <= {'nostdin', 'db'}:
        try:
            _db = _db or os.path.join(BukuDb.get_default_dbdir(), 'bookmarks.db')
            if not os.path.exists(_db):
                print(f'DB file is being created at {_db}')  # not printed without chatty param
            bdb = BukuDb(dbfile=_db)
        except Exception:
            sys.exit(1)
        prompt(bdb, None)
        bdb.close_quit(0)

    # Set up debugging
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)
        LOGDBG('buku v%s', __version__)
        LOGDBG('Python v%s', ('%d.%d.%d' % sys.version_info[:3]))
    else:
        logging.disable(logging.WARNING)
        urllib3.disable_warnings()

    # Handle encrypt/decrypt options at top priority
    if args.lock is not None:
        BukuCrypt.encrypt_file(args.lock, dbfile=_db)
    elif args.unlock is not None:
        BukuCrypt.decrypt_file(args.unlock, dbfile=_db)

    order = [s for ss in (args.order or []) for s in re.split(r'\s*,\s*', ss.strip()) if s]

    # Set up title
    if args.title is not None:
        title_in = ' '.join(args.title)

    # Set up tags
    if args.tag is not None:
        tags_in = args.tag or [DELIM]

    # Set up comment
    if args.comment is not None:
        desc_in = ' '.join(args.comment)

    # validating HTTP-code handling args
    tag_redirect = args.tag_redirect
    if isinstance(args.tag_redirect, str):
        try:
            args.tag_redirect.format(301)
            tag_redirect = args.tag_redirect.strip() or True
        except (IndexError, KeyError):
            LOGERR('Invalid format of --tag-redirect (should use "{}" as placeholder)')
            sys.exit(1)
    tag_error = args.tag_error
    if isinstance(args.tag_error, str):
        try:
            args.tag_error.format(301)
            tag_error = args.tag_error.strip() or True
        except (IndexError, KeyError):
            LOGERR('Invalid format of --tag-error (should use "{}" as placeholder)')
            sys.exit(1)
    try:
        del_error = (None if args.del_error is None else
                     parse_range(args.del_error, lambda x: 400 <= x < 600) or range(400, 600))
    except ValueError:
        LOGERR('Invalid HTTP code(s) given for --del-error (should be within 4xx/5xx ranges)')
        sys.exit(1)
    try:
        _default = (set() if not args.url_redirect and not tag_redirect else PERMANENT_REDIRECTS)
        _default |= set([] if not tag_error else range(400, 600)) | set(del_error or [])
        export_on = (None if args.export_on is None else
                     parse_range(args.export_on, lambda x: 100 <= x < 600) or _default)
    except ValueError:
        LOGERR('Invalid HTTP code(s) given for --export-on')
        sys.exit(1)

    # Initialize the database and get handles, set verbose by default
    try:
        bdb = BukuDb(args.json, args.format, not args.tacit, dbfile=_db, colorize=not args.nc)
    except Exception:
        sys.exit(1)

    if args.swap:
        index1, index2 = args.swap
        if bdb.swap_recs(index1, index2):
            bdb.print_rec({index1, index2})
        else:
            LOGERR('Failed to swap records #%d and #%d', index1, index2)
        bdb.close_quit(0)

    # Editor mode
    if args.write is not None:
        if not is_editor_valid(args.write):
            bdb.close_quit(1)

        if is_int(args.write):
            if not bdb.edit_update_rec(int(args.write), _immutable(args)):
                bdb.close_quit(1)
        elif args.add is None:
            # Edit and add a new bookmark
            # Parse tags into a comma-separated string
            tags = parse_tags(tags_in, edit_input=True)

            result = edit_rec(args.write, '', title_in, tags, desc_in)
            if result is not None:
                url, title_in, tags, desc_in = result
                if args.suggest:
                    tags = bdb.suggest_similar_tag(tags)
                bdb.add_rec(url, title_in, tags, desc_in, _immutable(args), False, not args.offline)

    # Add record
    if args.add is not None:
        if args.url is not None and args.update is None:
            LOGERR('Bookmark a single URL at a time')
            bdb.close_quit(1)

        # Parse tags into a comma-separated string
        # --add may have URL followed by tags
        keywords_except, keywords = [], args.add[1:]
        # taglists are taken from --add (starting from 2nd value) and from --tags
        # if taglist starts with '-', its contents are excluded from resulting tags
        # if BOTH taglists is are either empty or start with '+'/'-', fetched tags are included
        if keywords and keywords[0] == '-':
            keywords, keywords_except = [], keywords[1:]
        tags_add = (not keywords or keywords[0] == '+')
        if tags_add:
            keywords = keywords[1:]
        if tags_in:
            # note: need to add a delimiter as url+tags may not end with one
            if tags_in[0] == '-':
                keywords_except += [DELIM] + tags_in[1:]
            elif tags_in[0] == '+':
                keywords += [DELIM] + tags_in[1:]
            else:
                keywords += [DELIM] + tags_in
                tags_add = False

        tags, tags_except = parse_tags(keywords), parse_tags(keywords_except)
        tags, tags_except = ((s if s and s != DELIM else None) for s in [tags, tags_except])
        url = args.add[0]
        edit_aborted = False

        if args.write and not is_int(args.write):
            result = edit_rec(args.write, url, title_in, tags, desc_in)
            if result is not None:
                url, title_in, tags, desc_in = result
            else:
                edit_aborted = True

        if edit_aborted is False:
            if args.suggest:
                tags = bdb.suggest_similar_tag(tags)
            network_test = args.url_redirect or tag_redirect or tag_error or del_error
            fetch = not args.offline and (network_test or tags_add or title_in is None)
            bdb.add_rec(url, title_in, tags, desc_in, _immutable(args), delay_commit=False, fetch=fetch,
                        tags_fetch=tags_add, tags_except=tags_except, url_redirect=args.url_redirect,
                        tag_redirect=tag_redirect, tag_error=tag_error, del_error=del_error)

    # Search record
    search_results, search_opted = None, True

    if args.sany is not None:
        if not args.sany:
            LOGERR('no keyword')
        else:
            LOGDBG('args.sany')
            # Apply tag filtering, if opted
            search_results = bdb.search_keywords_and_filter_by_tags(
                args.sany, deep=args.deep, stag=args.stag, markers=args.markers, without=args.exclude, order=order)
    elif args.sall is not None:
        if not args.sall:
            LOGERR('no keyword')
        else:
            LOGDBG('args.sall')
            search_results = bdb.search_keywords_and_filter_by_tags(
                args.sall, all_keywords=True, deep=args.deep, stag=args.stag,
                markers=args.markers, without=args.exclude, order=order)
    elif args.sreg is not None:
        if not args.sreg:
            LOGERR('no expression')
        else:
            LOGDBG('args.sreg')
            search_results = bdb.search_keywords_and_filter_by_tags(
                args.sreg, regex=True, stag=args.stag, markers=args.markers, without=args.exclude, order=order)
    elif args.keywords:
        LOGDBG('args.keywords')
        search_results = bdb.search_keywords_and_filter_by_tags(
            args.keywords, deep=args.deep, stag=args.stag, markers=args.markers, without=args.exclude, order=order)
    elif args.stag is not None:
        if not args.stag:  # use sub-prompt to list all tags
            prompt(bdb, None, noninteractive=args.np, listtags=True, suggest=args.suggest, order=order)
        else:
            LOGDBG('args.stag')
            search_results = bdb.exclude_results_from_search(
                bdb.search_by_tag(' '.join(args.stag), order=order), args.exclude, deep=args.deep, markers=args.markers)
    elif args.exclude is not None:
        LOGERR('No search criteria to exclude results from')
    elif args.markers:
        LOGERR('No search criteria to apply markers to')
    else:
        search_opted = False

    # Add cmdline search options to readline history
    if search_opted and len(args.keywords):
        try:
            readline.add_history(' '.join(args.keywords))
        except Exception:
            pass

    check_stdout_encoding()
    monkeypatch_textwrap_for_cjk()

    update_search_results = False
    if search_results:
        if args.random and args.random < len(search_results):
            search_results = bdb._sort(random.sample(search_results, args.random), order)
        single_record = args.random == 1  # matching print_rec() behaviour

        oneshot = args.np

        # Open all results in browser right away if args.oa
        # is specified. The has priority over delete/update.
        # URLs are opened first and updated/deleted later.
        if args.oa:
            for row in search_results:
                browse(row[1])

        if (
                (args.export is not None) or
                (args.delete is not None and not args.delete) or
                (args.update is not None and not args.update)):
            oneshot = True

        if args.json is None and not args.format and not args.random:
            num = 10 if not args.count else args.count
            prompt(bdb, search_results, noninteractive=oneshot, deep=args.deep, markers=args.markers, order=order, num=num)
        elif args.json is None:
            print_rec_with_filter(search_results, field_filter=args.format)
        elif args.json:
            write_string_to_file(format_json(search_results, single_record, field_filter=args.format), args.json)
        else:
            # Printing in JSON format is non-interactive
            print_json_safe(search_results, single_record, field_filter=args.format)

        # Export the results, if opted
        if args.export and not (args.update is not None and export_on):
            bdb.exportdb(args.export[0], search_results)

        # In case of search and delete/update,
        # prompt should be non-interactive
        # delete gets priority over update
        if args.delete is not None and not args.delete:
            bdb.delete_resultset(search_results, retain_order=args.retain_order)
        elif args.update is not None and not args.update:
            update_search_results = True

    # Update record
    if args.update is not None:
        url_in = (args.url[0] if args.url else None)

        # Parse tags into a comma-separated string
        tags = parse_tags(tags_in, edit_input=True)
        tags = (None if tags == DELIM else tags)

        # No arguments to --update, update all
        if not args.update:
            # Update all records only if search was not opted
            if not search_opted:
                _indices = []
            elif search_results and update_search_results:
                if not args.tacit:
                    print('Updated results:\n')

                _indices = [x.id for x in search_results]
            else:
                _indices = None
        else:
            try:
                _indices = parse_range(args.update, lambda x: x >= 0)
            except ValueError:
                LOGERR('Invalid index or range to update')
                bdb.close_quit(1)
            _indices = ([] if 0 in _indices else _indices)
        if _indices is not None:
            bdb.update_rec(_indices, url_in, title_in, tags, desc_in, _immutable(args), threads=args.threads,
                           url_redirect=args.url_redirect, tag_redirect=tag_redirect, tag_error=tag_error,
                           del_error=del_error, export_on=export_on, retain_order=args.retain_order)
            if args.export and bdb._to_export is not None:
                bdb.exportdb(args.export[0], order=order)

    # Delete record
    if args.delete is not None:
        if not args.delete:
            # Attempt delete-all only if search was not opted
            if not search_opted:
                bdb.cleardb()
        elif len(args.delete) == 1 and '-' in args.delete[0]:
            try:
                vals = [int(x) for x in args.delete[0].split('-')]
                if len(vals) == 2:
                    bdb.delete_rec(0, vals[0], vals[1], is_range=True, retain_order=args.retain_order)
            except ValueError:
                LOGERR('Invalid index or range to delete')
                bdb.close_quit(1)
        else:
            ids = set(args.delete)
            try:
                # Index delete order - highest to lowest
                ids = sorted(map(int, ids), reverse=True)
                for idx in ids:
                    bdb.delete_rec(idx, retain_order=args.retain_order)
            except ValueError:
                LOGERR('Invalid index or range or combination')
                bdb.close_quit(1)

    # Print record
    if args.print is not None:
        try:
            max_id = bdb.get_max_id() or 0
            id_range = list(parse_range(args.print, maxidx=max_id) or []) or range(1, 1 + max_id)
        except ValueError:
            LOGERR('Invalid index or range to print')
            bdb.close_quit(1)
        if args.random and args.random < len(id_range):
            bdb.print_rec(random.sample(id_range, args.random), order=order)
        elif not args.print:
            if args.count:
                search_results = bdb.list_using_id(order=order)
                prompt(bdb, search_results, noninteractive=args.np, num=args.count, order=order)
            else:
                bdb.print_rec(None, order=order)
        else:
            if args.count:
                search_results = bdb.list_using_id(args.print, order=order)
                prompt(bdb, search_results, noninteractive=args.np, num=args.count, order=order)
            else:
                bdb.print_rec(id_range, order=order)

    # Replace a tag in DB
    if args.replace is not None:
        if len(args.replace) == 1:
            bdb.delete_tag_at_index(0, args.replace[0])
        else:
            try:
                bdb.replace_tag(args.replace[0], [' '.join(args.replace[1:])])
            except Exception as e:
                LOGERR(str(e))
                bdb.close_quit(1)

    # Export bookmarks
    if args.export and not search_opted and not export_on:
        bdb.exportdb(args.export[0], order=order, pick=args.random)

    # Import bookmarks
    if args.importfile is not None:
        bdb.importdb(args.importfile[0], args.tacit)

    # Import bookmarks from browser
    if args.ai:
        bdb.auto_import_from_browser(firefox_profile=os.environ.get('FIREFOX_PROFILE'))

    # Open URL in browser
    if args.open is not None:
        if not args.open:
            bdb.browse_by_index(0)
        else:
            try:
                for idx in args.open:
                    if is_int(idx):
                        bdb.browse_by_index(int(idx))
                    elif '-' in idx:
                        vals = [int(x) for x in idx.split('-')]
                        bdb.browse_by_index(0, vals[0], vals[-1], True)
            except ValueError:
                LOGERR('Invalid index or range to open')
                bdb.close_quit(1)

    # Try to fetch URL from Wayback Machine
    if args.cached:
        wbu = bdb.browse_cached_url(args.cached[0])
        if wbu is not None:
            browse(wbu)

    # Report upstream version
    if args.upstream:
        check_upstream_release()

    # Fix tags
    if args.fixtags:
        bdb.fixtags()

    # Close DB connection and quit
    bdb.close_quit(0)

if __name__ == '__main__':
    main()
