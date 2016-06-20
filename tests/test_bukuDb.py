#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from genericpath import exists
import imp
import os
from tempfile import TemporaryDirectory
import unittest
from os.path import join, expanduser
import sqlite3

buku = imp.load_source('buku', '../buku')

TEST_TEMP_DIR_OBJ = TemporaryDirectory(prefix='bukutest_')
TEST_TEMP_DIR_PATH = TEST_TEMP_DIR_OBJ.name
TEST_TEMP_DBDIR_PATH = join(TEST_TEMP_DIR_PATH, 'buku')
TEST_TEMP_DBFILE_PATH = join(TEST_TEMP_DBDIR_PATH, 'bookmarks.db')

from buku import BukuDb, parse_tags


class TestBukuDb(unittest.TestCase):

    def setUp(self):
        os.environ['XDG_DATA_HOME'] = TEST_TEMP_DIR_PATH

        # start every test from a clean state
        if exists(TEST_TEMP_DBFILE_PATH):
            os.remove(TEST_TEMP_DBFILE_PATH)

        self.bookmarks = [ ['http://slashdot.org',
                            'SLASHDOT',
                            parse_tags(['old,news']),
                            "News for old nerds, stuff that doesn't matter",
                            ],

                           ['http://www.zażółćgęśląjaźń.pl/',
                            'ZAŻÓŁĆ',
                            parse_tags(['zażółć,gęślą,jaźń']),
                            "Testing UTF-8, zażółć gęślą jaźń.",
                            ],

                           ['https://test.com:8080',
                            'test',
                            parse_tags(['test,tes,est,es']),
                            "a case for replace_tag test",
                            ],
        ]

    def tearDown(self):
        os.environ['XDG_DATA_HOME'] = TEST_TEMP_DIR_PATH

    # @unittest.skip('skipping')
    def test_get_dbdir_path(self):
        dbdir_expected = TEST_TEMP_DBDIR_PATH
        dbdir_local_expected = join(expanduser('~'), '.local', 'share', 'buku')
        dbdir_relative_expected = join('.', 'buku')

        # desktop linux
        self.assertEqual(dbdir_expected, BukuDb.get_dbdir_path())

        # desktop generic
        os.environ.pop('XDG_DATA_HOME')
        self.assertEqual(dbdir_local_expected, BukuDb.get_dbdir_path())

        # no desktop

        # -- home is defined differently on various platforms.
        # -- keep a copy and set it back once done
        originals = {}
        for env_var in ['HOME', 'HOMEPATH', 'HOMEDIR']:
            try:
                originals[env_var] = os.environ.pop(env_var)
            except KeyError:
                pass
        self.assertEqual(dbdir_relative_expected, BukuDb.get_dbdir_path())
        for key, value in originals.items():
            os.environ[key] = value

    # # not sure how to test this in nondestructive manner
    # def test_move_legacy_dbfile(self):
    #     self.fail()

    # @unittest.skip('skipping')
    def test_initdb(self):
        if exists(TEST_TEMP_DBFILE_PATH):
            os.remove(TEST_TEMP_DBFILE_PATH)
        self.assertIs(False, exists(TEST_TEMP_DBFILE_PATH))
        conn, curr = BukuDb.initdb()
        self.assertIsInstance(conn, sqlite3.Connection)
        self.assertIsInstance(curr, sqlite3.Cursor)
        self.assertIs(True, exists(TEST_TEMP_DBFILE_PATH))
        curr.close()
        conn.close()

    # @unittest.skip('skipping')
    def test_get_bookmark_index(self):
        bdb = BukuDb()
        for idx, bookmark in enumerate(self.bookmarks):
            # adding bookmark from self.bookmarks to database
            bdb.add_bookmark(*bookmark)
            # asserting index is in order
            idx_from_db = bdb.get_bookmark_index(bookmark[0])
            self.assertEqual(idx + 1, idx_from_db)

        # asserting -1 is returned for nonexistent url
        idx_from_db = bdb.get_bookmark_index("http://nonexistent.url")
        self.assertEqual(-1, idx_from_db)

    # @unittest.skip('skipping')
    def test_add_bookmark(self):
        bdb = BukuDb()

        for bookmark in self.bookmarks:
            # adding bookmark from self.bookmarks to database
            bdb.add_bookmark(*bookmark)
            # retrieving bookmark from database
            index = bdb.get_bookmark_index(bookmark[0])
            from_db = bdb.get_bookmark_by_index(index)
            self.assertIsNotNone(from_db)
            # comparing data
            for pair in zip(from_db[1:], bookmark):
                self.assertEqual(*pair)

        # TODO: tags should be passed to the api as a sequence...

    # @unittest.skip('skipping')
    def test_update_bookmark(self):
        bdb = BukuDb()
        old_values = self.bookmarks[0]
        new_values = self.bookmarks[1]

        # adding bookmark and getting index
        bdb.add_bookmark(*old_values)
        index = bdb.get_bookmark_index(old_values[0])
        # updating with new values
        bdb.update_bookmark(index, *new_values)
        # retrieving bookmark from database
        from_db = bdb.get_bookmark_by_index(index)
        self.assertIsNotNone(from_db)
        # checking if values are updated
        for pair in zip(from_db[1:], new_values):
            self.assertEqual(*pair)

    # @unittest.skip('skipping')
    def test_refreshdb(self):
        bdb = BukuDb()

        bdb.add_bookmark("https://www.google.com/ncr", "?")
        bdb.refreshdb(1)
        from_db = bdb.get_bookmark_by_index(1)
        self.assertEqual(from_db[2], "Google")

    # def test_searchdb(self):
        # self.fail()

    # def test_search_by_tag(self):
        # self.fail()

    # def test_compactdb(self):
        # self.fail()

    # @unittest.skip('skipping')
    def test_delete_bookmark(self):
        bdb = BukuDb()
        # adding bookmark and getting index
        bdb.add_bookmark(*self.bookmarks[0])
        index = bdb.get_bookmark_index(self.bookmarks[0][0])
        # deleting bookmark
        bdb.delete_bookmark(index)
        # asserting it doesn't exist
        from_db = bdb.get_bookmark_by_index(index)
        self.assertIsNone(from_db)

        # TODO: test deleting all bookmarks (index == 0)

    # def test_print_bookmark(self):
        # self.fail()

    # def test_list_tags(self):
        # self.fail()

    # @unittest.skip('skipping')
    def test_replace_tag(self):
        bdb = BukuDb()
        indices = []
        for bookmark in self.bookmarks:
            # adding bookmark, getting index
            bdb.add_bookmark(*bookmark)
            index = bdb.get_bookmark_index(bookmark[0])
            indices += [index]
        # replacing tags
        bdb.replace_tag("news", ["__01"])
        bdb.replace_tag("zażółć", ["__02,__03"])
        # replacing tag which is also a substring of other tag
        bdb.replace_tag("es", ["__04"])
        # removing tags
        bdb.replace_tag("gęślą")
        bdb.replace_tag("old")
        # removing nonexistent tag
        bdb.replace_tag("_")
        # removing nonexistent tag which is also a substring of other tag
        bdb.replace_tag("e")

        for url, title, _, _  in self.bookmarks:
            # retrieving from db
            index = bdb.get_bookmark_index(url)
            from_db = bdb.get_bookmark_by_index(index)
            # asserting tags were replaced
            if title == "SLASHDOT":
                self.assertEqual(from_db[3], parse_tags(["__01"]))
            elif title == "ZAŻÓŁĆ":
                self.assertEqual(from_db[3], parse_tags(["__02,__03,jaźń"]))
            elif title == "test":
                self.assertEqual(from_db[3], parse_tags(["test,tes,est,__04"]))

    # def test_browse_by_index(self):
        # self.fail()

    # @unittest.skip('skipping')
    def test_close_quit(self):
        bdb=BukuDb()
        # quitting with no args
        try:
            bdb.close_quit()
        except SystemExit as err:
            self.assertEqual(err.args[0], 0)
        # quitting with custom arg
        try:
            bdb.close_quit(1)
        except SystemExit as err:
            self.assertEqual(err.args[0], 1)

    # def test_import_bookmark(self):
        # self.fail()


if __name__ == "__main__":
    unittest.main()
