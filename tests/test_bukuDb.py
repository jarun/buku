#!/usr/bin/env python3
# Unit test cases for buku
# -*- coding: utf-8 -*-
from genericpath import exists
import imp
import os
from tempfile import TemporaryDirectory
import unittest, pytest
from unittest import mock
from os.path import join, expanduser
import sqlite3

buku = imp.load_source('buku', '../buku')

TEST_TEMP_DIR_OBJ = TemporaryDirectory(prefix='bukutest_')
TEST_TEMP_DIR_PATH = TEST_TEMP_DIR_OBJ.name
TEST_TEMP_DBDIR_PATH = join(TEST_TEMP_DIR_PATH, 'buku')
TEST_TEMP_DBFILE_PATH = join(TEST_TEMP_DBDIR_PATH, 'bookmarks.db')

from buku import BukuDb, parse_tags

TEST_BOOKMARKS = [ ['http://slashdot.org',
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

@pytest.fixture()
def setup():
    os.environ['XDG_DATA_HOME'] = TEST_TEMP_DIR_PATH

    # start every test from a clean state
    if exists(TEST_TEMP_DBFILE_PATH):
        os.remove(TEST_TEMP_DBFILE_PATH)

class TestBukuDb(unittest.TestCase):

    def setUp(self):
        os.environ['XDG_DATA_HOME'] = TEST_TEMP_DIR_PATH

        # start every test from a clean state
        if exists(TEST_TEMP_DBFILE_PATH):
            os.remove(TEST_TEMP_DBFILE_PATH)

        self.bookmarks = TEST_BOOKMARKS

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
    def test_get_bookmark_by_index(self):
        bdb = BukuDb()
        for bookmark in self.bookmarks:
            # adding bookmark from self.bookmarks
            bdb.add_bookmark(*bookmark)

        # the expected bookmark
        expected = (1, 'http://slashdot.org', 'SLASHDOT', ',news,old,',
                "News for old nerds, stuff that doesn't matter")
        bookmark_from_db = bdb.get_bookmark_by_index(1)
        # asserting bookmark matches expected
        self.assertEqual(expected, bookmark_from_db)
        # asserting None returned if index out of range
        self.assertIsNone(bdb.get_bookmark_by_index( len(self.bookmarks[0]) + 1 ))

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
    def test_append_tag_at_index(self):
        bdb = BukuDb()
        for bookmark in self.bookmarks:
            bdb.add_bookmark(*bookmark)

        # tags to add
        old_tags = bdb.get_bookmark_by_index(1)[3]
        new_tags = ",foo,bar,baz"
        bdb.append_tag_at_index(1, new_tags)
        # updated list of tags
        from_db = bdb.get_bookmark_by_index(1)[3]

        # checking if new tags were added to the bookmark
        self.assertTrue(all( x in from_db.split(',') for x in new_tags.split(',') ))
        # checking if old tags still exist
        self.assertTrue(all( x in from_db.split(',') for x in old_tags.split(',') ))

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

    # @unittest.skip('skipping')
    def test_delete_bookmark_yes(self):
        bdb = BukuDb()
        # checking that "y" response causes delete_bookmark to return True
        with mock.patch('builtins.input', return_value='y'):
            self.assertTrue(bdb.delete_bookmark(0))

    # @unittest.skip('skipping')
    def test_delete_bookmark_no(self):
        bdb = BukuDb()
        # checking that non-"y" response causes delete_bookmark to return None
        with mock.patch('builtins.input', return_value='n'):
            self.assertIsNone(bdb.delete_bookmark(0))

    # @unittest.skip('skipping')
    def test_delete_all_bookmarks(self):
        bdb = BukuDb()
        # adding bookmarks
        bdb.add_bookmark(*self.bookmarks[0])
        # deleting all bookmarks
        bdb.delete_all_bookmarks()
        # assert table has been dropped
        with self.assertRaises(sqlite3.OperationalError):
            bdb.get_bookmark_by_index(0)

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
        bdb = BukuDb()
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

def test_print_bookmark(capsys, caplog, setup):
    bdb = BukuDb()
    out, err = capsys.readouterr()
    # calling with nonexistent index
    bdb.print_bookmark(1)
    out, err = capsys.readouterr()

    for record in caplog.records():
        assert record.levelname == "ERROR"
        assert record.getMessage() == "No matching index"
    assert (out, err) == ('', '')

    # adding bookmarks
    bdb.add_bookmark("http://full-bookmark.com", "full", parse_tags(['full,bookmark']), "full bookmark")
    bdb.add_bookmark("http://blank-title.com", "", parse_tags(['blank,title']), "blank title")
    bdb.add_bookmark("http://empty-tags.com", "empty tags", parse_tags(['']), "empty tags")
    bdb.add_bookmark("http://all-empty.com", "", parse_tags(['']), "all empty")
    out, err = capsys.readouterr()

    # printing first bookmark
    bdb.print_bookmark(1)
    out, err = capsys.readouterr()
    assert out == "\x1b[1m\x1b[93m1. \x1b[0m\x1b[92mhttp://full-bookmark.com\x1b[0m\n   \x1b[91m>\x1b[0m full\n   \x1b[91m+\x1b[0m full bookmark\n   \x1b[91m#\x1b[0m bookmark,full\n\n"
    assert err == ''

    # printing all bookmarks
    bdb.print_bookmark(0)
    out, err = capsys.readouterr()
    assert out == "\x1b[1m\x1b[93m1. \x1b[0m\x1b[92mhttp://full-bookmark.com\x1b[0m\n   \x1b[91m>\x1b[0m full\n   \x1b[91m+\x1b[0m full bookmark\n   \x1b[91m#\x1b[0m bookmark,full\n\n\x1b[1m\x1b[93m2. \x1b[0m\x1b[92mhttp://blank-title.com\x1b[0m\n   \x1b[91m+\x1b[0m blank title\n   \x1b[91m#\x1b[0m blank,title\n\n\x1b[1m\x1b[93m3. \x1b[0m\x1b[92mhttp://empty-tags.com\x1b[0m\n   \x1b[91m>\x1b[0m empty tags\n   \x1b[91m+\x1b[0m empty tags\n\n\x1b[1m\x1b[93m4. \x1b[0m\x1b[92mhttp://all-empty.com\x1b[0m\n   \x1b[91m+\x1b[0m all empty\n\n"
    assert err == ''

    # printing all bookmarks with empty fields
    bdb.print_bookmark(0, empty=True)
    out, err = capsys.readouterr()
    assert out == "\x1b[1m3 records found\x1b[21m\n\n\x1b[1m\x1b[93m2. \x1b[0m\x1b[92mhttp://blank-title.com\x1b[0m\n   \x1b[91m+\x1b[0m blank title\n   \x1b[91m#\x1b[0m blank,title\n\n\x1b[1m\x1b[93m3. \x1b[0m\x1b[92mhttp://empty-tags.com\x1b[0m\n   \x1b[91m>\x1b[0m empty tags\n   \x1b[91m+\x1b[0m empty tags\n\n\x1b[1m\x1b[93m4. \x1b[0m\x1b[92mhttp://all-empty.com\x1b[0m\n   \x1b[91m+\x1b[0m all empty\n\n"
    assert err == ''

def test_list_tags(capsys, setup):
    bdb = BukuDb()

    # adding bookmarks
    bdb.add_bookmark("http://one.com", "", parse_tags(['cat,ant,bee,1']), "")
    bdb.add_bookmark("http://two.com", "", parse_tags(['Cat,Ant,bee,1']), "")
    bdb.add_bookmark("http://three.com", "", parse_tags(['Cat,Ant,3,Bee,2']), "")

    # listing tags, asserting output
    out, err = capsys.readouterr()
    bdb.list_tags()
    out, err = capsys.readouterr()
    assert out == "     1. 1\n     2. 2\n     3. 3\n     4. Ant\n     5. ant\n     6. bee\n     7. Bee\n     8. Cat\n     9. cat\n"
    assert err == ''

def test_compactdb(setup):
    bdb = BukuDb()

    # adding bookmarks
    for bookmark in TEST_BOOKMARKS:
        bdb.add_bookmark(*bookmark)

    # manually deleting 2nd index from db, calling compactdb
    bdb.cur.execute('DELETE FROM bookmarks WHERE id = ?', (2,))
    bdb.compactdb(2)

    # asserting bookmarks have correct indices
    assert bdb.get_bookmark_by_index(1) == (1, 'http://slashdot.org', 'SLASHDOT', ',news,old,', "News for old nerds, stuff that doesn't matter")
    assert bdb.get_bookmark_by_index(2) == (2, 'https://test.com:8080', 'test', ',es,est,tes,test,', 'a case for replace_tag test')
    assert bdb.get_bookmark_by_index(3) is None

if __name__ == "__main__":
    unittest.main()
