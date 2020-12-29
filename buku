#!/usr/bin/env python3
#
# Bookmark management utility
#
# Copyright © 2015-2021 Arun Prakash Jana <engineerarun@gmail.com>
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

from enum import Enum
from itertools import chain
import argparse
import calendar
import cgi
import collections
import contextlib
import json
import logging
import os
import platform
import re
import shutil
import signal
import sqlite3
import struct
import subprocess
from subprocess import Popen, PIPE, DEVNULL
import sys
import tempfile
import threading
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple
import webbrowser
import certifi
import urllib3
from urllib3.exceptions import LocationParseError
from urllib3.util import parse_url, make_headers, Retry
from bs4 import BeautifulSoup
# note catch ModuleNotFoundError instead Exception
# when python3.5 not supported
try:
    import readline
except Exception:
    import pyreadline as readline  # type: ignore
try:
    from mypy_extensions import TypedDict
except ImportError:
    TypedDict = None  # type: ignore

__version__ = '4.5'
__author__ = 'Arun Prakash Jana <engineerarun@gmail.com>'
__license__ = 'GPLv3'

# Global variables
INTERRUPTED = False  # Received SIGINT
DELIM = ','  # Delimiter used to store tags in DB
SKIP_MIMES = {'.pdf', '.txt'}
PROMPTMSG = 'buku (? for help): '  # Prompt message string

# Default format specifiers to print records
ID_STR = '%d. %s [%s]\n'
ID_DB_STR = '%d. %s'
MUTE_STR = '%s (L)\n'
URL_STR = '   > %s\n'
DESC_STR = '   + %s\n'
TAG_STR = '   # %s\n'

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

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:84.0) Gecko/20100101 Firefox/84.0'
MYHEADERS = None  # Default dictionary of headers
MYPROXY = None  # Default proxy
TEXT_BROWSERS = ['elinks', 'links', 'links2', 'lynx', 'w3m', 'www-browser']
IGNORE_FF_BOOKMARK_FOLDERS = frozenset(["placesRoot", "bookmarksMenuFolder"])

# Set up logging
LOGGER = logging.getLogger()
LOGDBG = LOGGER.debug
LOGERR = LOGGER.error


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
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.ciphers import (Cipher, modes, algorithms)
            from getpass import getpass
            from hashlib import sha256
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
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.ciphers import (Cipher, modes, algorithms)
            from getpass import getpass
            from hashlib import sha256
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


BookmarkVar = Tuple[int, str, Optional[str], str, str, int]
# example:
# (1, 'http://example.com', 'example title', ',tags1,', 'randomdesc', 0))


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
            self, json: Optional[str] = None, field_filter: Optional[int] = 0, chatty: Optional[bool] = False,
            dbfile: Optional[str] = None, colorize: Optional[bool] = True) -> None:
        """Database initialization API.

        Parameters
        ----------
        json : string
            Empty string if results should be printed in JSON format to stdout.
            Nonempty string if results should be printed in JSON format to file. The string has to be a valid path.
            None if the results should be printed as human-readable plaintext.
        field_filter : int, optional
            Indicates format for displaying bookmarks. Default is 0.
        chatty : bool, optional
            Sets the verbosity of the APIs. Default is False.
        colorize : bool, optional
            Indicates whether color should be used in output. Default is True.
        """

        self.json = json
        self.field_filter = field_filter
        self.chatty = chatty
        self.colorize = colorize
        self.conn, self.cur = BukuDb.initdb(dbfile, self.chatty)

    @staticmethod
    def get_default_dbdir():
        """Determine the directory path where dbfile will be stored.

        If the platform is Windows, use %APPDATA%
        else if $XDG_DATA_HOME is defined, use it
        else if $HOME exists, use it
        else use the current directory.

        Returns
        -------
        str
            Path to database file.
        """

        data_home = os.environ.get('XDG_DATA_HOME')
        if data_home is None:
            if os.environ.get('HOME') is None:
                if sys.platform == 'win32':
                    data_home = os.environ.get('APPDATA')
                    if data_home is None:
                        return os.path.abspath('.')
                else:
                    return os.path.abspath('.')
            else:
                data_home = os.path.join(os.environ.get('HOME'), '.local', 'share')

        return os.path.join(data_home, 'buku')

    @staticmethod
    def initdb(dbfile: Optional[str] = None, chatty: Optional[bool] = False) -> Tuple[sqlite3.Connection, sqlite3.Cursor]:
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
            sys.exit(1)

        return (conn, cur)

    def get_rec_all(self):
        """Get all the bookmarks in the database.

        Returns
        -------
        list
            A list of tuples representing bookmark records.
        """

        self.cur.execute('SELECT * FROM bookmarks')
        return self.cur.fetchall()

    def get_rec_by_id(self, index: int) -> Optional[BookmarkVar]:
        """Get a bookmark from database by its ID.

        Parameters
        ----------
        index : int
            DB index of bookmark record.

        Returns
        -------
        tuple or None
            Bookmark data, or None if index is not found.
        """

        self.cur.execute('SELECT * FROM bookmarks WHERE id = ? LIMIT 1', (index,))
        resultset = self.cur.fetchall()
        return resultset[0] if resultset else None

    def get_rec_id(self, url):
        """Check if URL already exists in DB.

        Parameters
        ----------
        url : str
            A URL to search for in the DB.

        Returns
        -------
        int
            DB index, or -1 if URL not found in DB.
        """

        self.cur.execute('SELECT id FROM bookmarks WHERE URL = ? LIMIT 1', (url,))
        resultset = self.cur.fetchall()
        return resultset[0][0] if resultset else -1

    def get_max_id(self) -> int:
        """Fetch the ID of the last record.

        Returns
        -------
        int
            ID of the record if any record exists, else -1.
        """

        self.cur.execute('SELECT MAX(id) from bookmarks')
        resultset = self.cur.fetchall()
        return -1 if resultset[0][0] is None else resultset[0][0]

    def add_rec(
            self,
            url: str,
            title_in: Optional[str] = None,
            tags_in: Optional[str] = None,
            desc: Optional[str] = None,
            immutable: Optional[int] = 0,
            delay_commit: Optional[bool] = False,
            fetch: Optional[bool] = True) -> int:
        """Add a new bookmark.

        Parameters
        ----------
        url : str
            URL to bookmark.
        title_in :str, optional
            Title to add manually. Default is None.
        tags_in : str, optional
            Comma-separated tags to add manually.
            Must start and end with comma. Default is None.
        desc : str, optional
            Description of the bookmark. Default is None.
        immutable : int, optional
            Indicates whether to disable title fetch from web.
            Default is 0.
        delay_commit : bool, optional
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.
        fetch : bool, optional
            Fetch page from web and parse for data

        Returns
        -------
        int
            DB index of new bookmark on success, -1 on failure.
        """

        # Return error for empty URL
        if not url or url == '':
            LOGERR('Invalid URL')
            return -1

        # Ensure that the URL does not exist in DB already
        id = self.get_rec_id(url)
        if id != -1:
            LOGERR('URL [%s] already exists at index %d', url, id)
            return -1

        if fetch:
            # Fetch data
            ptitle, pdesc, ptags, mime, bad = network_handler(url)
            if bad:
                print('Malformed URL\n')
            elif mime:
                LOGDBG('HTTP HEAD requested')
            elif ptitle == '' and title_in is None:
                print('No title\n')
            else:
                LOGDBG('Title: [%s]', ptitle)
        else:
            ptitle = pdesc = ptags = ''
            LOGDBG('ptags: [%s]', ptags)

        if title_in is not None:
            ptitle = title_in

        # Fix up tags, if broken
        tags_in = delim_wrap(tags_in)

        # Process description
        if desc is None:
            desc = '' if pdesc is None else pdesc

        try:
            flagset = 0
            if immutable == 1:
                flagset |= immutable

            qry = 'INSERT INTO bookmarks(URL, metadata, tags, desc, flags) VALUES (?, ?, ?, ?, ?)'
            self.cur.execute(qry, (url, ptitle, tags_in, desc, flagset))
            if not delay_commit:
                self.conn.commit()
            if self.chatty:
                self.print_rec(self.cur.lastrowid)
            return self.cur.lastrowid
        except Exception as e:
            LOGERR('add_rec(): %s', e)
            return -1

    def append_tag_at_index(self, index, tags_in, delay_commit=False):
        """Append tags to bookmark tagset at index.

        Parameters
        ----------
        index : int
            DB index of the record. 0 indicates all records.
        tags_in : str
            Comma-separated tags to add manually.
        delay_commit : bool, optional
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        if tags_in is None or tags_in == DELIM:
            return True

        if index == 0:
            resp = read_in('Append the tags to ALL bookmarks? (y/n): ')
            if resp != 'y':
                return False

            self.cur.execute('SELECT id, tags FROM bookmarks ORDER BY id ASC')
        else:
            self.cur.execute('SELECT id, tags FROM bookmarks WHERE id = ? LIMIT 1', (index,))

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
        index : int
            DB index of bookmark record. 0 indicates all records.
        tags_in : str
            Comma-separated tags to delete manually.
        delay_commit : bool, optional
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.
        chatty: bool, optional
            Skip confirmation when set to False.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        if tags_in is None or tags_in == DELIM:
            return True

        tags_to_delete = tags_in.strip(DELIM).split(DELIM)

        if index == 0:
            if chatty:
                resp = read_in('Delete the tag(s) from ALL bookmarks? (y/n): ')
                if resp != 'y':
                    return False

            count = 0
            match = "'%' || ? || '%'"
            for tag in tags_to_delete:
                tag = delim_wrap(tag)
                q = ("UPDATE bookmarks SET tags = replace(tags, '%s', '%s') "
                     "WHERE tags LIKE %s" % (tag, DELIM, match))
                self.cur.execute(q, (tag,))
                count += self.cur.rowcount

            if count and not delay_commit:
                self.conn.commit()
                if self.chatty:
                    print('%d record(s) updated' % count)

            return True

        # Process a single index
        # Use SELECT and UPDATE to handle multiple tags at once
        query = 'SELECT id, tags FROM bookmarks WHERE id = ? LIMIT 1'
        self.cur.execute(query, (index,))
        resultset = self.cur.fetchall()
        if resultset:
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
        else:
            return False

        return True

    def update_rec(
            self,
            index: int,
            url: Optional[str] = None,
            title_in: Optional[str] = None,
            tags_in: Optional[str] = None,
            desc: Optional[str] = None,
            immutable: Optional[int] = -1,
            threads: int = 4) -> bool:
        """Update an existing record at index.

        Update all records if index is 0 and url is not specified.
        URL is an exception because URLs are unique in DB.

        Parameters
        ----------
        index : int
            DB index of record. 0 indicates all records.
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
        immutable : int, optional
            Disable title fetch from web if 1. Default is -1.
        threads : int, optional
            Number of threads to use to refresh full DB. Default is 4.

        Returns
        -------
        bool
            True on success, False on Failure.
        """

        arguments = []  # type: List[Any]
        query = 'UPDATE bookmarks SET'
        to_update = False
        tag_modified = False
        ret = False

        # Update URL if passed as argument
        if url is not None and url != '':
            if index == 0:
                LOGERR('All URLs cannot be same')
                return False
            query += ' URL = ?,'
            arguments += (url,)
            to_update = True

        # Update tags if passed as argument
        if tags_in is not None:
            if tags_in in ('+,', '-,'):
                LOGERR('Please specify a tag')
                return False

            if tags_in.startswith('+,'):
                chatty = self.chatty
                self.chatty = False
                ret = self.append_tag_at_index(index, tags_in[1:])
                self.chatty = chatty
                tag_modified = True
            elif tags_in.startswith('-,'):
                chatty = self.chatty
                self.chatty = False
                ret = self.delete_tag_at_index(index, tags_in[1:])
                self.chatty = chatty
                tag_modified = True
            else:
                tags_in = delim_wrap(tags_in)

                query += ' tags = ?,'
                arguments += (tags_in,)
                to_update = True

        # Update description if passed as an argument
        if desc is not None:
            query += ' desc = ?,'
            arguments += (desc,)
            to_update = True

        # Update immutable flag if passed as argument
        if immutable != -1:
            flagset = 1
            if immutable == 1:
                query += ' flags = flags | ?,'
            elif immutable == 0:
                query += ' flags = flags & ?,'
                flagset = ~flagset

            arguments += (flagset,)
            to_update = True

        # Update title
        #
        # 1. If --title has no arguments, delete existing title
        # 2. If --title has arguments, update existing title
        # 3. If --title option is omitted at cmdline:
        #    If URL is passed, update the title from web using the URL
        # 4. If no other argument (url, tag, comment, immutable) passed,
        #    update title from web using DB URL (if title is mutable)
        title_to_insert = None
        pdesc = None
        ptags = None
        if title_in is not None:
            title_to_insert = title_in
        elif url is not None and url != '':
            title_to_insert, pdesc, ptags, mime, bad = network_handler(url)
            if bad:
                print('Malformed URL')
            elif mime:
                LOGDBG('HTTP HEAD requested')
            elif title_to_insert == '':
                print('No title')
            else:
                LOGDBG('Title: [%s]', title_to_insert)

            if not desc:
                if not pdesc:
                    pdesc = ''
                query += ' desc = ?,'
                arguments += (pdesc,)
                to_update = True
        elif not to_update and not tag_modified:
            ret = self.refreshdb(index, threads)
            if ret and index and self.chatty:
                self.print_rec(index)
            return ret

        if title_to_insert is not None:
            query += ' metadata = ?,'
            arguments += (title_to_insert,)
            to_update = True

        if not to_update:  # Nothing to update
            # Show bookmark if tags were appended to deleted
            if tag_modified and self.chatty:
                self.print_rec(index)
            return ret

        if index == 0:  # Update all records
            resp = read_in('Update ALL bookmarks? (y/n): ')
            if resp != 'y':
                return False

            query = query[:-1]
        else:
            query = query[:-1] + ' WHERE id = ?'
            arguments += (index,)

        LOGDBG('update_rec query: "%s", args: %s', query, arguments)

        try:
            self.cur.execute(query, arguments)
            self.conn.commit()
            if self.cur.rowcount and self.chatty:
                self.print_rec(index)

            if self.cur.rowcount == 0:
                LOGERR('No matching index %d', index)
                return False
        except sqlite3.IntegrityError:
            LOGERR('URL already exists')
            return False
        except sqlite3.OperationalError as e:
            LOGERR(e)
            return False

        return True

    def refreshdb(self, index: int, threads: int) -> bool:
        """Refresh ALL records in the database.

        Fetch title for each bookmark from the web and update the records.
        Doesn't update the record if fetched title is empty.

        Notes
        -----
            This API doesn't change DB index, URL or tags of a bookmark.
            This API is verbose.

        Parameters
        ----------
        index : int
            DB index of record to update. 0 indicates all records.
        threads: int
            Number of threads to use to refresh full DB. Default is 4.
        """

        if index == 0:
            self.cur.execute('SELECT id, url, flags FROM bookmarks ORDER BY id ASC')
        else:
            self.cur.execute('SELECT id, url, flags FROM bookmarks WHERE id = ? LIMIT 1', (index,))

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
        # gen_headers() is called within network_handler()
        # However, this initial call to setup headers
        # ensures there is no race condition among the
        # initial threads to setup headers
        if not MYHEADERS:
            gen_headers()

        cond = threading.Condition()
        cond.acquire()

        def refresh(count, cond):
            """Inner function to fetch titles and update records.

            Parameters
            ----------
            count : int
                Dummy input to adhere to convention.
            cond : threading condition object.
            """

            count = 0

            while True:
                query = 'UPDATE bookmarks SET'
                arguments = []

                cond.acquire()
                if resultset:
                    row = resultset.pop()
                else:
                    cond.release()
                    break
                cond.release()

                title, desc, tags, mime, bad = network_handler(row[1], row[2] & 1)
                count += 1

                cond.acquire()

                if bad:
                    print(bad_url_str % row[0])
                    cond.release()
                    continue

                if mime:
                    if self.chatty:
                        print(mime_str % row[0])
                    cond.release()
                    continue

                to_update = False

                if not title or title == '':
                    LOGERR(blank_url_str, row[0])
                else:
                    query += ' metadata = ?,'
                    arguments += (title,)
                    to_update = True

                if desc:
                    query += ' desc = ?,'
                    arguments += (desc,)
                    to_update = True

                if not to_update:
                    cond.release()
                    continue

                query = query[:-1] + ' WHERE id = ?'
                arguments += (row[0],)
                LOGDBG('refreshdb query: "%s", args: %s', query, arguments)

                self.cur.execute(query, arguments)

                # Save after fetching 32 titles per thread
                if count & 0b11111 == 0:
                    self.conn.commit()

                if self.chatty:
                    print(success_str % (title, row[0]))
                cond.release()

                if INTERRUPTED:
                    break

            LOGDBG('Thread %d: processed %d', threading.get_ident(), count)
            with cond:
                done['value'] += 1
                processed['value'] += count
                cond.notify()

        if recs < threads:
            threads = recs

        for i in range(threads):
            thread = threading.Thread(target=refresh, args=(i, cond))
            thread.start()

        while done['value'] < threads:
            cond.wait()
            LOGDBG('%d threads completed', done['value'])

        # Guard: records found == total records processed
        if recs != processed['value']:
            LOGERR('Records: %d, processed: %d !!!', recs, processed['value'])

        cond.release()
        self.conn.commit()
        return True

    def edit_update_rec(self, index, immutable=-1):
        """Edit in editor and update a record.

        Parameters
        ----------
        index : int
            DB index of the record.
            Last record, if index is -1.
        immutable : int, optional
            Diable title fetch from web if 1. Default is -1.

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
            if index == -1:
                LOGERR('Empty database')
                return False

        rec = self.get_rec_by_id(index)
        if not rec:
            LOGERR('No matching index %d', index)
            return False

        # If reading from DB, show empty title and desc as empty lines. We have to convert because
        # even in case of add with a blank title or desc, '' is used as initializer to show '-'.
        result = edit_rec(editor, rec[1], rec[2] if rec[2] != '' else None,
                          rec[3], rec[4] if rec[4] != '' else None)
        if result is not None:
            url, title, tags, desc = result
            return self.update_rec(index, url, title, tags, desc, immutable)

        if immutable != -1:
            return self.update_rec(index, immutable)

        return False

    def list_using_id(self, ids=[]):
        """List entries in the DB using the specified id list.

        Parameters
        ----------
        ids : list of ids in string form

        Returns
        -------
        list
        """
        q0 = 'SELECT * FROM bookmarks'
        if ids:
            q0 += ' WHERE id in ('
            for idx in ids:
                if '-' in idx:
                    val = idx.split('-')
                    if val[0]:
                        part_ids = list(map(int, val))
                        part_ids[1] += 1
                        part_ids = list(range(*part_ids))
                    else:
                        end = int(val[1])
                        qtemp = 'SELECT id FROM bookmarks ORDER BY id DESC limit {0}'.format(end)
                        self.cur.execute(qtemp, [])
                        part_ids = list(chain.from_iterable(self.cur.fetchall()))
                    q0 += ','.join(list(map(str, part_ids)))
                else:
                    q0 += idx + ','
            q0 = q0.rstrip(',')
            q0 += ')'

        try:
            self.cur.execute(q0, [])
        except sqlite3.OperationalError as e:
            LOGERR(e)
            return None
        return self.cur.fetchall()

    def searchdb(
            self,
            keywords: List[str],
            all_keywords: Optional[bool] = False,
            deep: Optional[bool] = False,
            regex: Optional[bool] = False
    ) -> Optional[Iterable[Any]]:
        """Search DB for entries where tags, URL, or title fields match keywords.

        Parameters
        ----------
        keywords : list of str
            Keywords to search.
        all_keywords : bool, optional
            True to return records matching ALL keywords.
            False (default value) to return records matching ANY keyword.
        deep : bool, optional
            True to search for matching substrings. Default is False.
        regex : bool, optional
            Match a regular expression if True. Default is False.

        Returns
        -------
        list or None
            List of search results, or None if no matches.
        """
        if not keywords:
            return None

        # Deep query string
        q1 = ("(tags LIKE ('%' || ? || '%') OR "
              "URL LIKE ('%' || ? || '%') OR "
              "metadata LIKE ('%' || ? || '%') OR "
              "desc LIKE ('%' || ? || '%')) ")
        # Non-deep query string
        q2 = ('(tags REGEXP ? OR '
              'URL REGEXP ? OR '
              'metadata REGEXP ? OR '
              'desc REGEXP ?) ')
        qargs = []  # type: List[Any]

        case_statement = lambda x: 'CASE WHEN ' + x + ' THEN 1 ELSE 0 END'
        if regex:
            q0 = 'SELECT id, url, metadata, tags, desc, flags FROM (SELECT *, '
            for token in keywords:
                if not token:
                    continue

                q0 += case_statement(q2) + ' + '
                qargs += (token, token, token, token,)

            if not qargs:
                return None

            q0 = q0[:-3] + ' AS score FROM bookmarks WHERE score > 0 ORDER BY score DESC)'
        elif all_keywords:
            if len(keywords) == 1 and keywords[0] == 'blank':
                q0 = "SELECT * FROM bookmarks WHERE metadata = '' OR tags = ? "
                qargs += (DELIM,)
            elif len(keywords) == 1 and keywords[0] == 'immutable':
                q0 = 'SELECT * FROM bookmarks WHERE flags & 1 == 1 '
            else:
                q0 = 'SELECT id, url, metadata, tags, desc, flags FROM bookmarks WHERE '
                for token in keywords:
                    if not token:
                        continue

                    if deep:
                        q0 += q1 + 'AND '
                    else:
                        _pre = _post = ''
                        if str.isalnum(token[0]):
                            _pre = '\\b'
                        if str.isalnum(token[-1]):
                            _post = '\\b'
                        token = _pre + re.escape(token.rstrip('/')) + _post
                        q0 += q2 + 'AND '

                    qargs += (token, token, token, token,)

                if not qargs:
                    return None

                q0 = q0[:-4]
            q0 += 'ORDER BY id ASC'
        elif not all_keywords:
            q0 = 'SELECT id, url, metadata, tags, desc, flags FROM (SELECT *, '
            for token in keywords:
                if not token:
                    continue

                if deep:
                    q0 += case_statement(q1) + ' + '
                else:
                    _pre = _post = ''
                    if str.isalnum(token[0]):
                        _pre = '\\b'
                    if str.isalnum(token[-1]):
                        _post = '\\b'
                    token = _pre + re.escape(token.rstrip('/')) + _post
                    q0 += case_statement(q2) + ' + '

                qargs += (token, token, token, token,)

            if not qargs:
                return None

            q0 = q0[:-3] + ' AS score FROM bookmarks WHERE score > 0 ORDER BY score DESC)'
        else:
            LOGERR('Invalid search option')
            return None

        LOGDBG('query: "%s", args: %s', q0, qargs)

        try:
            self.cur.execute(q0, qargs)
        except sqlite3.OperationalError as e:
            LOGERR(e)
            return None

        return self.cur.fetchall()

    def search_by_tag(self, tags: Optional[str]) -> Optional[List[BookmarkVar]]:
        """Search bookmarks for entries with given tags.

        Parameters
        ----------
        tags : str
            String of tags to search for.
            Retrieves entries matching ANY tag if tags are
            delimited with ','.
            Retrieves entries matching ALL tags if tags are
            delimited with '+'.

        Returns
        -------
        list or None
            List of search results, or None if no matches.
        """

        LOGDBG(tags)
        if tags is None or tags == DELIM or tags == '':
            return None

        tags_, search_operator, excluded_tags = prep_tag_search(tags)
        if search_operator is None:
            LOGERR("Cannot use both '+' and ',' in same search")
            return None

        LOGDBG('tags: %s', tags_)
        LOGDBG('search_operator: %s', search_operator)
        LOGDBG('excluded_tags: %s', excluded_tags)

        if search_operator == 'AND':
            query = ("SELECT id, url, metadata, tags, desc, flags FROM bookmarks "
                     "WHERE tags LIKE '%' || ? || '%' ")
            for tag in tags_[1:]:
                query += "{} tags LIKE '%' || ? || '%' ".format(search_operator)

            if excluded_tags:
                tags_.append(excluded_tags)
                query = query.replace('WHERE tags', 'WHERE (tags')
                query += ') AND tags NOT REGEXP ? '
            query += 'ORDER BY id ASC'
        else:
            query = 'SELECT id, url, metadata, tags, desc, flags FROM (SELECT *, '
            case_statement = "CASE WHEN tags LIKE '%' || ? || '%' THEN 1 ELSE 0 END"
            query += case_statement

            for tag in tags_[1:]:
                query += ' + ' + case_statement

            query += ' AS score FROM bookmarks WHERE score > 0'

            if excluded_tags:
                tags_.append(excluded_tags)
                query += ' AND tags NOT REGEXP ? '

            query += ' ORDER BY score DESC)'

        LOGDBG('query: "%s", args: %s', query, tags_)
        self.cur.execute(query, tuple(tags_, ))
        return self.cur.fetchall()

    def search_keywords_and_filter_by_tags(
            self,
            keywords: List[str],
            all_keywords: bool,
            deep: bool,
            regex: bool,
            stag: str) -> Optional[List[BookmarkVar]]:
        """Search bookmarks for entries with keywords and specified
        criteria while filtering out entries with matching tags.

        Parameters
        ----------
        keywords : list of str
            Keywords to search.
        all_keywords : bool, optional
            True to return records matching ALL keywords.
            False to return records matching ANY keyword.
        deep : bool, optional
            True to search for matching substrings.
        regex : bool, optional
            Match a regular expression if True.
        stag : str
            String of tags to search for.
            Retrieves entries matching ANY tag if tags are
            delimited with ','.
            Retrieves entries matching ALL tags if tags are
            delimited with '+'.

        Returns
        -------
        list or None
            List of search results, or None if no matches.
        """

        keyword_results = self.searchdb(keywords, all_keywords, deep, regex)
        keyword_results = keyword_results if keyword_results is not None else []
        stag_results = self.search_by_tag(''.join(stag))
        stag_results = stag_results if stag_results is not None else []
        return list(set(keyword_results) & set(stag_results))

    def exclude_results_from_search(self, search_results, without, deep):
        """Excludes records that match keyword search using without parameters

        Parameters
        ----------
        search_results : list
            List of search results
        without : list of str
            Keywords to search.
        deep : bool, optional
            True to search for matching substrings.

        Returns
        -------
        list or None
            List of search results, or None if no matches.
        """

        return list(set(search_results) - set(self.searchdb(without, False, deep)))

    def compactdb(self, index: int, delay_commit: bool = False):
        """When an entry at index is deleted, move the
        last entry in DB to index, if index is lesser.

        Parameters
        ----------
        index : int
            DB index of deleted entry.
        delay_commit : bool, optional
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.
        """

        # Return if the last index left in DB was just deleted
        max_id = self.get_max_id()
        if max_id == -1:
            return

        query1 = 'SELECT id, URL, metadata, tags, desc, flags FROM bookmarks WHERE id = ? LIMIT 1'
        query2 = 'DELETE FROM bookmarks WHERE id = ?'
        query3 = 'INSERT INTO bookmarks(id, URL, metadata, tags, desc, flags) VALUES (?, ?, ?, ?, ?, ?)'

        # NOOP if the just deleted index was the last one
        if max_id > index:
            self.cur.execute(query1, (max_id,))
            results = self.cur.fetchall()
            for row in results:
                self.cur.execute(query2, (row[0],))
                self.cur.execute(query3, (index, row[1], row[2], row[3], row[4], row[5]))
                if not delay_commit:
                    self.conn.commit()
                if self.chatty:
                    print('Index %d moved to %d' % (row[0], index))

    def delete_rec(
            self,
            index: int,
            low: int = 0,
            high: int = 0,
            is_range: bool = False,
            delay_commit: bool = False
    ) -> bool:
        """Delete a single record or remove the table if index is None.

        Parameters
        ----------
        index : int
            DB index of deleted entry.
        low : int, optional
            Actual lower index of range.
        high : int, optional
            Actual higher index of range.
        is_range : bool, optional
            A range is passed using low and high arguments.
            An index is ignored if is_range is True (use dummy index).
            Default is False.
        delay_commit : bool, optional
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.

        Raises
        ------
        TypeError
            If any of index, low, or high variable is not integer.

        Returns
        -------
        bool
            True on success, False on failure.
        """

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
                if self.chatty:
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
                self.cur.execute(query, (low, high))
                print('Index %d-%d: %d deleted' % (low, high, self.cur.rowcount))
                if not self.cur.rowcount:
                    return False

                # Compact DB by ascending order of index to ensure
                # the existing higher indices move only once
                # Delayed commit is forced
                for index in range(low, high + 1):
                    self.compactdb(index, delay_commit=True)

                if not delay_commit:
                    self.conn.commit()
            except IndexError:
                LOGERR('No matching index')
                return False
        elif index == 0:  # Remove the table
            return self.cleardb()
        else:  # Remove a single entry
            try:
                if self.chatty:
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

                query = 'DELETE FROM bookmarks WHERE id = ?'
                self.cur.execute(query, (index,))
                if self.cur.rowcount == 1:
                    print('Index %d deleted' % index)
                    self.compactdb(index, delay_commit=True)
                    if not delay_commit:
                        self.conn.commit()
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

    def delete_resultset(self, results):
        """Delete search results in descending order of DB index.

        Indices are expected to be unique and in ascending order.

        Notes
        -----
            This API forces a delayed commit.

        Parameters
        ----------
        results : list of tuples
            List of results to delete from DB.

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
        pos = len(results) - 1
        while pos >= 0:
            idx = results[pos][0]
            self.delete_rec(idx, delay_commit=True)

            # Commit at every 200th removal
            if pos % 200 == 0:
                self.conn.commit()

            pos -= 1

        return True

    def delete_rec_all(self, delay_commit=False):
        """Removes all records in the Bookmarks table.

        Parameters
        ----------
        delay_commit : bool, optional
            True if record should not be committed to the DB,
            leaving commit responsibility to caller. Default is False.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        try:
            self.cur.execute('DELETE FROM bookmarks')
            if not delay_commit:
                self.conn.commit()
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
            self.cur.execute('VACUUM')
            self.conn.commit()
            print('All bookmarks deleted')
            return True

        return False

    def print_rec(self, index=0, low=0, high=0, is_range=False):
        """Print bookmark details at index or all bookmarks if index is 0.

        A negative index behaves like tail, if title is blank show "Untitled".

        Parameters
        -----------
        index : int, optional
            DB index of record to print. 0 prints all records.
        low : int, optional
            Actual lower index of range.
        high : int, optional
            Actual higher index of range.
        is_range : bool, optional
            A range is passed using low and high arguments.
            An index is ignored if is_range is True (use dummy index).
            Default is False.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        if index < 0:
            # Show the last n records
            _id = self.get_max_id()
            if _id == -1:
                LOGERR('Empty database')
                return False

            low = (1 if _id <= -index else _id + index + 1)
            high = _id
            is_range = True

        if is_range:
            if low < 0 or high < 0:
                LOGERR('Negative range boundary')
                return False

            if low > high:
                low, high = high, low

            try:
                # If range starts from 0 print all records
                if low == 0:
                    query = 'SELECT * from bookmarks'
                    resultset = self.cur.execute(query)
                else:
                    query = 'SELECT * from bookmarks where id BETWEEN ? AND ?'
                    resultset = self.cur.execute(query, (low, high))
            except IndexError:
                LOGERR('Index out of range')
                return False
        elif index != 0:  # Show record at index
            try:
                query = 'SELECT * FROM bookmarks WHERE id = ? LIMIT 1'
                self.cur.execute(query, (index,))
                results = self.cur.fetchall()
                if not results:
                    LOGERR('No matching index %d', index)
                    return False
            except IndexError:
                LOGERR('No matching index %d', index)
                return False

            if self.json is None:
                print_rec_with_filter(results, self.field_filter)
            elif self.json:
                write_string_to_file(format_json(results, True, self.field_filter), self.json)
            else:
                print(format_json(results, True, self.field_filter))

            return True
        else:  # Show all entries
            self.cur.execute('SELECT * FROM bookmarks')
            resultset = self.cur.fetchall()

        if not resultset:
            LOGERR('0 records')
            return True

        if self.json is None:
            print_rec_with_filter(resultset, self.field_filter)
        elif self.json:
            write_string_to_file(format_json(resultset, field_filter=self.field_filter), self.json)
        else:
            print(format_json(resultset, field_filter=self.field_filter))

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
            print('%d. %s' % (count + 1, unique_tags[count]))

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

    def replace_tag(self, orig: str, new: Optional[List[str]] = None) -> bool:
        """Replace original tag by new tags in all records.

        Remove original tag if new tag is empty.

        Parameters
        ----------
        orig : str
            Original tag.
        new : list
            Replacement tags.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        newtags = DELIM

        orig = delim_wrap(orig)
        if new is not None:
            newtags = parse_tags(new)

        if orig == newtags:
            print('Tags are same.')
            return False

        # Remove original tag from DB if new tagset reduces to delimiter
        if newtags == DELIM:
            return self.delete_tag_at_index(0, orig)

        # Update bookmarks with original tag
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

        return True

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
            qry = 'SELECT id from bookmarks ORDER BY RANDOM() LIMIT 1'
            self.cur.execute(qry)
            result = self.cur.fetchone()

            # Return if no entries in DB
            if result is None:
                print('No bookmarks added yet ...')
                return False

            index = result[0]
            LOGDBG('Opening random index %d', index)

        qry = 'SELECT URL FROM bookmarks WHERE id = ? LIMIT 1'
        try:
            for row in self.cur.execute(qry, (index,)):
                browse(row[0])
                return True
            LOGERR('No matching index %d', index)
        except IndexError:
            LOGERR('No matching index %d', index)

        return False

    def exportdb(self, filepath: str, resultset: Optional[List[BookmarkVar]] = None) -> bool:
        """Export DB bookmarks to file.
        Exports full DB, if resultset is None

        If destination file name ends with '.db', bookmarks are
        exported to a buku database file.
        If destination file name ends with '.md', bookmarks are
        exported to a Markdown file.
        If destination file name ends with '.org' bookmarks are
        exported to a org file.
        Otherwise, bookmarks are exported to a Firefox bookmarks.html
        formatted file.

        Parameters
        ----------
        filepath : str
            Path to export destination file.
        resultset : list of tuples
            List of results to export.


        Returns
        -------
        bool
            True on success, False on failure.
        """

        count = 0

        if not resultset:
            resultset = self.get_rec_all()
            if not resultset:
                print('No records found')
                return False

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
                outdb.cur.execute(qry, (row[1], row[2], row[3], row[4], row[5]))
                count += 1
            outdb.conn.commit()
            outdb.close()
            print('%s exported' % count)
            return True

        try:
            outfp = open(filepath, mode='w', encoding='utf-8')
        except Exception as e:
            LOGERR(e)
            return False

        res = {}  # type: Dict
        if filepath.endswith('.md'):
            res = convert_bookmark_set(resultset, 'markdown')
            count += res['count']
            outfp.write(res['data'])
        elif filepath.endswith('.org'):
            res = convert_bookmark_set(resultset, 'org')
            count += res['count']
            outfp.write(res['data'])
        else:
            res = convert_bookmark_set(resultset, 'html')
            count += res['count']
            outfp.write(res['data'])
        outfp.close()
        print('%s exported' % count)
        return True

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
                next_folder_name = folder_name + ',' + item['name']
                for i in self.traverse_bm_folder(
                        item['children'],
                        unique_tag,
                        next_folder_name,
                        add_parent_folder_as_tag):
                    yield i
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

            formatted_tags = [DELIM + tag for tag in bookmark_tags]
            tags = parse_tags(formatted_tags)

            # get the title
            if row[2]:
                title = row[2]
            else:
                title = ''

            self.add_rec(url, title, tags, None, 0, True, False)
        try:
            cur.close()
            conn.close()
        except Exception as e:
            LOGERR(e)

    def auto_import_from_browser(self):
        """Import bookmarks from a browser default database file.

        Supports Firefox and Google Chrome.

        Returns
        -------
        bool
            True on success, False on failure.
        """

        ff_bm_db_path = None

        if sys.platform.startswith(('linux', 'freebsd', 'openbsd')):
            gc_bm_db_path = '~/.config/google-chrome/Default/Bookmarks'
            cb_bm_db_path = '~/.config/chromium/Default/Bookmarks'

            default_ff_folder = os.path.expanduser('~/.mozilla/firefox')
            profile = get_firefox_profile_name(default_ff_folder)
            if profile:
                ff_bm_db_path = '~/.mozilla/firefox/{}/places.sqlite'.format(profile)
        elif sys.platform == 'darwin':
            gc_bm_db_path = '~/Library/Application Support/Google/Chrome/Default/Bookmarks'
            cb_bm_db_path = '~/Library/Application Support/Chromium/Default/Bookmarks'

            default_ff_folder = os.path.expanduser('~/Library/Application Support/Firefox')
            profile = get_firefox_profile_name(default_ff_folder)
            if profile:
                ff_bm_db_path = ('~/Library/Application Support/Firefox/'
                                 '{}/places.sqlite'.format(profile))
        elif sys.platform == 'win32':
            username = os.getlogin()
            gc_bm_db_path = ('C:/Users/{}/AppData/Local/Google/Chrome/User Data/'
                             'Default/Bookmarks'.format(username))
            cb_bm_db_path = ('C:/Users/{}/AppData/Local/Chromium/User Data/'
                             'Default/Bookmarks'.format(username))

            default_ff_folder = 'C:/Users/{}/AppData/Roaming/Mozilla/Firefox/'.format(username)
            profile = get_firefox_profile_name(default_ff_folder)
            if profile:
                ff_bm_db_path = os.path.join(default_ff_folder, '{}/places.sqlite'.format(profile))
        else:
            LOGERR('buku does not support {} yet'.format(sys.platform))
            self.close_quit(1)

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
        add_parent_folder_as_tag = (resp == 'y')

        resp = 'y'

        try:
            if self.chatty:
                resp = input('Import bookmarks from google chrome? (y/n): ')
            if resp == 'y':
                bookmarks_database = os.path.expanduser(gc_bm_db_path)
                if not os.path.exists(bookmarks_database):
                    raise FileNotFoundError
                self.load_chrome_database(bookmarks_database, newtag, add_parent_folder_as_tag)
        except Exception as e:
            LOGERR(e)
            print('Could not import bookmarks from google-chrome')

        try:
            if self.chatty:
                resp = input('Import bookmarks from chromium? (y/n): ')
            if resp == 'y':
                bookmarks_database = os.path.expanduser(cb_bm_db_path)
                if not os.path.exists(bookmarks_database):
                    raise FileNotFoundError
                self.load_chrome_database(bookmarks_database, newtag, add_parent_folder_as_tag)
        except Exception as e:
            LOGERR(e)
            print('Could not import bookmarks from chromium')

        try:
            if self.chatty:
                resp = input('Import bookmarks from Firefox? (y/n): ')
            if resp == 'y':
                bookmarks_database = os.path.expanduser(ff_bm_db_path)
                if not os.path.exists(bookmarks_database):
                    raise FileNotFoundError
                self.load_firefox_database(bookmarks_database, newtag, add_parent_folder_as_tag)
        except Exception as e:
            LOGERR(e)
            print('Could not import bookmarks from Firefox.')

        self.conn.commit()

        if newtag:
            print('\nAuto-generated tag: %s' % newtag)

    def importdb(self, filepath, tacit=False):
        """Import bookmarks from a HTML or a Markdown file.

        Supports Firefox, Google Chrome, and IE exported HTML bookmarks.
        Supports Markdown files with extension '.md, .org'.
        Supports importing bookmarks from another buku database file.

        Parameters
        ----------
        filepath : str
            Path to file to import.
        tacit : bool, optional
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
        elif filepath.endswith('json'):
            if not tacit:
                resp = input('Add parent folder names as tags? (y/n): ')
            else:
                resp = 'y'
            add_bookmark_folder_as_tag = (resp == 'y')
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

            if not tacit:
                resp = input('Add parent folder names as tags? (y/n): ')
            else:
                resp = 'y'

            add_parent_folder_as_tag = (resp == 'y')
            items = import_html(soup, add_parent_folder_as_tag, newtag)
            infp.close()

        for item in items:
            add_rec_res = self.add_rec(*item)
            if add_rec_res == -1 and append_tags_resp == 'y':
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
            for row in resultset:
                self.add_rec(row[1], row[2], row[3], row[4], row[5], True, False)

            self.conn.commit()

        try:
            indb_cur.close()
            indb_conn.close()
        except Exception:
            pass

        return True

    def tnyfy_url(
            self,
            index: Optional[int] = 0,
            url: Optional[str] = None,
            shorten: Optional[bool] = True) -> Optional[str]:
        """Shorten a URL using Google URL shortener.

        Parameters
        ----------
        index : int, optional (if URL is provided)
            DB index of the bookmark with the URL to shorten. Default is 0.
        url : str, optional (if index is provided)
            URL to shorten.
        shorten : bool, optional
            True to shorten, False to expand. Default is False.

        Returns
        -------
        str
            Shortened url on success, None on failure.
        """

        global MYPROXY

        if not index and not url:
            LOGERR('Either a valid DB index or URL required')
            return None

        if index:
            self.cur.execute('SELECT url FROM bookmarks WHERE id = ? LIMIT 1', (index,))
            results = self.cur.fetchall()
            if not results:
                return None

            url = results[0][0]

        from urllib.parse import quote_plus as qp

        url = url if url is not None else ''
        urlbase = 'https://tny.im/yourls-api.php?action='
        if shorten:
            _u = urlbase + 'shorturl&format=simple&url=' + qp(url)
        else:
            _u = urlbase + 'expand&format=simple&shorturl=' + qp(url)

        if MYPROXY is None:
            gen_headers()

        ca_certs = os.getenv('BUKU_CA_CERTS', default=certifi.where())
        if MYPROXY:
            manager = urllib3.ProxyManager(
                MYPROXY,
                num_pools=1,
                headers=MYHEADERS,
                cert_reqs='CERT_REQUIRED',
                ca_certs=ca_certs)
        else:
            manager = urllib3.PoolManager(num_pools=1,
                                          headers={'User-Agent': USER_AGENT},
                                          cert_reqs='CERT_REQUIRED',
                                          ca_certs=ca_certs)

        try:
            r = manager.request(
                'POST',
                _u,
                headers={
                    'content-type': 'application/json',
                    'User-Agent': USER_AGENT}
            )
        except Exception as e:
            LOGERR(e)
            manager.clear()
            return None

        if r.status != 200:
            LOGERR('[%s] %s', r.status, r.reason)
            return None

        manager.clear()

        return r.data.decode(errors='replace')

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
        exitval : int, optional
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

    @staticmethod
    def program_info(file=sys.stdout):
        """Print program info.

        Parameters
        ----------
        file : file, optional
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
Copyright © 2015-2021 %s
License: %s
Webpage: https://github.com/jarun/buku
''' % (__version__, __author__, __license__))

    @staticmethod
    def prompt_help(file=sys.stdout):
        """Print prompt help.

        Parameters
        ----------
        file : file, optional
            File to write program info to. Default is sys.stdout.
        """
        file.write('''
PROMPT KEYS:
    1-N                    browse search result indices and/or ranges
    O [id|range [...]]     open search results/indices in GUI browser
                           toggle try GUI browser if no arguments
    a                      open all results in browser
    s keyword [...]        search for records with ANY keyword
    S keyword [...]        search for records with ALL keywords
    d                      match substrings ('pen' matches 'opened')
    r expression           run a regex search
    t [tag, ...]           search by tags; show taglist, if no args
    g taglist id|range [...] [>>|>|<<] [record id|range ...]
                           append, set, remove (all or specific) tags
                           search by taglist id(s) if records are omitted
    n                      show next page of search results
    o id|range [...]       browse bookmarks by indices and/or ranges
    p id|range [...]       print bookmarks by indices and/or ranges
    w [editor|id]          edit and add or update a bookmark
    c id                   copy url at search result index to clipboard
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
        file : file, optional
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
        buku_tags = list(
            sorted(set(map(lambda x: x.replace(' ', '_'), buku_tags)), reverse=False))
        if buku_tags:
            return ' :{}:\n'.format(':'.join(buku_tags))
    return '\n'


def convert_bookmark_set(
        bookmark_set: List[BookmarkVar],
        export_type: str) -> ConverterResult:  # type: ignore
    """Convert list of bookmark set into multiple data format.

    Parameters
    ----------
        bookmark_set: bookmark set
        export type: one of supported type: markdown, html, org

    Returns
    -------
        converted data and count of converted bookmark set
    """
    assert export_type in ['markdown', 'html', 'org']
    #  compatibility
    resultset = bookmark_set

    count = 0
    out = ''
    if export_type == 'markdown':
        for row in resultset:
            if not row[2] or row[2] is None:
                out += '- [Untitled](' + row[1] + ')'
            else:
                out += '- [' + row[2] + '](' + row[1] + ')'

            if row[3] != DELIM:
                out += ' <!-- TAGS: {} -->\n'.format(row[3][1:-1])
            else:
                out += '\n'

            count += 1
    elif export_type == 'org':
        for row in resultset:
            if not row[2]:
                out += '* [[{}][Untitled]]'.format(row[1])
            else:
                out += '* [[{}][{}]]'.format(row[1], row[2])
            out += convert_tags_to_org_mode_tags(row[3])
            count += 1
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
            out += '        <DT><A HREF="%s" ADD_DATE="%s" LAST_MODIFIED="%s"' % (row[1], timestamp, timestamp)
            if row[3] != DELIM:
                out += ' TAGS="' + row[3][1:-1] + '"'
            out += '>{}</A>\n'.format(row[2] if row[2] else '')
            if row[4] != '':
                out += '        <DD>' + row[4] + '\n'
            count += 1

        out += '    </DL><p>\n</DL><p>'

    return {'data': out, 'count': count}


def get_firefox_profile_name(path):
    """List folder and detect default Firefox profile name.

    Returns
    -------
    profile : str
        Firefox profile name.
    """
    from configparser import ConfigParser, NoOptionError

    profile_path = os.path.join(path, 'profiles.ini')
    if os.path.exists(profile_path):
        config = ConfigParser()
        config.read(profile_path)

        install_names = [section for section in config.sections() if section.startswith('Install')]
        for name in install_names:
            try:
                profile_path = config.get(name, 'default')
                return profile_path
            except NoOptionError:
                pass

        profiles_names = [section for section in config.sections() if section.startswith('Profile')]
        if not profiles_names:
            return None
        for name in profiles_names:
            try:
                # If profile is default
                if config.getboolean(name, 'default'):
                    profile_path = config.get(name, 'path')
                    return profile_path
            except NoOptionError:
                pass
            try:
                # alternative way to detect default profile
                if config.get(name, 'name').lower() == "default":
                    profile_path = config.get(name, 'path')
                    return profile_path
            except NoOptionError:
                pass

        # There is no default profile
        return None
    LOGDBG('get_firefox_profile_name(): {} does not exist'.format(path))
    return None


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
    with open(filepath, mode='r', encoding='utf-8') as infp:
        for line in infp:
            # Supported Markdown format: [title](url)
            # Find position of title end, url start delimiter combo
            index = line.find('](')
            if index != -1:
                # Find title start delimiter
                title_start_delim = line[:index].find('[')
                # Reverse find the url end delimiter
                url_end_delim = line[index + 2:].rfind(')')

                if title_start_delim != -1 and url_end_delim > 0:
                    # Parse title
                    title = line[title_start_delim + 1:index]
                    # Parse url
                    url = line[index + 2:index + 2 + url_end_delim]
                    if is_nongeneric_url(url):
                        continue

                    yield (url, title, delim_wrap(newtag), None, 0, True)

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
        tag_list_raw = [i for i in re.split(r'(?<!\:)\:', tag_string) if i]
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

    with open(filepath, mode='r', encoding='utf-8') as infp:
        # Supported Markdown format: * [[url][title]] :tags:
        # Find position of url end, title start delimiter combo
        for line in infp:
            index = line.find('][')
            if index != -1:
                # Find url start delimiter
                url_start_delim = line[:index].find('[[')
                # Reverse find title end delimiter
                title_end_delim = line[index + 2:].rfind(']]')

                if url_start_delim != -1 and title_end_delim > 0:
                    # Parse title
                    title = line[index + 2: index + 2 + title_end_delim]
                    # Parse url
                    url = line[url_start_delim + 2:index]
                    # Parse Tags
                    tags = list(collections.OrderedDict.fromkeys(get_org_tags(line[(index + 4 + title_end_delim):])))
                    tags_string = DELIM.join(tags)

                    if is_nongeneric_url(url):
                        continue

                    if newtag:
                        if newtag.lower() not in tags:
                            tags_string = (newtag + DELIM) + tags_string

                    yield (url, title, delim_wrap(tags_string), None, 0, True)

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


def import_html(html_soup, add_parent_folder_as_tag, newtag):
    """Parse bookmark HTML.

    Parameters
    ----------
    html_soup : BeautifulSoup object
        BeautifulSoup representation of bookmark HTML.
    add_parent_folder_as_tag : bool
        True if bookmark parent folders should be added as tags else False.
    newtag : str
        A new unique tag to add to imported bookmarks.

    Returns
    -------
    tuple
        Parsed result.
    """

    # compatibility
    soup = html_soup

    for tag in soup.findAll('a'):
        # Extract comment from <dd> tag
        try:
            if is_nongeneric_url(tag['href']):
                continue
        except KeyError:
            continue

        desc = None
        comment_tag = tag.findNextSibling('dd')

        if comment_tag:
            desc = comment_tag.find(text=True, recursive=False)

        # add parent folder as tag
        if add_parent_folder_as_tag:
            # could be its folder or not
            possible_folder = tag.find_previous('h3')
            # get list of tags within that folder
            tag_list = tag.parent.parent.find_parent('dl')

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
            tag['href'], tag.string,
            parse_tags([tag['tags']]) if tag.has_attr('tags') else None,
            desc if not desc else desc.strip(), 0, True, False
        )


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

    # Get the netloc token
    try:
        netloc = parse_url(url).netloc
        if not netloc:
            # Try of prepend '//' and get netloc
            netloc = parse_url('//' + url).netloc
            if not netloc:
                return True
    except LocationParseError as e:
        LOGERR('%s, URL: %s', e, url)
        return True

    LOGDBG('netloc: %s', netloc)

    # netloc cannot start or end with a '.'
    if netloc.startswith('.') or netloc.endswith('.'):
        return True

    # netloc should have at least one '.'
    if netloc.rfind('.') < 0:
        return True

    return False


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

    title = None
    desc = None
    keys = None

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
            keys = re.sub(r'\s{2,}', ' ', keys)
            if is_unusual_tag(keys):
                if keys not in (title, desc):
                    LOGDBG('keywords to description: %s', keys)
                    if desc:
                        desc = desc + '\n## ' + keys
                    else:
                        desc = '* ' + keys

                keys = None
    except Exception as e:
        LOGDBG(e)

    LOGDBG('title: %s', title)
    LOGDBG('desc : %s', desc)
    LOGDBG('keys : %s', keys)

    return (title, desc, keys)


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
        soup = BeautifulSoup(resp.data, 'html.parser')
    except Exception as e:
        LOGERR('get_data_from_page(): %s', e)

    try:
        charset = None

        if soup.meta and soup.meta.get('charset') is not None:
            charset = soup.meta.get('charset')
        elif 'content-type' in resp.headers:
            _, params = cgi.parse_header(resp.headers['content-type'])
            if params.get('charset') is not None:
                charset = params.get('charset')

        if not charset and soup:
            meta_tag = soup.find('meta', attrs={'http-equiv': 'Content-Type'})
            if meta_tag:
                _, params = cgi.parse_header(meta_tag.attrs['content'])
                charset = params.get('charset', charset)

        if charset:
            LOGDBG('charset: %s', charset)
            title, desc, keywords = parse_decoded_page(resp.data.decode(charset, errors='replace'))
        else:
            title, desc, keywords = parse_decoded_page(resp.data.decode(errors='replace'))

        return (title, desc, keywords)
    except Exception as e:
        LOGERR(e)
        return (None, None, None)


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
            url = parse_url(MYPROXY)
        except Exception as e:
            LOGERR(e)
            return

        # Strip username and password (if present) and update headers
        if url.auth:
            MYPROXY = MYPROXY.replace(url.auth + '@', '')
            auth_headers = make_headers(basic_auth=url.auth)
            MYHEADERS.update(auth_headers)

        LOGDBG('proxy: [%s]', MYPROXY)


def get_PoolManager():
    """Creates a pool manager with proxy support, if applicable.

    Returns
    -------
    ProxyManager or PoolManager
        ProxyManager if https_proxy is defined, PoolManager otherwise.
    """
    ca_certs = os.getenv('BUKU_CA_CERTS', default=certifi.where())
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
        http_head: Optional[bool] = False
) -> Tuple[Optional[str], Optional[str], Optional[str], int, int]:
    """Handle server connection and redirections.

    Parameters
    ----------
    url : str
        URL to fetch.
    http_head : bool
        If True, send only HTTP HEAD request. Default is False.

    Returns
    -------
    tuple
        (title, description, tags, recognized mime, bad url).
    """

    page_title = None
    page_desc = None
    page_keys = None
    exception = False

    if is_nongeneric_url(url) or is_bad_url(url):
        return (None, None, None, 0, 1)

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

            if resp.status == 200:
                if method == 'GET':
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
                LOGERR('[%s] %s', resp.status, resp.reason)

            if resp:
                resp.close()

            break
    except Exception as e:
        LOGERR('network_handler(): %s', e)
        exception = True
    finally:
        if manager:
            manager.clear()
        if exception:
            return (None, None, None, 0, 0)
        if method == 'HEAD':
            return ('', '', '', 1, 0)
        if page_title is None:
            return ('', page_desc, page_keys, 0, 0)

        return (page_title, page_desc, page_keys, 0, 0)


def parse_tags(keywords=[]):
    """Format and get tag string from tokens.

    Parameters
    ----------
    keywords : list, optional
        List of tags to parse. Default is empty list.

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

    if not keywords or len(keywords) < 1 or not keywords[0]:
        return DELIM

    tags = DELIM

    # Cleanse and get the tags
    tagstr = ' '.join(keywords)
    marker = tagstr.find(DELIM)

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

    # original tags in lower case
    orig_tags = tags.lower().strip(DELIM).split(DELIM)

    # Create list of unique tags and sort
    unique_tags = sorted(set(orig_tags))

    # Wrap with delimiter
    return delim_wrap(DELIM.join(unique_tags))


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
    suggest : bool, optional
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


def prompt(obj, results, noninteractive=False, deep=False, listtags=False, suggest=False, num=10):
    """Show each matching result from a search and prompt.

    Parameters
    ----------
    obj : BukuDb instance
        A valid instance of BukuDb class.
    results : list
        Search result set from a DB query.
    noninteractive : bool, optional
        If True, does not seek user input. Shows all results. Default is False.
    deep : bool, optional
        Use deep search. Default is False.
    listtags : bool, optional
        If True, list all tags.
    suggest : bool, optional
        If True, suggest similar tags on edit and add bookmark.
    num : int, optional
        Number of results to show per page. Default is 10.
    """

    if not isinstance(obj, BukuDb):
        LOGERR('Not a BukuDb instance')
        return

    new_results = bool(results)
    nav = ''
    cur_index = next_index = count = 0

    if listtags:
        show_taglist(obj)

    if noninteractive:
        try:
            for row in results:
                count += 1
                print_single_rec(row, count)
        except Exception:
            pass
        finally:
            return

    while True:
        if new_results or nav == 'n':
            count = 0

            if results:
                total_results = len(results)
                cur_index = next_index
                if cur_index < total_results:
                    next_index = min(cur_index + num, total_results)
                    print()
                    for row in results[cur_index:next_index]:
                        count += 1
                        print_single_rec(row, count)
                else:
                    print('No more results')
            else:
                print('0 results')

        try:
            nav = read_in(PROMPTMSG)
            if not nav:
                nav = read_in(PROMPTMSG)
                if not nav:
                    # Quit on double enter
                    break
            nav = nav.strip()
        except EOFError:
            return

        # show the next set of results from previous search
        if nav == 'n':
            continue

        # search ANY match with new keywords
        if nav.startswith('s '):
            results = obj.searchdb(nav[2:].split(), False, deep)
            new_results = True
            cur_index = next_index = 0
            continue

        # search ALL match with new keywords
        if nav.startswith('S '):
            results = obj.searchdb(nav[2:].split(), True, deep)
            new_results = True
            cur_index = next_index = 0
            continue

        # regular expressions search with new keywords
        if nav.startswith('r '):
            results = obj.searchdb(nav[2:].split(), True, regex=True)
            new_results = True
            cur_index = next_index = 0
            continue

        # tag search with new keywords
        if nav.startswith('t '):
            results = obj.search_by_tag(nav[2:])
            new_results = True
            cur_index = next_index = 0
            continue

        # quit with 'q'
        if nav == 'q':
            return

        # No new results fetched beyond this point
        new_results = False

        # toggle deep search with 'd'
        if nav == 'd':
            deep = not deep
            if deep:
                print('deep search on')
            else:
                print('deep search off')

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
            edit_at_prompt(obj, nav, suggest)
            continue

        # Append or overwrite tags
        if nav.startswith('g '):
            unique_tags, dic = obj.get_tag_all()
            _count = obj.set_tag(nav[2:], unique_tags)
            if _count == -1:
                print('Invalid input')
            elif _count == -2:
                try:
                    tagid_list = nav[2:].split()
                    tagstr = obj.get_tagstr_from_taglist(tagid_list, unique_tags)
                    tagstr = tagstr.strip(DELIM)
                    results = obj.search_by_tag(tagstr)
                    new_results = True
                    cur_index = next_index = 0
                except Exception:
                    print('Invalid input')
            else:
                print('%d updated' % _count)
            continue

        # Print bookmarks by DB index
        if nav.startswith('p '):
            id_list = nav[2:].split()
            try:
                for id in id_list:
                    if is_int(id):
                        obj.print_rec(int(id))
                    elif '-' in id:
                        vals = [int(x) for x in id.split('-')]
                        obj.print_rec(0, vals[0], vals[-1], True)
                    else:
                        print('Invalid input')
            except ValueError:
                print('Invalid input')
            continue

        # Browse bookmarks by DB index
        if nav.startswith('o '):
            id_list = nav[2:].split()
            try:
                for id in id_list:
                    if is_int(id):
                        obj.browse_by_index(int(id))
                    elif '-' in id:
                        vals = [int(x) for x in id.split('-')]
                        obj.browse_by_index(0, vals[0], vals[-1], True)
                    else:
                        print('Invalid input')
            except ValueError:
                print('Invalid input')
            continue

        # Copy URL to clipboard
        if nav.startswith('c ') and nav[2:].isdigit():
            index = int(nav[2:]) - 1
            if index < 0 or index >= count:
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
            show_taglist(obj)
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
                if index < 0 or index >= count:
                    print('No matching index %s' % nav)
                    continue
                browse(results[index + cur_index][1])
            elif '-' in nav:
                try:
                    vals = [int(x) for x in nav.split('-')]
                    if vals[0] > vals[-1]:
                        vals[0], vals[-1] = vals[-1], vals[0]

                    for _id in range(vals[0]-1, vals[-1]):
                        if 0 <= _id < count:
                            browse(results[_id + cur_index][1])
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
        Integer indicating which fields to print.
    """

    try:
        if field_filter == 0:
            for row in records:
                print_single_rec(row)
        elif field_filter == 1:
            for row in records:
                print('%s\t%s' % (row[0], row[1]))
        elif field_filter == 2:
            for row in records:
                print('%s\t%s\t%s' % (row[0], row[1], row[3][1:-1]))
        elif field_filter == 3:
            for row in records:
                print('%s\t%s' % (row[0], row[2]))
        elif field_filter == 4:
            for row in records:
                print('%s\t%s\t%s\t%s' % (row[0], row[1], row[2], row[3][1:-1]))
        elif field_filter == 5:
            for row in records:
                print('%s\t%s\t%s' % (row[0], row[2], row[3][1:-1]))
        elif field_filter == 10:
            for row in records:
                print(row[1])
        elif field_filter == 20:
            for row in records:
                print('%s\t%s' % (row[1], row[3][1:-1]))
        elif field_filter == 30:
            for row in records:
                print(row[2])
        elif field_filter == 40:
            for row in records:
                print('%s\t%s\t%s' % (row[1], row[2], row[3][1:-1]))
        elif field_filter == 50:
            for row in records:
                print('%s\t%s' % (row[2], row[3][1:-1]))
    except BrokenPipeError:
        sys.stdout = os.fdopen(1)
        sys.exit(1)


def print_single_rec(row: BookmarkVar, idx: Optional[int] = 0):  # NOQA
    """Print a single DB record.

    Handles both search results and individual record.

    Parameters
    ----------
    row : tuple
        Tuple representing bookmark record data.
    idx : int, optional
        Search result index. If 0, print with DB index.
        Default is 0.
    """

    str_list = []

    # Start with index and title
    if idx != 0:
        id_title_res = ID_STR % (idx, row[2] if row[2] else 'Untitled', row[0])
    else:
        id_title_res = ID_DB_STR % (row[0], row[2] if row[2] else 'Untitled')
        # Indicate if record is immutable
        if row[5] & 1:
            id_title_res = MUTE_STR % (id_title_res)
        else:
            id_title_res += '\n'

    str_list.append(id_title_res)
    str_list.append(URL_STR % (row[1]))
    if row[4]:
        str_list.append(DESC_STR % (row[4]))
    if row[3] != DELIM:
        str_list.append(TAG_STR % (row[3][1:-1]))

    try:
        print(''.join(str_list))
    except UnicodeEncodeError:
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
    single_record : bool, optional
        If True, indicates only one record. Default is False.

    Returns
    -------
    json
        Record(s) in JSON format.
    """

    if single_record:
        marks = {}
        for row in resultset:
            if field_filter == 1:
                marks['uri'] = row[1]
            elif field_filter == 2:
                marks['uri'] = row[1]
                marks['tags'] = row[3][1:-1]
            elif field_filter == 3:
                marks['title'] = row[2]
            elif field_filter == 4:
                marks['uri'] = row[1]
                marks['tags'] = row[3][1:-1]
                marks['title'] = row[2]
            else:
                marks['index'] = row[0]
                marks['uri'] = row[1]
                marks['title'] = row[2]
                marks['description'] = row[4]
                marks['tags'] = row[3][1:-1]
    else:
        marks = []
        for row in resultset:
            if field_filter == 1:
                record = {'uri': row[1]}
            elif field_filter == 2:
                record = {'uri': row[1], 'tags': row[3][1:-1]}
            elif field_filter == 3:
                record = {'title': row[2]}
            elif field_filter == 4:
                record = {'uri': row[1], 'title': row[2], 'tags': row[3][1:-1]}
            else:
                record = {
                    'index': row[0],
                    'uri': row[1],
                    'title': row[2],
                    'description': row[4],
                    'tags': row[3][1:-1]
                }

            marks.append(record)

    return json.dumps(marks, sort_keys=True, indent=4)


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

    if not parse_url(url).scheme:
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

    global MYPROXY

    if MYPROXY is None:
        gen_headers()

    ca_certs = os.getenv('BUKU_CA_CERTS', default=certifi.where())
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
        print('waiting for input')
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

# main starts here
def main():
    """Main."""
    global ID_STR, ID_DB_STR, MUTE_STR, URL_STR, DESC_STR, TAG_STR, PROMPTMSG

    title_in = None
    tags_in = None
    desc_in = None
    pipeargs = []
    colorstr_env = os.getenv('BUKU_COLORS')

    try:
        piped_input(sys.argv, pipeargs)
    except KeyboardInterrupt:
        pass

    # If piped input, set argument vector
    if pipeargs:
        sys.argv = pipeargs

    # Setup custom argument parser
    argparser = ExtendedArgumentParser(
        description='''Bookmark manager like a text-based mini-web.

POSITIONAL ARGUMENTS:
      KEYWORD              search keywords''',
        formatter_class=argparse.RawTextHelpFormatter,
        usage='''buku [OPTIONS] [KEYWORD [KEYWORD ...]]''',
        add_help=False
    )
    hide = argparse.SUPPRESS

    argparser.add_argument('keywords', nargs='*', metavar='KEYWORD', help=hide)

    # ---------------------
    # GENERAL OPTIONS GROUP
    # ---------------------

    general_grp = argparser.add_argument_group(
        title='GENERAL OPTIONS',
        description='''    -a, --add URL [tag, ...]
                         bookmark URL with comma-separated tags
    -u, --update [...]   update fields of an existing bookmark
                         accepts indices and ranges
                         refresh title and desc if no edit options
                         if no arguments:
                         - update results when used with search
                         - otherwise refresh all titles and desc
    -w, --write [editor|index]
                         open editor to edit a fresh bookmark
                         edit last bookmark, if index=-1
                         to specify index, EDITOR must be set
    -d, --delete [...]   remove bookmarks from DB
                         accepts indices or a single range
                         if no arguments:
                         - delete results when used with search
                         - otherwise delete all bookmarks
    -h, --help           show this information and exit
    -v, --version        show the program version and exit''')
    addarg = general_grp.add_argument
    addarg('-a', '--add', nargs='+', help=hide)
    addarg('-u', '--update', nargs='*', help=hide)
    addarg('-w', '--write', nargs='?', const=get_system_editor(), help=hide)
    addarg('-d', '--delete', nargs='*', help=hide)
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
                         N=0: mutable (default), N=1: immutable''')
    addarg = edit_grp.add_argument
    addarg('--url', nargs=1, help=hide)
    addarg('--tag', nargs='*', help=hide)
    addarg('--title', nargs='*', help=hide)
    addarg('-c', '--comment', nargs='*', help=hide)
    addarg('--immutable', type=int, default=-1, choices={0, 1}, help=hide)

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
    -r, --sreg expr      run a regex search
    -t, --stag [tag [,|+] ...] [- tag, ...]
                         search bookmarks by tags
                         use ',' to find entries matching ANY tag
                         use '+' to find entries matching ALL tags
                         excludes entries with tags after ' - '
                         list all tags, if no search keywords
    -x, --exclude [...]  omit records matching specified keywords''')
    addarg = search_grp.add_argument
    addarg('-s', '--sany', nargs='*', help=hide)
    addarg('-S', '--sall', nargs='*', help=hide)
    addarg('-r', '--sreg', nargs='*', help=hide)
    addarg('--deep', action='store_true', help=hide)
    addarg('-t', '--stag', nargs='*', help=hide)
    addarg('-x', '--exclude', nargs='*', help=hide)

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
        description='''    --ai                 auto-import from Firefox/Chrome/Chromium
    -e, --export file    export bookmarks to Firefox format HTML
                         export Markdown, if file ends with '.md'
                         format: [title](url) <!-- TAGS -->
                         export Orgfile, if file ends with '.org'
                         format: *[[url][title]] :tags:
                         export buku DB, if file ends with '.db'
                         combines with search results, if opted
    -i, --import file    import bookmarks based on file extension
                         supports 'html', 'json', 'md', 'org', 'db'
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
    --shorten index|URL  fetch shortened url from tny.im service
    --expand index|URL   expand a tny.im shortened url
    --cached index|URL   browse a cached page from Wayback Machine
    --suggest            show similar tags when adding bookmarks
    --tacit              reduce verbosity, skip some confirmations
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
    addarg('--shorten', nargs=1, help=hide)
    addarg('--expand', nargs=1, help=hide)
    addarg('--cached', nargs=1, help=hide)
    addarg('--suggest', action='store_true', help=hide)
    addarg('--tacit', action='store_true', help=hide)
    addarg('--threads', type=int, default=4, choices=range(1, 11), help=hide)
    addarg('-V', dest='upstream', action='store_true', help=hide)
    addarg('-g', '--debug', action='store_true', help=hide)
    # Undocumented APIs
    # Fix uppercase tags allowed in releases before v2.7
    addarg('--fixtags', action='store_true', help=hide)
    # App-use only, not for manual usage
    addarg('--db', nargs=1, help=hide)

    # Parse the arguments
    args = argparser.parse_args()

    # Show help and exit if help requested
    if args.help:
        argparser.print_help(sys.stdout)
        sys.exit(0)

    # By default, buku uses ANSI colors. As Windows does not really use them,
    # we'd better check for known working console emulators first. Currently,
    # only ConEmu is supported. If the user does not use ConEmu, colors are
    # disabled unless --colors or %BUKU_COLORS% is specified.
    if sys.platform == 'win32' and os.environ.get('ConemuDir') is None:
        if args.colorstr is None and colorstr_env is not None:
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
        TAG_STR = COLORMAP['j'] + '   # ' + setcolors(colorstr)[4] + '%s\n' + COLORMAP['x']

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

    # Fallback to prompt if no arguments
    if len(sys.argv) == 1:
        bdb = BukuDb()
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
        BukuCrypt.encrypt_file(args.lock)
    elif args.unlock is not None:
        BukuCrypt.decrypt_file(args.unlock)

    # Set up title
    if args.title is not None:
        if args.title:
            title_in = ' '.join(args.title)
        else:
            title_in = ''

    # Set up tags
    if args.tag is not None:
        if args.tag:
            tags_in = args.tag
        else:
            tags_in = [DELIM, ]

    # Set up comment
    if args.comment is not None:
        if args.comment:
            desc_in = ' '.join(args.comment)
        else:
            desc_in = ''

    # Initialize the database and get handles, set verbose by default
    bdb = BukuDb(
        args.json,
        args.format,
        not args.tacit,
        dbfile=args.db[0] if args.db is not None else None,
        colorize=not args.nc
    )

    # Editor mode
    if args.write is not None:
        if not is_editor_valid(args.write):
            bdb.close_quit(1)

        if is_int(args.write):
            if not bdb.edit_update_rec(int(args.write), args.immutable):
                bdb.close_quit(1)
        elif args.add is None:
            # Edit and add a new bookmark
            # Parse tags into a comma-separated string
            if tags_in:
                if tags_in[0] == '+':
                    tags = '+' + parse_tags(tags_in[1:])
                elif tags_in[0] == '-':
                    tags = '-' + parse_tags(tags_in[1:])
                else:
                    tags = parse_tags(tags_in)
            else:
                tags = DELIM

            result = edit_rec(args.write, '', title_in, tags, desc_in)
            if result is not None:
                url, title_in, tags, desc_in = result
                if args.suggest:
                    tags = bdb.suggest_similar_tag(tags)
                bdb.add_rec(url, title_in, tags, desc_in, args.immutable)

    # Add record
    if args.add is not None:
        if args.url is not None and args.update is None:
            LOGERR('Bookmark a single URL at a time')
            bdb.close_quit(1)

        # Parse tags into a comma-separated string
        tags = DELIM
        keywords = args.add
        if tags_in is not None:
            if tags_in[0] == '+':
                if len(tags_in) > 1:
                    # The case: buku -a url tag1, tag2 --tag + tag3, tag4
                    tags_in = tags_in[1:]
                    # In case of add, args.add may have URL followed by tags
                    # Add delimiter as url+tags may not end with one
                    keywords = args.add + [DELIM] + tags_in
            else:
                keywords = args.add + [DELIM] + tags_in

        if len(keywords) > 1:  # args.add is URL followed by optional tags
            tags = parse_tags(keywords[1:])

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
            bdb.add_rec(url, title_in, tags, desc_in, args.immutable)

    # Search record
    search_results = None
    search_opted = True
    tags_search = bool(args.stag is not None and len(args.stag))
    exclude_results = bool(args.exclude is not None and len(args.exclude))

    if args.sany is not None:
        if len(args.sany):
            LOGDBG('args.sany')
            # Apply tag filtering, if opted
            if tags_search:
                search_results = bdb.search_keywords_and_filter_by_tags(
                    args.sany, False, args.deep, False, args.stag)
            else:
                # Search URLs, titles, tags for any keyword
                search_results = bdb.searchdb(args.sany, False, args.deep)

            if exclude_results:
                search_results = bdb.exclude_results_from_search(
                    search_results,
                    args.exclude,
                    args.deep
                )
        else:
            LOGERR('no keyword')
    elif args.sall is not None:
        if len(args.sall):
            LOGDBG('args.sall')
            # Apply tag filtering, if opted
            if tags_search:
                search_results = bdb.search_keywords_and_filter_by_tags(
                    args.sall,
                    True,
                    args.deep,
                    False,
                    args.stag
                )
            else:
                # Search URLs, titles, tags with all keywords
                search_results = bdb.searchdb(args.sall, True, args.deep)

            if exclude_results:
                search_results = bdb.exclude_results_from_search(
                    search_results,
                    args.exclude,
                    args.deep
                )
        else:
            LOGERR('no keyword')
    elif args.sreg is not None:
        if len(args.sreg):
            LOGDBG('args.sreg')
            # Apply tag filtering, if opted
            if tags_search:
                search_results = bdb.search_keywords_and_filter_by_tags(
                    args.sreg,
                    False,
                    False,
                    True,
                    args.stag
                )
            else:
                # Run a regular expression search
                search_results = bdb.searchdb(args.sreg, regex=True)

            if exclude_results:
                search_results = bdb.exclude_results_from_search(
                    search_results,
                    args.exclude,
                    args.deep
                )
        else:
            LOGERR('no expression')
    elif len(args.keywords):
        LOGDBG('args.keywords')
        # Apply tag filtering, if opted
        if tags_search:
            search_results = bdb.search_keywords_and_filter_by_tags(
                args.keywords,
                False,
                args.deep,
                False,
                args.stag
            )
        else:
            # Search URLs, titles, tags for any keyword
            search_results = bdb.searchdb(args.keywords, False, args.deep)

        if exclude_results:
            search_results = bdb.exclude_results_from_search(
                search_results,
                args.exclude,
                args.deep
            )
    elif args.stag is not None:
        if len(args.stag):
            LOGDBG('args.stag')
            # Search bookmarks by tag
            search_results = bdb.search_by_tag(' '.join(args.stag))
            if exclude_results:
                search_results = bdb.exclude_results_from_search(
                    search_results,
                    args.exclude,
                    args.deep
                )
        else:
            # Use sub prompt to list all tags
            prompt(bdb, None, args.np, listtags=True, suggest=args.suggest)
    elif args.exclude is not None:
        LOGERR('No search criteria to exclude results from')
    else:
        search_opted = False

    # Add cmdline search options to readline history
    if search_opted and len(args.keywords):
        try:
            readline.add_history(' '.join(args.keywords))
        except Exception:
            pass

    if search_results:
        oneshot = args.np
        update_search_results = False

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

        if args.json is None and not args.format:
            num = 10 if not args.count else args.count
            prompt(bdb, search_results, oneshot, args.deep, num=num)
        elif args.json is None:
            print_rec_with_filter(search_results, field_filter=args.format)
        elif args.json:
            write_string_to_file(format_json(search_results, field_filter=args.format), args.json)
        else:
            # Printing in JSON format is non-interactive
            print(format_json(search_results, field_filter=args.format))

        # Export the results, if opted
        if args.export is not None:
            bdb.exportdb(args.export[0], search_results)

        # In case of search and delete/update,
        # prompt should be non-interactive
        # delete gets priority over update
        if args.delete is not None and not args.delete:
            bdb.delete_resultset(search_results)
        elif args.update is not None and not args.update:
            update_search_results = True

    # Update record
    if args.update is not None:
        if args.url is not None:
            url_in = args.url[0]
        else:
            url_in = ''

        # Parse tags into a comma-separated string
        if tags_in:
            if tags_in[0] == '+':
                tags = '+' + parse_tags(tags_in[1:])
            elif tags_in[0] == '-':
                tags = '-' + parse_tags(tags_in[1:])
            else:
                tags = parse_tags(tags_in)
        else:
            tags = None

        # No arguments to --update, update all
        if not args.update:
            # Update all records only if search was not opted
            if not search_opted:
                bdb.update_rec(0, url_in, title_in, tags, desc_in, args.immutable, args.threads)
            elif update_search_results and search_results is not None:
                if not args.tacit:
                    print('Updated results:\n')

                pos = len(search_results) - 1
                while pos >= 0:
                    idx = search_results[pos][0]
                    bdb.update_rec(
                        idx,
                        url_in,
                        title_in,
                        tags,
                        desc_in,
                        args.immutable,
                        args.threads
                    )

                    # Commit at every 200th removal
                    if pos % 200 == 0:
                        bdb.conn.commit()

                    pos -= 1
        else:
            for idx in args.update:
                if is_int(idx):
                    bdb.update_rec(
                        int(idx),
                        url_in,
                        title_in,
                        tags,
                        desc_in,
                        args.immutable,
                        args.threads
                    )
                elif '-' in idx:
                    try:
                        vals = [int(x) for x in idx.split('-')]
                        if vals[0] > vals[1]:
                            vals[0], vals[1] = vals[1], vals[0]

                        # Update only once if range starts from 0 (all)
                        if vals[0] == 0:
                            bdb.update_rec(
                                0,
                                url_in,
                                title_in,
                                tags,
                                desc_in,
                                args.immutable,
                                args.threads
                            )
                        else:
                            for _id in range(vals[0], vals[1] + 1):
                                bdb.update_rec(
                                    _id,
                                    url_in,
                                    title_in,
                                    tags,
                                    desc_in,
                                    args.immutable,
                                    args.threads
                                )
                                if INTERRUPTED:
                                    break
                    except ValueError:
                        LOGERR('Invalid index or range to update')
                        bdb.close_quit(1)

                if INTERRUPTED:
                    break

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
                    bdb.delete_rec(0, vals[0], vals[1], True)
            except ValueError:
                LOGERR('Invalid index or range to delete')
                bdb.close_quit(1)
        else:
            ids = []
            # Select the unique indices
            for idx in args.delete:
                if idx not in ids:
                    ids += (idx,)

            try:
                # Index delete order - highest to lowest
                ids.sort(key=lambda x: int(x), reverse=True)
                for idx in ids:
                    bdb.delete_rec(int(idx))
            except ValueError:
                LOGERR('Invalid index or range or combination')
                bdb.close_quit(1)

    # Print record
    if args.print is not None:
        if not args.print:
            if args.count:
                search_results = bdb.list_using_id()
                prompt(bdb, search_results, args.np, False, num=args.count)
            else:
                bdb.print_rec(0)
        else:
            if args.count:
                search_results = bdb.list_using_id(args.print)
                prompt(bdb, search_results, args.np, False, num=args.count)
            else:
                try:
                    for idx in args.print:
                        if is_int(idx):
                            bdb.print_rec(int(idx))
                        elif '-' in idx:
                            vals = [int(x) for x in idx.split('-')]
                            bdb.print_rec(0, vals[0], vals[-1], True)

                except ValueError:
                    LOGERR('Invalid index or range to print')
                    bdb.close_quit(1)

    # Replace a tag in DB
    if args.replace is not None:
        if len(args.replace) == 1:
            bdb.delete_tag_at_index(0, args.replace[0])
        else:
            bdb.replace_tag(args.replace[0], args.replace[1:])

    # Export bookmarks
    if args.export is not None and not search_opted:
        bdb.exportdb(args.export[0])

    # Import bookmarks
    if args.importfile is not None:
        bdb.importdb(args.importfile[0], args.tacit)

    # Import bookmarks from browser
    if args.ai:
        bdb.auto_import_from_browser()

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

    # Shorten URL
    if args.shorten:
        if is_int(args.shorten[0]):
            shorturl = bdb.tnyfy_url(index=int(args.shorten[0]))
        else:
            shorturl = bdb.tnyfy_url(url=args.shorten[0])

        if shorturl:
            print(shorturl)

    # Expand URL
    if args.expand:
        if is_int(args.expand[0]):
            url = bdb.tnyfy_url(index=int(args.expand[0]), shorten=False)
        else:
            url = bdb.tnyfy_url(url=args.expand[0], shorten=False)

        if url:
            print(url)

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
