#!/usr/bin/env python3
#
# Bookmark management utility
#
# Copyright © 2015-2019 Arun Prakash Jana <engineerarun@gmail.com>
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
# along with Buku.  If not, see <http://www.gnu.org/licenses/>.

from itertools import chain
import collections
import json
import logging
import os
import re
import shutil
import signal
import sqlite3
from subprocess import Popen, PIPE, DEVNULL
import sys
import threading
import time
import webbrowser
try:
    import readline
    readline
except ImportError:
    pass
from bs4 import BeautifulSoup
import urllib3
from urllib3.util import parse_url

from .bukuconstants import (__version__, __author__, __license__,  # pylint: disable=unused-import # noqa: F401
                            COLORMAP, DELIM, SKIP_MIMES, USER_AGENT, TEXT_BROWSERS)
from .bukucrypt import BukuCrypt
from .bukuimporter import BukuImporter
from .bukunetworking import get_PoolManager, network_handler
from .bukuutil import (get_default_dbdir, is_nongeneric_url, delim_wrap, parse_tags, get_system_editor,
                       get_firefox_profile_name, prep_tag_search, gen_auto_tag, edit_rec, format_json, is_int, regexp)
from .extended_argument_parser import create_argparser, ExtendedArgumentParser

# Global variables
INTERRUPTED = False  # Received SIGINT
PROMPTMSG = 'buku (? for help): '  # Prompt message string

# Default format specifiers to print records
ID_STR = '%d. %s [%s]\n'
ID_DB_STR = '%d. %s'
MUTE_STR = '%s (L)\n'
URL_STR = '   > %s\n'
DESC_STR = '   + %s\n'
TAG_STR = '   # %s\n'

# Set up logging
LOGGER = logging.getLogger()
LOGDBG = LOGGER.debug
LOGERR = LOGGER.error


class BukuDb:
    """Abstracts all database operations.

    Attributes
    ----------
    conn : sqlite database connection.
    cur : sqlite database cursor.
    json : bool
        True if results should be printed in JSON format else False.
    field_filter : int
        Indicates format for displaying bookmarks. Default is 0.
    chatty : bool
        Sets the verbosity of the APIs. Default is False.
    """

    def __init__(self, json=False, field_filter=0, chatty=False, dbfile=None, colorize=True):
        """Database initialization API.

        Parameters
        ----------
        json : bool, optional
            True if results should be printed in JSON format else False.
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
    def initdb(dbfile=None, chatty=False):
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
            dbpath = get_default_dbdir()
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

    def get_rec_by_id(self, index):
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

    def get_max_id(self):
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
            url,
            title_in=None,
            tags_in=None,
            desc=None,
            immutable=0,
            delay_commit=False,
            fetch=True):
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
            index,
            url=None,
            title_in=None,
            tags_in=None,
            desc=None,
            immutable=-1,
            threads=4):
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

        arguments = []
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

    def refreshdb(self, index, threads):
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

    def searchdb(self, keywords, all_keywords=False, deep=False, regex=False):
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
        qargs = []

        case_statement = lambda x: 'CASE WHEN ' + x + ' THEN 1 ELSE 0 END'
        if regex:
            q0 = 'SELECT id, url, metadata, tags, desc FROM (SELECT *, '
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
                q0 = 'SELECT id, url, metadata, tags, desc FROM bookmarks WHERE '
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
            q0 = 'SELECT id, url, metadata, tags, desc FROM (SELECT *, '
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

    def search_by_tag(self, tags):
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

        tags, search_operator, excluded_tags = prep_tag_search(tags)
        if search_operator is None:
            LOGERR("Cannot use both '+' and ',' in same search")
            return None

        LOGDBG('tags: %s', tags)
        LOGDBG('search_operator: %s', search_operator)
        LOGDBG('excluded_tags: %s', excluded_tags)

        if search_operator == 'AND':
            query = ("SELECT id, url, metadata, tags, desc FROM bookmarks "
                     "WHERE tags LIKE '%' || ? || '%' ")
            for tag in tags[1:]:
                query += "{} tags LIKE '%' || ? || '%' ".format(search_operator)

            if excluded_tags:
                tags.append(excluded_tags)
                query = query.replace('WHERE tags', 'WHERE (tags')
                query += ') AND tags NOT REGEXP ? '
            query += 'ORDER BY id ASC'
        else:
            query = 'SELECT id, url, metadata, tags, desc FROM (SELECT *, '
            case_statement = "CASE WHEN tags LIKE '%' || ? || '%' THEN 1 ELSE 0 END"
            query += case_statement

            for tag in tags[1:]:
                query += ' + ' + case_statement

            query += ' AS score FROM bookmarks WHERE score > 0'

            if excluded_tags:
                tags.append(excluded_tags)
                query += ' AND tags NOT REGEXP ? '

            query += ' ORDER BY score DESC)'

        LOGDBG('query: "%s", args: %s', query, tags)
        self.cur.execute(query, tuple(tags, ))
        return self.cur.fetchall()

    def search_keywords_and_filter_by_tags(self, keywords, all_keywords, deep, regex, stag):
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
        stag_results = self.search_by_tag(''.join(stag))
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

    def compactdb(self, index, delay_commit=False):
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

        query1 = 'SELECT id, URL, metadata, tags, desc FROM bookmarks WHERE id = ? LIMIT 1'
        query2 = 'DELETE FROM bookmarks WHERE id = ?'
        query3 = 'INSERT INTO bookmarks(id, URL, metadata, tags, desc) VALUES (?, ?, ?, ?, ?)'

        if max_id > index:
            self.cur.execute(query1, (max_id,))
            results = self.cur.fetchall()
            for row in results:
                self.cur.execute(query2, (row[0],))
                self.cur.execute(query3, (index, row[1], row[2], row[3], row[4],))
                if not delay_commit:
                    self.conn.commit()
                if self.chatty:
                    print('Index %d moved to %d' % (row[0], index))

    def delete_rec(self, index, low=0, high=0, is_range=False, delay_commit=False):
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

            if not self.json:
                print_rec_with_filter(results, self.field_filter)
            else:
                print(format_json(results, True, self.field_filter))

            return True
        else:  # Show all entries
            self.cur.execute('SELECT * FROM bookmarks')
            resultset = self.cur.fetchall()

        if not resultset:
            LOGERR('0 records')
            return True

        if not self.json:
            print_rec_with_filter(resultset, self.field_filter)
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

    def replace_tag(self, orig, new=None):
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
            if tags == DELIM:
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
                else:
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

    def exportdb(self, filepath, resultset=None):
        """Export DB bookmarks to file.
        Exports full DB, if resultset is None

        If destination file name ends with '.db', bookmarks are
        exported to a Buku database file.
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
        timestamp = str(int(time.time()))

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
            outdb.conn.commit()
            outdb.close()

            count = self.get_max_id()
            if count == -1:
                count = 0
            print('%s exported' % count)
            return True

        try:
            outfp = open(filepath, mode='w', encoding='utf-8')
        except Exception as e:
            LOGERR(e)
            return False

        if filepath.endswith('.md'):
            for row in resultset:
                if row[2] == '':
                    out = '- [Untitled](' + row[1] + ')\n'
                else:
                    out = '- [' + row[2] + '](' + row[1] + ')\n'
                outfp.write(out)
                count += 1

        elif filepath.endswith('.org'):
            for row in resultset:
                if row[2] == '':
                    out = '* [[{}][Untitled]]\n'.format(row[1])
                else:
                    out = '* [[{}][{}]]\n'.format(row[1], row[2])
                outfp.write(out)
                count += 1
        else:
            outfp.write('<!DOCTYPE NETSCAPE-Bookmark-file-1>\n\n'
                        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
                        '<TITLE>Bookmarks</TITLE>\n'
                        '<H1>Bookmarks</H1>\n\n'
                        '<DL><p>\n'
                        '    <DT><H3 ADD_DATE="%s" LAST_MODIFIED="%s" '
                        'PERSONAL_TOOLBAR_FOLDER="true">Buku bookmarks</H3>\n'
                        '    <DL><p>\n'
                        % (timestamp, timestamp))

            for row in resultset:
                out = ('        <DT><A HREF="%s" ADD_DATE="%s" LAST_MODIFIED="%s"'
                       % (row[1], timestamp, timestamp))
                if row[3] != DELIM:
                    out += ' TAGS="' + row[3][1:-1] + '"'
                out += '>' + row[2] + '</A>\n'
                if row[4] != '':
                    out += '        <DD>' + row[4] + '\n'

                outfp.write(out)
                count += 1

            outfp.write('    </DL><p>\n</DL><p>')

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

        with open(path, 'r') as datafile:
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
        if sys.version_info >= (3, 4, 4):
            # Python 3.4.4 and above
            conn = sqlite3.connect('file:%s?mode=ro' % path, uri=True)
        else:
            conn = sqlite3.connect(path)

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
            LOGERR('Buku does not support {} yet'.format(sys.platform))
            self.close_quit(1)

        if self.chatty:
            newtag = gen_auto_tag()
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
        except Exception:
            print('Could not import bookmarks from google-chrome')

        try:
            if self.chatty:
                resp = input('Import bookmarks from chromium? (y/n): ')
            if resp == 'y':
                bookmarks_database = os.path.expanduser(cb_bm_db_path)
                if not os.path.exists(bookmarks_database):
                    raise FileNotFoundError
                self.load_chrome_database(bookmarks_database, newtag, add_parent_folder_as_tag)
        except Exception:
            print('Could not import bookmarks from chromium')

        try:
            if self.chatty:
                resp = input('Import bookmarks from Firefox? (y/n): ')
            if resp == 'y':
                bookmarks_database = os.path.expanduser(ff_bm_db_path)
                if not os.path.exists(bookmarks_database):
                    raise FileNotFoundError
                self.load_firefox_database(bookmarks_database, newtag, add_parent_folder_as_tag)
        except Exception:
            print('Could not import bookmarks from Firefox.')

        self.conn.commit()

        if newtag:
            print('\nAuto-generated tag: %s' % newtag)

    def importdb(self, filepath, tacit=False):
        """Import bookmarks from a HTML or a Markdown file.

        Supports Firefox, Google Chrome, and IE exported HTML bookmarks.
        Supports Markdown files with extension '.md, .org'.
        Supports importing bookmarks from another Buku database file.

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

        if not tacit:
            newtag = gen_auto_tag()
        else:
            newtag = None

        if not tacit:
            append_tags_resp = input('Append tags when bookmark exist? (y/n): ')
        else:
            append_tags_resp = 'y'

        items = []
        if filepath.endswith('.md'):
            items = BukuImporter.import_md(filepath=filepath, newtag=newtag)
        elif filepath.endswith('org'):
            items = BukuImporter.import_org(filepath=filepath, newtag=newtag)
        elif filepath.endswith('json'):
            if not tacit:
                resp = input('Add parent folder names as tags? (y/n): ')
            else:
                resp = 'y'
            add_bookmark_folder_as_tag = (resp == 'y')
            try:
                with open(filepath, 'r', encoding='utf-8') as datafile:
                    data = json.load(datafile)

                items = BukuImporter.import_firefox_json(data, add_bookmark_folder_as_tag, newtag)
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
            items = BukuImporter.import_html(soup, add_parent_folder_as_tag, newtag)
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
        """Merge bookmarks from another Buku database file.

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
            if sys.version_info >= (3, 4, 4):
                # Python 3.4.4 and above
                indb_conn = sqlite3.connect('file:%s?mode=ro' % path, uri=True)
            else:
                indb_conn = sqlite3.connect(path)

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

    def tnyfy_url(self, index=0, url=None, shorten=True):
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

        urlbase = 'https://tny.im/yourls-api.php?action='
        if shorten:
            _u = urlbase + 'shorturl&format=simple&url=' + qp(url)
        else:
            _u = urlbase + 'expand&format=simple&shorturl=' + qp(url)

        manager = get_PoolManager()

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
        api_url = 'https://archive.org/wayback/available/?url=' + quote_plus(url)
        manager = get_PoolManager()
        resp = manager.request('GET', api_url)
        respobj = json.loads(resp.data.decode('utf-8'))
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


# ----------------
# Helper functions
# ----------------


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
        import tempfile
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
    except BrokenPipeError:
        sys.stdout = os.fdopen(1)
        sys.exit(1)


def print_single_rec(row, idx=0):  # NOQA
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
    except BrokenPipeError:
        sys.stdout = os.fdopen(1)
        sys.exit(1)


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

    manager = get_PoolManager()

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

    argparser = create_argparser()

    # Parse the arguments
    args = argparser.parse_args()

    # Show help and exit if help requested
    if args.help:
        argparser.print_help(sys.stdout)
        sys.exit(0)

    # By default, Buku uses ANSI colors. As Windows does not really use them,
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
        PROMPTMSG = '\x1b[7mbuku (? for help)\x1b[0m '

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
        LOGDBG('Buku v%s', __version__)
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

        if not args.json and not args.format:
            num = 10 if not args.count else args.count
            prompt(bdb, search_results, oneshot, args.deep, num=num)
        elif not args.json:
            print_rec_with_filter(search_results, field_filter=args.format)
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