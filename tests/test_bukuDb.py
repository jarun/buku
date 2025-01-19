#!/usr/bin/env python3
#
# Unit test cases for buku
#
import math
import os
import re
import sqlite3
import sys
import unittest
from tempfile import NamedTemporaryFile, TemporaryDirectory
from random import shuffle
from unittest import mock

import pytest
import yaml
from genericpath import exists
from hypothesis import example, given, settings
from hypothesis import strategies as st

from buku import PERMANENT_REDIRECTS, BukuDb, FetchResult, BookmarkVar, bookmark_vars, parse_tags, prompt
from tests.util import mock_http, mock_fetch, _add_rec, _tagset


def get_temp_dir_path():
    with TemporaryDirectory(prefix="bukutest_") as dir_obj:
        return dir_obj

TEST_TEMP_DIR_PATH = get_temp_dir_path()
TEST_TEMP_DBDIR_PATH = os.path.join(TEST_TEMP_DIR_PATH, "buku")
TEST_TEMP_DBFILE_PATH = os.path.join(TEST_TEMP_DBDIR_PATH, "bookmarks.db")
MAX_SQLITE_INT = int(math.pow(2, 63) - 1)
TEST_PRINT_REC = ("https://example.com", "", parse_tags(["cat,ant,bee,1"]), "")

TEST_BOOKMARKS = [
    [
        "http://slashdot.org",
        "SLASHDOT",
        parse_tags(["old,news"]),
        "News for old nerds, stuff that doesn't matter",
    ],
    [
        "http://www.zażółćgęśląjaźń.pl/",
        "ZAŻÓŁĆ",
        parse_tags(["zażółć,gęślą,jaźń"]),
        "Testing UTF-8, zażółć gęślą jaźń.",
    ],
    [
        "http://example.com/",
        "test",
        parse_tags(["test,tes,est,es"]),
        "a case for replace_tag test",
    ],
]

only_python_3_5 = pytest.mark.skipif(
    sys.version_info < (3, 5), reason="requires Python 3.5 or later"
)


@pytest.fixture(scope="module")
def vcr_cassette_dir(request):
    # Put all cassettes in vhs/{module}/{test}.yaml
    return os.path.join("tests", "vcr_cassettes", request.module.__name__)


def rmdb(*bdbs):
    for bdb in bdbs:
        try:
            bdb.cur.close()
            bdb.conn.close()
        except Exception:
            pass
    if exists(TEST_TEMP_DBFILE_PATH):
        os.remove(TEST_TEMP_DBFILE_PATH)


@pytest.fixture()
def bukuDb():
    os.environ["XDG_DATA_HOME"] = TEST_TEMP_DIR_PATH

    # start every test from a clean state
    rmdb()

    bdbs = []

    def _bukuDb(*args, **kwargs):
        nonlocal bdbs
        bdbs += [BukuDb(*args, **kwargs)]
        return bdbs[-1]

    yield _bukuDb
    rmdb(*bdbs)


class PrettySafeLoader(
    yaml.SafeLoader
):  # pylint: disable=too-many-ancestors,too-few-public-methods
    def construct_python_tuple(self, node):
        return tuple(self.construct_sequence(node))


PrettySafeLoader.add_constructor(
    "tag:yaml.org,2002:python/tuple", PrettySafeLoader.construct_python_tuple
)


class TestBukuDb(unittest.TestCase):
    def setUp(self):
        os.environ["XDG_DATA_HOME"] = TEST_TEMP_DIR_PATH

        # start every test from a clean state
        rmdb()

        self.bookmarks = TEST_BOOKMARKS
        self.bdb = BukuDb()

    def tearDown(self):
        os.environ["XDG_DATA_HOME"] = TEST_TEMP_DIR_PATH
        rmdb(self.bdb)

    @pytest.mark.non_tox
    def test_get_default_dbdir(self):
        dbdir_expected = TEST_TEMP_DBDIR_PATH
        home = os.path.expanduser("~")
        dbdir_local_expected = (os.path.join(home, ".local", "share", "buku") if sys.platform != 'win32' else
                                os.path.join(home, "AppData", "Roaming", "buku"))
        dbdir_relative_expected = os.path.abspath(".")

        # desktop linux
        self.assertEqual(dbdir_expected, BukuDb.get_default_dbdir())

        # desktop generic
        os.environ.pop("XDG_DATA_HOME")
        self.assertEqual(dbdir_local_expected, BukuDb.get_default_dbdir())

        # no desktop

        # -- home is defined differently on various platforms.
        # -- keep a copy and set it back once done
        originals = {}
        for env_var in ["HOME", "HOMEPATH", "HOMEDIR", "APPDATA"]:
            if env_var in os.environ:
                originals[env_var] = os.environ.pop(env_var)
        try:
            self.assertEqual(dbdir_relative_expected, BukuDb.get_default_dbdir())
        finally:
            os.environ.update(originals)

    # # not sure how to test this in nondestructive manner
    # def test_move_legacy_dbfile(self):
    #     self.fail()

    def test_initdb(self):
        rmdb(self.bdb)
        self.assertIs(False, exists(TEST_TEMP_DBFILE_PATH))
        try:
            conn, curr = BukuDb.initdb()
            self.assertIsInstance(conn, sqlite3.Connection)
            self.assertIsInstance(curr, sqlite3.Cursor)
            self.assertIs(True, exists(TEST_TEMP_DBFILE_PATH))
        finally:
            curr.close()
            conn.close()

    def test_get_rec_by_id(self):
        for bookmark in self.bookmarks:
            # adding bookmark from self.bookmarks
            _add_rec(self.bdb, *bookmark)

        # the expected bookmark
        expected = (1,) + tuple(TEST_BOOKMARKS[0]) + (0,)
        bookmark_from_db = self.bdb.get_rec_by_id(1)
        # asserting bookmark matches expected
        self.assertEqual(expected, bookmark_from_db)
        # asserting None returned if index out of range
        self.assertIsNone(self.bdb.get_rec_by_id(len(self.bookmarks[0]) + 1))

    def test_get_rec_all_by_ids(self):
        for bookmark in self.bookmarks:
            # adding bookmark from self.bookmarks
            _add_rec(self.bdb, *bookmark)
        expected = [(i+1,) + tuple(TEST_BOOKMARKS[i]) + (0,) for i in [0, 2]]
        bookmarks_from_db = self.bdb.get_rec_all_by_ids([3, 1, 1, 3, 5])  # ignoring order and duplicates
        self.assertEqual(expected, bookmarks_from_db)

    def test_get_rec_id(self):
        for idx, bookmark in enumerate(self.bookmarks):
            # adding bookmark from self.bookmarks to database
            _add_rec(self.bdb, *bookmark)
            # asserting index is in order
            idx_from_db = self.bdb.get_rec_id(bookmark[0])
            self.assertEqual(idx + 1, idx_from_db)

        # asserting None is returned for nonexistent url
        idx_from_db = self.bdb.get_rec_id("http://nonexistent.url")
        self.assertIsNone(idx_from_db)

    def test_add_rec(self):
        for bookmark in self.bookmarks:
            # adding bookmark from self.bookmarks to database
            self.bdb.add_rec(*bookmark, fetch=False)
            # retrieving bookmark from database
            index = self.bdb.get_rec_id(bookmark[0])
            from_db = self.bdb.get_rec_by_id(index)
            self.assertIsNotNone(from_db)
            # comparing data
            for pair in zip(from_db[1:], bookmark):
                self.assertEqual(*pair)

    def test_swap_recs(self):
        for bookmark in self.bookmarks:
            _add_rec(self.bdb, *bookmark)
        for id1, id2 in [(0, 1), (1, 4), (1, 1)]:
            self.assertFalse(self.bdb.swap_recs(id1, id2), 'Not a valid index pair: (%d, %d)' % (id1, id2))
        self.assertTrue(self.bdb.swap_recs(1, 3), 'This one should be valid')  # 3, 2, 1
        self.assertEqual([x[0] for x in reversed(self.bookmarks)], [x.url for x in self.bdb.get_rec_all()])

    # TODO: tags should be passed to the api as a sequence...
    def test_suggest_tags(self):
        for bookmark in self.bookmarks:
            _add_rec(self.bdb, *bookmark)

        tagstr = ",test,old,"
        with mock.patch("builtins.input", return_value="1 2 3"):
            expected_results = ",es,est,news,old,test,"
            suggested_results = self.bdb.suggest_similar_tag(tagstr)
            self.assertEqual(expected_results, suggested_results)

        # returns user supplied tags if none are in the DB
        tagstr = ",uniquetag1,uniquetag2,"
        expected_results = tagstr
        suggested_results = self.bdb.suggest_similar_tag(tagstr)
        self.assertEqual(expected_results, suggested_results)

    def test_update_rec(self):
        old_values = self.bookmarks[0]
        new_values = self.bookmarks[1]

        # adding bookmark and getting index
        _add_rec(self.bdb, *old_values)
        index = self.bdb.get_rec_id(old_values[0])
        # updating with new values
        self.bdb.update_rec(index, *new_values)
        # retrieving bookmark from database
        from_db = self.bdb.get_rec_by_id(index)
        self.assertIsNotNone(from_db)
        # checking if values are updated
        for pair in zip(from_db[1:], new_values):
            self.assertEqual(*pair)

    def test_append_tag_at_index(self):
        for bookmark in self.bookmarks:
            _add_rec(self.bdb, *bookmark)

        # tags to add
        old_tags = self.bdb.get_rec_by_id(1)[3]
        new_tags = ",foo,bar,baz"
        self.bdb.append_tag_at_index(1, new_tags)
        # updated list of tags
        from_db = self.bdb.get_rec_by_id(1)[3]

        # checking if new tags were added to the bookmark
        self.assertTrue(split_and_test_membership(new_tags, from_db))
        # checking if old tags still exist
        self.assertTrue(split_and_test_membership(old_tags, from_db))

    def test_append_tag_at_all_indices(self):
        for bookmark in self.bookmarks:
            _add_rec(self.bdb, *bookmark)

        # tags to add
        new_tags = ",foo,bar,baz"
        # record of original tags for each bookmark
        old_tagsets = {
            i: self.bdb.get_rec_by_id(i)[3]
            for i in inclusive_range(1, len(self.bookmarks))
        }

        with mock.patch("builtins.input", return_value="y"):
            self.bdb.append_tag_at_index(0, new_tags)
            # updated tags for each bookmark
            from_db = [
                (i, self.bdb.get_rec_by_id(i)[3])
                for i in inclusive_range(1, len(self.bookmarks))
            ]
            for index, tagset in from_db:
                # checking if new tags added to bookmark
                self.assertTrue(split_and_test_membership(new_tags, tagset))
                # checking if old tags still exist for bookmark
                self.assertTrue(split_and_test_membership(old_tagsets[index], tagset))

    def test_delete_tag_at_index(self):
        # adding bookmarks
        for bookmark in self.bookmarks:
            _add_rec(self.bdb, *bookmark)

        get_tags_at_idx = lambda i: self.bdb.get_rec_by_id(i)[3]
        # list of two-tuples, each containing bookmark index and corresponding tags
        tags_by_index = [
            (i, get_tags_at_idx(i)) for i in inclusive_range(1, len(self.bookmarks))
        ]

        for i, tags in tags_by_index:
            # get the first tag from the bookmark
            to_delete = re.match(",.*?,", tags).group(0)
            self.bdb.delete_tag_at_index(i, to_delete)
            # get updated tags from db
            from_db = get_tags_at_idx(i)
            self.assertNotIn(to_delete, from_db)

    def test_search_keywords_and_filter_by_tags(self):
        # adding bookmark
        for bookmark in self.bookmarks:
            _add_rec(self.bdb, *bookmark)

        with mock.patch("buku.prompt"):
            expected = [
                (
                    3,
                    "http://example.com/",
                    "test",
                    ",es,est,tes,test,",
                    "a case for replace_tag test",
                    0,
                )
            ]
            results = self.bdb.search_keywords_and_filter_by_tags(
                ["News", "case"],
                False,
                False,
                False,
                ["est"],
            )
            self.assertIn(expected[0], results)
            expected = [
                (
                    3,
                    "http://example.com/",
                    "test",
                    ",es,est,tes,test,",
                    "a case for replace_tag test",
                    0,
                ),
                (
                    2,
                    "http://www.zażółćgęśląjaźń.pl/",
                    "ZAŻÓŁĆ",
                    ",gęślą,jaźń,zażółć,",
                    "Testing UTF-8, zażółć gęślą jaźń.",
                    0,
                ),
            ]
            results = self.bdb.search_keywords_and_filter_by_tags(
                ["UTF-8", "case"],
                False,
                False,
                False,
                "jaźń, test",
            )
            self.assertIn(expected[0], results)
            self.assertIn(expected[1], results)

    def test_searchdb(self):
        # adding bookmarks
        for bookmark in self.bookmarks:
            _add_rec(self.bdb, *bookmark)

        get_first_tag = lambda x: "".join(x[2].split(",")[:2])
        for i, bookmark in enumerate(self.bookmarks):
            tag_search = get_first_tag(bookmark)
            # search by the domain name for url
            url_search = re.match(r"https?://(.*)?\..*", bookmark[0]).group(1)
            title_search = bookmark[1]
            # Expect a five-tuple containing all bookmark data
            # db index, URL, title, tags, description
            expected = [(i + 1,) + tuple(bookmark)]
            expected[0] += tuple([0])
            # search db by tag, url (domain name), and title
            for keyword in (tag_search, url_search, title_search):
                with mock.patch("buku.prompt"):
                    # search by keyword
                    results = self.bdb.searchdb([keyword])
                    self.assertEqual(results, expected)

    def test_search_by_tag(self):
        # adding bookmarks
        for bookmark in self.bookmarks:
            _add_rec(self.bdb, *bookmark)

        with mock.patch("buku.prompt"):
            get_first_tag = lambda x: "".join(x[2].split(",")[:2])
            for i, bookmark in enumerate(self.bookmarks):
                # search for bookmark with a tag that is known to exist
                results = self.bdb.search_by_tag(get_first_tag(bookmark))
                # Expect a five-tuple containing all bookmark data
                # db index, URL, title, tags, description
                expected = [(i + 1,) + tuple(bookmark)]
                expected[0] += tuple([0])
                self.assertEqual(results, expected)

    @pytest.mark.slow
    @pytest.mark.vcr("tests/vcr_cassettes/test_search_by_multiple_tags_search_any.yaml")
    def test_search_by_multiple_tags_search_any(self):
        # adding bookmarks
        for bookmark in self.bookmarks:
            self.bdb.add_rec(*bookmark)

        new_bookmark = [
            "https://newbookmark.com",
            "New Bookmark",
            parse_tags(["test,old,new"]),
            "additional bookmark to test multiple tag search",
            0,
        ]

        self.bdb.add_rec(*new_bookmark)

        with mock.patch("buku.prompt"):
            # search for bookmarks matching ANY of the supplied tags
            results = self.bdb.search_by_tag("test, old")
            # Expect a list of five-element tuples containing all bookmark data
            # db index, URL, title, tags, description, ordered by records with
            # the most number of matches.
            expected = [
                (
                    4,
                    "https://newbookmark.com",
                    "New Bookmark",
                    parse_tags([",test,old,new,"]),
                    "additional bookmark to test multiple tag search",
                    0,
                ),
                (
                    1,
                    "http://slashdot.org",
                    "SLASHDOT",
                    parse_tags([",news,old,"]),
                    "News for old nerds, stuff that doesn't matter",
                    0,
                ),
                (
                    3,
                    "http://example.com/",
                    "test",
                    ",es,est,tes,test,",
                    "a case for replace_tag test",
                    0,
                ),
            ]
            self.assertEqual(results, expected)

    @pytest.mark.slow
    @pytest.mark.vcr("tests/vcr_cassettes/test_search_by_multiple_tags_search_all.yaml")
    def test_search_by_multiple_tags_search_all(self):
        # adding bookmarks
        for bookmark in self.bookmarks:
            self.bdb.add_rec(*bookmark)

        new_bookmark = [
            "https://newbookmark.com",
            "New Bookmark",
            parse_tags(["test,old,new"]),
            "additional bookmark to test multiple tag search",
        ]

        self.bdb.add_rec(*new_bookmark)

        with mock.patch("buku.prompt"):
            # search for bookmarks matching ALL of the supplied tags
            results = self.bdb.search_by_tag("test + old")
            # Expect a list of five-element tuples containing all bookmark data
            # db index, URL, title, tags, description
            expected = [
                (
                    4,
                    "https://newbookmark.com",
                    "New Bookmark",
                    parse_tags([",test,old,new,"]),
                    "additional bookmark to test multiple tag search",
                    0,
                )
            ]
            self.assertEqual(results, expected)

    def test_search_by_tags_enforces_space_seprations_search_all(self):

        bookmark1 = [
            "https://bookmark1.com",
            "Bookmark One",
            parse_tags(["tag, two,tag+two"]),
            "test case for bookmark with '+' in tag",
        ]

        bookmark2 = [
            "https://bookmark2.com",
            "Bookmark Two",
            parse_tags(["tag,two, tag-two"]),
            "test case for bookmark with hyphenated tag",
        ]

        _add_rec(self.bdb, *bookmark1)
        _add_rec(self.bdb, *bookmark2)

        with mock.patch("buku.prompt"):
            # check that space separation for ' + ' operator is enforced
            results = self.bdb.search_by_tag("tag+two")
            # Expect a list of five-element tuples containing all bookmark data
            # db index, URL, title, tags, description
            expected = [
                (
                    1,
                    "https://bookmark1.com",
                    "Bookmark One",
                    parse_tags([",tag,two,tag+two,"]),
                    "test case for bookmark with '+' in tag",
                    0,
                )
            ]
            self.assertEqual(results, expected)
            results = self.bdb.search_by_tag("tag + two")
            # Expect a list of five-element tuples containing all bookmark data
            # db index, URL, title, tags, description
            expected = [
                (
                    1,
                    "https://bookmark1.com",
                    "Bookmark One",
                    parse_tags([",tag,two,tag+two,"]),
                    "test case for bookmark with '+' in tag",
                    0,
                ),
                (
                    2,
                    "https://bookmark2.com",
                    "Bookmark Two",
                    parse_tags([",tag,two,tag-two,"]),
                    "test case for bookmark with hyphenated tag",
                    0,
                ),
            ]
            self.assertEqual(results, expected)

    def test_search_by_tags_exclusion(self):
        # adding bookmarks
        for bookmark in self.bookmarks:
            _add_rec(self.bdb, *bookmark)

        new_bookmark = [
            "https://newbookmark.com",
            "New Bookmark",
            parse_tags(["test,old,new"]),
            "additional bookmark to test multiple tag search",
        ]

        _add_rec(self.bdb, *new_bookmark)

        with mock.patch("buku.prompt"):
            # search for bookmarks matching ANY of the supplied tags
            # while excluding bookmarks from results that match a given tag
            results = self.bdb.search_by_tag("test, old - est")
            # Expect a list of five-element tuples containing all bookmark data
            # db index, URL, title, tags, description
            expected = [
                (
                    4,
                    "https://newbookmark.com",
                    "New Bookmark",
                    parse_tags([",test,old,new,"]),
                    "additional bookmark to test multiple tag search",
                    0,
                ),
                (
                    1,
                    "http://slashdot.org",
                    "SLASHDOT",
                    parse_tags([",news,old,"]),
                    "News for old nerds, stuff that doesn't matter",
                    0,
                ),
            ]
            self.assertEqual(results, expected)

    @pytest.mark.vcr("tests/vcr_cassettes/test_search_by_tags_enforces_space_seprations_exclusion.yaml")
    def test_search_by_tags_enforces_space_seprations_exclusion(self):

        bookmark1 = [
            "https://bookmark1.com",
            "Bookmark One",
            parse_tags(["tag, two,tag+two"]),
            "test case for bookmark with '+' in tag",
        ]

        bookmark2 = [
            "https://bookmark2.com",
            "Bookmark Two",
            parse_tags(["tag,two, tag-two"]),
            "test case for bookmark with hyphenated tag",
        ]

        bookmark3 = [
            "https://bookmark3.com",
            "Bookmark Three",
            parse_tags(["tag, tag three"]),
            "second test case for bookmark with hyphenated tag",
        ]

        self.bdb.add_rec(*bookmark1)
        self.bdb.add_rec(*bookmark2)
        self.bdb.add_rec(*bookmark3)

        with mock.patch("buku.prompt"):
            # check that space separation for ' - ' operator is enforced
            results = self.bdb.search_by_tag("tag-two")
            # Expect a list of five-element tuples containing all bookmark data
            # db index, URL, title, tags, description
            expected = [
                (
                    2,
                    "https://bookmark2.com",
                    "Bookmark Two",
                    parse_tags([",tag,two,tag-two,"]),
                    "test case for bookmark with hyphenated tag",
                    0,
                ),
            ]
            self.assertEqual(results, expected)
            results = self.bdb.search_by_tag("tag - two")
            # Expect a list of five-element tuples containing all bookmark data
            # db index, URL, title, tags, description
            expected = [
                (
                    3,
                    "https://bookmark3.com",
                    "Bookmark Three",
                    parse_tags([",tag,tag three,"]),
                    "second test case for bookmark with hyphenated tag",
                    0,
                ),
            ]
            self.assertEqual(results, expected)

    def test_search_and_open_in_browser_by_range(self):
        # adding bookmarks
        for bookmark in self.bookmarks:
            _add_rec(self.bdb, *bookmark)

        # simulate user input, select range of indices 1-3
        index_range = "1-%s" % len(self.bookmarks)
        with mock.patch("builtins.input", side_effect=[index_range]):
            with mock.patch("buku.browse") as mock_browse:
                try:
                    # search the db with keywords from each bookmark
                    # searching using the first tag from bookmarks
                    get_first_tag = lambda x: x[2].split(",")[1]
                    results = self.bdb.searchdb(
                        [get_first_tag(bm) for bm in self.bookmarks]
                    )
                    prompt(self.bdb, results)
                except StopIteration:
                    # catch exception thrown by reaching the end of the side effect iterable
                    pass

                # collect arguments passed to browse
                arg_list = [args[0] for args, _ in mock_browse.call_args_list]
                # expect a list of one-tuples that are bookmark URLs
                expected = [x[0] for x in self.bookmarks]
                # checking if browse called with expected arguments
                self.assertEqual(arg_list, expected)

    @pytest.mark.slow
    @pytest.mark.vcr("tests/vcr_cassettes/test_search_and_open_all_in_browser.yaml")
    def test_search_and_open_all_in_browser(self):
        # adding bookmarks
        for bookmark in self.bookmarks:
            self.bdb.add_rec(*bookmark)

        # simulate user input, select 'a' to open all bookmarks in results
        with mock.patch("builtins.input", side_effect=["a"]):
            with mock.patch("buku.browse") as mock_browse:
                try:
                    # search the db with keywords from each bookmark
                    # searching using the first tag from bookmarks
                    get_first_tag = lambda x: x[2].split(",")[1]
                    results = self.bdb.searchdb(
                        [get_first_tag(bm) for bm in self.bookmarks[:2]]
                    )
                    prompt(self.bdb, results)
                except StopIteration:
                    # catch exception thrown by reaching the end of the side effect iterable
                    pass

                # collect arguments passed to browse
                arg_list = [args[0] for args, _ in mock_browse.call_args_list]
                # expect a list of one-tuples that are bookmark URLs
                expected = [x[0] for x in self.bookmarks][:2]
                # checking if browse called with expected arguments
                self.assertEqual(arg_list, expected)

    def test_delete_rec(self):
        # adding bookmark and getting index
        _add_rec(self.bdb, *self.bookmarks[0])
        index = self.bdb.get_rec_id(self.bookmarks[0][0])
        # deleting bookmark
        self.bdb.delete_rec(index)
        # asserting it doesn't exist
        from_db = self.bdb.get_rec_by_id(index)
        self.assertIsNone(from_db)

    def test_delete_rec_yes(self):
        # checking that "y" response causes delete_rec to return True
        with mock.patch("builtins.input", return_value="y"):
            self.assertTrue(self.bdb.delete_rec(0))

    def test_delete_rec_no(self):
        # checking that non-"y" response causes delete_rec to return None
        with mock.patch("builtins.input", return_value="n"):
            self.assertFalse(self.bdb.delete_rec(0))

    def test_cleardb(self):
        # adding bookmarks
        _add_rec(self.bdb, *self.bookmarks[0])
        # deleting all bookmarks
        with mock.patch("builtins.input", return_value="y"):
            self.bdb.cleardb()
        # assert table has been dropped
        assert self.bdb.get_rec_by_id(0) is None

    def test_replace_tag(self):
        indices = []
        for bookmark in self.bookmarks:
            # adding bookmark, getting index
            _add_rec(self.bdb, *bookmark)
            index = self.bdb.get_rec_id(bookmark[0])
            indices += [index]

        # replacing tags
        with mock.patch("builtins.input", return_value="y"):
            self.bdb.replace_tag("news", ["__01"])
        with mock.patch("builtins.input", return_value="y"):
            self.bdb.replace_tag("zażółć", ["__02,__03"])

        # replacing tag which is also a substring of other tag
        with mock.patch("builtins.input", return_value="y"):
            self.bdb.replace_tag("es", ["__04"])

        # removing tags
        with mock.patch("builtins.input", return_value="y"):
            self.bdb.replace_tag("gęślą")
        with mock.patch("builtins.input", return_value="y"):
            self.bdb.replace_tag("old")

        # removing non-existent tag
        with mock.patch("builtins.input", return_value="y"):
            self.bdb.replace_tag("_")

        # removing nonexistent tag which is also a substring of other tag
        with mock.patch("builtins.input", return_value="y"):
            self.bdb.replace_tag("e")

        for url, title, _, _ in self.bookmarks:
            # retrieving from db
            index = self.bdb.get_rec_id(url)
            from_db = self.bdb.get_rec_by_id(index)
            # asserting tags were replaced
            if title == "SLASHDOT":
                self.assertEqual(from_db[3], parse_tags(["__01"]))
            elif title == "ZAŻÓŁĆ":
                self.assertEqual(from_db[3], parse_tags(["__02,__03,jaźń"]))
            elif title == "test":
                self.assertEqual(from_db[3], parse_tags(["test,tes,est,__04"]))

    def test_tnyfy_url(self):
        tny, full = 'http://tny.im/yt', 'https://www.google.com'
        # shorten a well-known url
        with mock_http(tny, status=200):
            shorturl = self.bdb.tnyfy_url(url=full, shorten=True)
        self.assertEqual(shorturl, tny)

        # expand a well-known short url
        with mock_http(full, status=200):
            url = self.bdb.tnyfy_url(url=tny, shorten=False)
        self.assertEqual(url, full)

    # def test_browse_by_index(self):
    # self.fail()

    def test_close_quit(self):
        # quitting with no args
        try:
            self.bdb.close_quit()
        except SystemExit as err:
            self.assertEqual(err.args[0], 0)
        # quitting with custom arg
        try:
            self.bdb.close_quit(1)
        except SystemExit as err:
            self.assertEqual(err.args[0], 1)

    # def test_import_bookmark(self):
    # self.fail()


@pytest.mark.parametrize('status', [None, 200, 302, 308, 404, 500])
@pytest.mark.parametrize('fetch, url_redirect, tag_redirect, tag_error, del_error', [
    (False, False, False, False, None),                # offline
    (True, True, False, False, None),                  # url-redirect
    (True, False, True, True, None),                   # tag-redirect, tag-error
    (True, True, 'http-{}', 'error:{}', None),         # url-redirect, fetch-tags (custom patterns)
    (True, True, 'redirect', 'error', None),           # ... (patterns without codes)
    (True, True, 'redirect', False, range(400, 600)),  # del-error (any errors)
    (True, True, 'redirect', 'error', {404}),          # ... (some errors)
])
def test_add_rec_fetch(bukuDb, caplog, fetch, url_redirect, tag_redirect, tag_error, del_error, status):
    '''Testing add_rec() behaviour with fetch-status params'''
    title_in, title, desc = 'Custom Title', 'Fetched Title', 'Fetched description.'
    tags_in, url_in, url_new = ',custom,tags,', 'https://example.com', 'https://example.com/redirect'
    url = (url_new if status in PERMANENT_REDIRECTS else url_in)
    bdb = bukuDb()
    with mock_fetch(url=url, title=title, desc=desc, fetch_status=status) as fetch_data:
        index = bdb.add_rec(url=url_in, title_in=title_in, tags_in=tags_in, fetch=fetch,
                            url_redirect=url_redirect, tag_redirect=tag_redirect,
                            tag_error=tag_error, del_error=del_error)

    # del-error?
    if del_error and (not status or status in del_error):
        assert index is None
        assert bdb.get_max_id() is None
        err = ('Network error' if not status else 'HTTP error {}'.format(status))
        assert caplog.record_tuples == [('root', 40, 'add_rec(): '+err)]
        return
    rec = bdb.get_rec_by_id(index)

    # offline?
    if not fetch:
        fetch_data.assert_not_called()
        assert (rec.url, rec.title, rec.desc) == (url_in, title_in, '')
        assert _tagset(rec.tags_raw) == _tagset(tags_in)
        return

    # url-redirect?
    if url_redirect and status in PERMANENT_REDIRECTS:
        assert rec.url == url_new
    else:
        assert rec.url == url_in

    # custom title, fetched description
    assert (rec.title, rec.desc) == (title_in, desc), 'custom title overrides fetched title'

    # fetch-tags?
    _tags = _tagset(tags_in)
    if tag_redirect and status in PERMANENT_REDIRECTS:
        _tags |= {('http:{}' if tag_redirect is True else tag_redirect).format(status).lower()}
    if tag_error and (status or 0) >= 400:
        _tags |= {('http:{}' if tag_error is True else tag_error).format(status).lower()}
    assert _tagset(rec.tags) == _tags


@pytest.mark.parametrize('status, tags_fetched, tags_in, tags_except, expected', [
    (None, None, 'foo,qux,foo bar,bar,baz', 'except,bar,foo,', ',baz,foo bar,qux,'),
    (200, '', 'foo,qux,foo bar,bar,baz', None, ',bar,baz,foo,foo bar,qux,'),
    (200, 'there,have been,some,tags,fetched', None,
     'except,bar,tags,there,foo', ',fetched,have been,some,'),
    (200, 'there,have been,some,tags,fetched', 'foo,qux,foo bar,bar,baz',
     'except,bar,tags,there,foo', ',baz,fetched,foo bar,have been,qux,some,'),
    (404, None, 'foo,foo bar,qux,bar,baz', 'except,bar,foo', ',baz,foo bar,http:error,qux,'),
    (301, 'there,have been,some,tags,fetched', 'foo,foo bar,qux,bar,baz',
     'except,bar,tags,there,foo', ',baz,fetched,foo bar,have been,http:redirect,qux,some,'),
    (308, 'there,have been,some,tags,fetched', 'foo,foo bar,qux,bar,baz',
     'except,http:redirect,bar,tags,there,foo', ',baz,fetched,foo bar,have been,qux,some,'),
])
def test_add_rec_tags(bukuDb, caplog, status, tags_fetched, tags_in, tags_except, expected):
    '''Testing add_rec() behaviour with tags params'''
    url, keywords = 'https://example.com', (',fetched,tags,' if tags_fetched is None else tags_fetched)
    bdb = bukuDb()
    with mock_fetch(url=url, title='Title', keywords=keywords, fetch_status=status):
        index = bdb.add_rec(url=url, fetch=status is not None, tags_in=tags_in, tags_except=tags_except,
                            tags_fetch=tags_fetched is not None, tag_redirect='http:redirect', tag_error='http:error')
    rec = bdb.get_rec_by_id(index)
    assert rec.tags_raw == expected


@pytest.mark.parametrize('index', [1, {2, 3}, None])
@pytest.mark.parametrize('export_on', [None, PERMANENT_REDIRECTS, range(400, 600), PERMANENT_REDIRECTS | {404}])
@pytest.mark.parametrize('url_in, title_in, tags_in, url_redirect, tag_redirect, tag_error, del_error', [
    (None, None, None, False, False, False, None),                                          # fetched title/desc, no network test
    (None, 'Custom Title', ',custom,tags,', False, False, False, None),                     # title, tags, no network test
    ('http://custom.url', None, None, False, False, False, None),                           # url, fetched title/desc, no network test
    ('http://custom.url', 'Custom Title', ',custom,tags,', False, False, False, None),      # url, title, tags, no network test
    (None, 'Custom Title', '+,custom,tags,', True, False, False, None),                     # title, +tags, url-redirect
    ('http://custom.url', 'Custom Title', '+,custom,tags,', False, True, True, None),       # url, title, +tags, fetch-tags
    (None, 'Custom Title', None, True, 'http-{}', 'error:{}', None),                        # title, url-redirect, fetch-tags (custom)
    (None, None, '-,initial%,', True, 'redirect', 'error', None),                           # -tags, url-redirect, fetch-tags (no codes)
    ('http://custom.url', 'Custom Title', None, True, 'redirect', False, range(400, 600)),  # url, title, url-redirect, del-error
    (None, None, ',custom,tags,', True, 'redirect', 'error', {404}),                        # tags, url-redirect, fetch-tags, del-error
])
def test_update_rec_fetch(bukuDb, caplog, url_in, title_in, tags_in, url_redirect, tag_redirect, tag_error, del_error, export_on, index):
    '''Testing update_rec() behaviour with fetch-status params'''
    # redirected URL, nonexistent page, nonexistend domain
    urls = {
        'http://wikipedia.net': {'fetch_status': 301, 'url': 'https://www.wikipedia.org', 'title': 'Wikipedia',
                                 'desc': 'Wikipedia is a free online encyclopedia, created and edited blah blah'},
        'https://python.org/notfound': {'fetch_status': 404, 'title': 'Welcome to Python.org',
                                        'desc': 'The official home of the Python Programming Language'},
        'http://nonexistent.url': {'fetch_status': None},  # unable to resolve host address
    }
    # for the URL override
    custom_url = {'fetch_status': 200, 'title': 'Fetched Title', 'desc': 'Fetched description.'}

    def custom_fetch(url, http_head=False):
        data = dict(urls.get(url, custom_url))
        _url = data.pop('url', url)
        return FetchResult(url_in or _url, **data)

    # computed test parameters
    title_initial, tags_initial, desc = 'Initial Title', ',initial%,tags,', 'Initial description.'
    fetch_title = title_in is tags_in is None  # when no custom params are passed (except for URL), titles are fetched
    network_test = url_redirect or tag_redirect or tag_error or del_error or export_on or fetch_title
    indices = ({index} if isinstance(index, int) else index or range(1, len(urls)+1))
    tags = _tagset(tags_in if (tags_in or '').startswith(',') else tags_initial)
    if not (tags_in or ',').startswith(','):
        tags = (tags | _tagset(tags_in[1:]) if tags_in.startswith('+') else tags - _tagset(tags_in[1:]))

    # setup
    bdb = bukuDb()
    for url_initial in urls:
        _add_rec(bdb, url_initial, title_in=title_initial, tags_in=tags_initial, desc=desc)
    assert bdb.get_max_id() == len(urls), 'expecting correct setup'
    with mock_fetch(custom_fetch) as fetch_data:
        with mock.patch('buku.read_in', return_value='y'):
            ok = bdb.update_rec(index=index, url=url_in, title_in=title_in, tags_in=tags_in,
                                url_redirect=url_redirect, tag_redirect=tag_redirect,
                                tag_error=tag_error, del_error=del_error, export_on=export_on)
    recs = bdb.get_rec_all()

    # custom URL on multiple records?
    if url_in and len(indices) != 1:
        assert not ok, 'expected to fail'
        assert caplog.record_tuples == [('root', 40, 'All URLs cannot be same')]
        fetch_data.assert_not_called()
        assert recs == [BookmarkVar(id, url, title_initial, tags_initial, desc)
                        for id, url in enumerate(urls, start=1)]
        return
    assert ok, 'expected to succeed'

    # offline?
    if not network_test and not (url_in and title_in is None):
        _tags = ',' + ','.join(sorted(tags)) + ','
        fetch_data.assert_not_called()
        for rec, url in zip(recs, urls):
            if rec.id in indices:
                assert rec == BookmarkVar(rec.id, url_in or url, title_in or title_initial, _tags, desc)
            else:
                assert rec == BookmarkVar(rec.id, url, title_initial, tags_initial, desc)
        return

    # export-on (given HTTP codes)?
    if not export_on:
        assert bdb._to_export is None, f'expected no to_export backup: {bdb._to_export}'
    else:
        assert isinstance(bdb._to_export, dict), f'to_export backup is not a dict: {bdb._to_export}'
    to_export = dict(bdb._to_export or {})
    _urls, _recs = set(urls), {x.url: x for x in recs}

    # one fetch per index
    assert fetch_data.call_count == len(indices), f'expected {len(indices)} fetches, done {fetch_data.call_count}'
    for call in fetch_data.call_args_list:
        # determining fetched, original and redirected URLs, along with fetched data
        url = call.args[0]
        url_old = url if not url_in else list(urls)[index-1]  # url_in applies to a single record
        _urls -= {url_old}
        data = urls.get(url, custom_url)
        url_new = (url if not url_redirect else data.get('url', url))
        rec = _recs.pop(url_new, None)
        status = data.get('fetch_status')

        # del-error? export-on?
        old = to_export.pop(url_new, None)
        if not export_on or status not in export_on:
            assert old is None, f'{url_old}: backup not expected'
        if del_error and status in del_error:
            assert rec is None, f'{url_old}: HTTP error {status}, should delete'
            if export_on and status in export_on:
                assert isinstance(old, BookmarkVar), f'{url_old}: should backup old record'
                assert (old.url, old.title, old.tags_raw, old.desc) == (url_old, title_initial, tags_initial, desc)
            continue
        if export_on and status in export_on:
            assert old == url_old, f'{url_old}: should backup old url on redirect'

        # url-redirect?
        if url_redirect and status in PERMANENT_REDIRECTS:
            assert url_new != url_old, f'{url_old}: redirect expected'
            assert rec.url == url_new, f'{url_old}: should replace with {url_new}'
        else:
            assert url_new == rec.url, f'{url_old}: redirect not expected'
            assert url_new == (url_in or url_old), f'{url_old}: URL should not be changed'

        # title
        if title_in or (fetch_title and 'title' in data):
            assert rec.title == (title_in or data['title']), f'{url_old}: should update title'
        else:
            assert rec.title == title_initial, f'{url_old}: should not update title'

        # description
        if fetch_title and 'desc' in data:
            assert rec.desc == data['desc'], f'{url_old}: should update description'
        else:
            assert rec.desc == desc, f'{url_old}: should not update description'

        # tags (+fetch-tags)
        _tags = set()
        if tag_redirect and status in PERMANENT_REDIRECTS:
            _tags |= {('http:{}' if tag_redirect is True else tag_redirect).format(status).lower()}
        elif tag_error and status in range(400, 600):
            _tags |= {('http:{}' if tag_error is True else tag_error).format(status).lower()}
        _tags_str = ',' + ','.join(sorted(_tags)) + ','
        assert _tagset(rec.tags) == tags | _tags, f'{url_old}: [{tags_initial} | {tags_in or ","} | {_tags_str}] -> {rec.tags}'

    # other records should not have been affected (other than possibly indices)
    assert not to_export, f'unexpected to_export backup: {to_export}'
    assert set(_recs) == _urls
    for rec in _recs.values():
        assert rec == BookmarkVar(rec.id, rec.url, title_initial, tags_initial, desc)


@pytest.mark.parametrize('ext, expected', [
    ('db', [(1, 'http://custom.url', 'Fetched Title (DELETED)', ',', 'Fetched description.'),
            (2, 'https://www.wikipedia.org', 'Wikipedia (OLD URL = http://wikipedia.net)', ',http:301,', 'Wikipedia is a free...'),
            (3, 'https://python.org/notfound', 'Welcome to Python.org', ',http:404,', 'The official home...')]),
    ('md', ['- [Fetched Title (DELETED)](http://custom.url)',
            '- [Wikipedia (OLD URL = http://wikipedia.net)](https://www.wikipedia.org) <!-- TAGS: http:301 -->',
            '- [Welcome to Python.org](https://python.org/notfound) <!-- TAGS: http:404 -->']),
    ('org', ['* [[http://custom.url][Fetched Title (DELETED)]]',
             '* [[https://www.wikipedia.org][Wikipedia (OLD URL = http://wikipedia.net)]] :http_301:',
             '* [[https://python.org/notfound][Welcome to Python.org]] :http_404:']),
    ('xbel', ['<?xml version="1.0" encoding="UTF-8"?>',
              '<!DOCTYPE xbel PUBLIC "+//IDN python.org//DTD XML Bookmark Exchange Language 1.0//EN//XML"'
                                   ' "http://pyxml.sourceforge.net/topics/dtds/xbel.dtd">',
              '',
              '<xbel version="1.0">',
              '    <bookmark href="http://custom.url">',
              '        <title>Fetched Title (DELETED)</title>',
              '        <desc>Fetched description.</desc>',
              '    </bookmark>',
              '    <bookmark href="https://www.wikipedia.org" TAGS="http:301">',
              '        <title>Wikipedia (OLD URL = http://wikipedia.net)</title>',
              '        <desc>Wikipedia is a free...</desc>',
              '    </bookmark>',
              '    <bookmark href="https://python.org/notfound" TAGS="http:404">',
              '        <title>Welcome to Python.org</title>',
              '        <desc>The official home...</desc>',
              '    </bookmark>',
              '</xbel>',]),
    ('html', ['<!DOCTYPE NETSCAPE-Bookmark-file-1>', '',
              '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
              '<TITLE>Bookmarks</TITLE>', '<H1>Bookmarks</H1>', '',
              '<DL><p>',
              '    <DT><H3 ADD_DATE="{0}" LAST_MODIFIED="{0}" PERSONAL_TOOLBAR_FOLDER="true">buku bookmarks</H3>',
              '    <DL><p>',
              '        <DT><A HREF="http://custom.url" ADD_DATE="{0}" LAST_MODIFIED="{0}">Fetched Title (DELETED)</A>',
              '        <DD>Fetched description.',
              '        <DT><A HREF="https://www.wikipedia.org" ADD_DATE="{0}" LAST_MODIFIED="{0}" '
                             'TAGS="http:301">Wikipedia (OLD URL = http://wikipedia.net)</A>',
              '        <DD>Wikipedia is a free...',
              '        <DT><A HREF="https://python.org/notfound" ADD_DATE="{0}" LAST_MODIFIED="{0}" '
                             'TAGS="http:404">Welcome to Python.org</A>',
              '        <DD>The official home...',
              '    </DL><p>',
              '</DL><p>']),
])
def test_export_on(bukuDb, ext, expected):
    '''Testing exportdb() behaviour after update_rec() with export_on'''
    outfile = TEST_TEMP_DIR_PATH + '/export-on.' + ext
    bdb = bukuDb()
    _add_rec(bdb, 'https://www.wikipedia.org', 'Wikipedia', ',http:301,', 'Wikipedia is a free...')
    _add_rec(bdb, 'https://python.org/notfound', 'Welcome to Python.org', ',http:404,', 'The official home...')
    _add_rec(bdb, 'https://nonexistent.url', 'Custom Title')                    # not exported
    to_export = {'http://custom.url': BookmarkVar(1, 'http://custom.url', 'Fetched Title', ',', 'Fetched description.'),  # deleted
                 'https://www.wikipedia.org': 'http://wikipedia.net',           # redirect
                 'https://python.org/notfound': 'https://python.org/notfound'}  # unchanged
    bdb._to_export = dict(to_export)
    bdb.exportdb(outfile, None)
    if ext == 'db':
        assert BukuDb(dbfile=outfile).get_rec_all() == list(bookmark_vars(expected))
    else:
        with open(outfile, encoding='utf-8') as fout:
            output = fout.read()
        match = re.search('ADD_DATE="([0-9]+)"', output)
        timestamp = match and match.group(1)
        assert output.splitlines() == [s.format(timestamp) for s in expected]


@pytest.fixture(scope="function")
def refreshdb_fixture():
    # Setup
    os.environ["XDG_DATA_HOME"] = TEST_TEMP_DIR_PATH

    # start every test from a clean state
    rmdb()

    bdb = BukuDb()

    yield bdb

    rmdb(bdb)
    # Teardown
    os.environ["XDG_DATA_HOME"] = TEST_TEMP_DIR_PATH


@pytest.mark.parametrize(
    "title_in, exp_res",
    [
        ["?", "Example Domain"],
        [None, "Example Domain"],
        ["", "Example Domain"],
        ["random title", "Example Domain"],
    ],
)
def test_refreshdb(refreshdb_fixture, title_in, exp_res):
    bdb = refreshdb_fixture
    args = ["http://example.com"]
    if title_in:
        args.append(title_in)
    _add_rec(bdb, *args)
    with mock_fetch(title=exp_res):
        bdb.refreshdb(1, 1)
    from_db = bdb.get_rec_by_id(1)
    assert from_db[2] == exp_res, "from_db: {}".format(from_db)


@pytest.fixture
def test_print_caplog(caplog):
    caplog.handler.records.clear()
    caplog.records.clear()
    yield caplog


@pytest.mark.parametrize(
    "kwargs, rec, exp_res",
    [
        [{}, TEST_PRINT_REC, (True, [])],
        [{"is_range": True}, TEST_PRINT_REC, (True, [])],
        [{"index": 0}, TEST_PRINT_REC, (True, [])],
        [{"index": -1}, TEST_PRINT_REC, (True, [])],
        [{"index": -2}, TEST_PRINT_REC, (True, [])],
        [{"index": 2}, TEST_PRINT_REC, (False, [("root", 40, "No matching index 2")])],
        [{"low": -1, "high": -1}, TEST_PRINT_REC, (True, [])],
        [
            {"low": -1, "high": -1, "is_range": True},
            TEST_PRINT_REC,
            (False, [("root", 40, "Negative range boundary")]),
        ],
        [{"low": 0, "high": 0, "is_range": True}, TEST_PRINT_REC, (True, [])],
        [{"low": 0, "high": 1, "is_range": True}, TEST_PRINT_REC, (True, [])],
        [{"low": 0, "high": 2, "is_range": True}, TEST_PRINT_REC, (True, [])],
        [{"low": 2, "high": 2, "is_range": True}, TEST_PRINT_REC, (True, [])],
        [{"low": 2, "high": 3, "is_range": True}, TEST_PRINT_REC, (True, [])],
        # empty database
        [{"is_range": True}, None, (True, [])],
        [{"index": 0}, None, (True, [("root", 40, "0 records")])],
        [{"index": -1}, None, (False, [("root", 40, "Empty database")])],
        [{"index": 1}, None, (False, [("root", 40, "No matching index 1")])],
        [{"low": -1, "high": -1}, TEST_PRINT_REC, (True, [])],
        [
            {"low": -1, "high": -1, "is_range": True},
            None,
            (False, [("root", 40, "Negative range boundary")]),
        ],
        [{"low": 0, "high": 0, "is_range": True}, None, (True, [])],
        [{"low": 0, "high": 1, "is_range": True}, None, (True, [])],
        [{"low": 0, "high": 2, "is_range": True}, None, (True, [])],
        [{"low": 2, "high": 2, "is_range": True}, None, (True, [])],
        [{"low": 2, "high": 3, "is_range": True}, None, (True, [])],
    ],
)
def test_print_rec(bukuDb, kwargs, rec, exp_res, tmp_path, caplog):
    bdb = bukuDb(dbfile=tmp_path / "tmp.db")
    if rec:
        _add_rec(bdb, *rec)
    # run the function
    assert (bdb.print_rec(**kwargs), caplog.record_tuples) == exp_res


def test_list_tags(capsys, bukuDb):
    bdb = bukuDb()

    # adding bookmarks
    _add_rec(bdb, "http://one.com", "", parse_tags(["cat,ant,bee,1"]), "")
    _add_rec(bdb, "http://two.com", "", parse_tags(["Cat,Ant,bee,1"]), "")
    _add_rec(bdb, "http://three.com", "", parse_tags(["Cat,Ant,3,Bee,2"]), "")

    # listing tags, asserting output
    out, err = capsys.readouterr()
    prompt(bdb, None, True, listtags=True)
    out, err = capsys.readouterr()
    exp_out = "     1. 1 (2)\n     2. 2 (1)\n     3. 3 (1)\n     4. ant (3)\n     5. bee (3)\n     6. cat (3)\n\n"
    assert out == exp_out
    assert err == ""


def test_compactdb(bukuDb):
    bdb = bukuDb()

    # adding bookmarks
    for bookmark in TEST_BOOKMARKS:
        _add_rec(bdb, *bookmark)

    # manually deleting 2nd index from db, calling compactdb
    bdb.cur.execute("DELETE FROM bookmarks WHERE id = ?", (2,))
    bdb.compactdb(2)

    # asserting bookmarks have correct indices
    assert bdb.get_rec_by_id(1) == (
        1,
        "http://slashdot.org",
        "SLASHDOT",
        ",news,old,",
        "News for old nerds, stuff that doesn't matter",
        0,
    )
    assert bdb.get_rec_by_id(2) == (
        2,
        "http://example.com/",
        "test",
        ",es,est,tes,test,",
        "a case for replace_tag test",
        0,
    )
    assert bdb.get_rec_by_id(3) is None


@pytest.mark.vcr()
@pytest.mark.parametrize(
    "low, high, delay_commit, input_retval, exp_res",
    [
        #  delay_commit, y input_retval
        [0, 0, True, "y", (True, [])],
        #  delay_commit, non-y input_retval
        [
            0,
            0,
            True,
            "x",
            (
                False,
                [tuple([x] + y + [0]) for x, y in zip(range(1, 4), TEST_BOOKMARKS)],
            ),
        ],
        #  non delay_commit, y input_retval
        [0, 0, False, "y", (True, [])],
        #  non delay_commit, non-y input_retval
        [
            0,
            0,
            False,
            "x",
            (
                False,
                [tuple([x] + y + [0]) for x, y in zip(range(1, 4), TEST_BOOKMARKS)],
            ),
        ],
    ],
)
def test_delete_rec_range_and_delay_commit(
    bukuDb, tmp_path, low, high, delay_commit, input_retval, exp_res
):
    """test delete rec, range and delay commit."""
    bdb = bukuDb(dbfile=tmp_path / "tmp.db")
    kwargs = {"is_range": True, "low": low, "high": high, "delay_commit": delay_commit}
    kwargs["index"] = 0

    # Fill bookmark
    for bookmark in TEST_BOOKMARKS:
        _add_rec(bdb, *bookmark)

    with mock.patch("builtins.input", return_value=input_retval):
        res = bdb.delete_rec(**kwargs)

    assert (res, bdb.get_rec_all()) == exp_res

    # teardown
    os.environ["XDG_DATA_HOME"] = TEST_TEMP_DIR_PATH


@pytest.mark.parametrize(
    "index, delay_commit, input_retval",
    [
        [-1, False, False],
        [0, False, False],
        [1, False, True],
        [1, False, False],
        [1, True, True],
        [1, True, False],
        [100, False, True],
    ],
)
def test_delete_rec_index_and_delay_commit(bukuDb, index, delay_commit, input_retval):
    """test delete rec, index and delay commit."""
    bdb = bukuDb()
    bdb_dc = bukuDb()  # instance for delay_commit check.

    # Fill bookmark
    for bookmark in TEST_BOOKMARKS:
        _add_rec(bdb, *bookmark)
    db_len = len(TEST_BOOKMARKS)

    n_index = index

    with mock.patch("builtins.input", return_value=input_retval):
        res = bdb.delete_rec(index=index, delay_commit=delay_commit)

    if n_index < 0:
        assert not res
    elif n_index > db_len:
        assert not res
        assert len(bdb.get_rec_all()) == db_len
    elif index == 0 and not input_retval:
        assert not res
        assert len(bdb.get_rec_all()) == db_len
    else:
        assert res
        assert len(bdb.get_rec_all()) == db_len - 1
        if delay_commit:
            assert len(bdb_dc.get_rec_all()) == db_len
        else:
            assert len(bdb_dc.get_rec_all()) == db_len - 1

    # teardown
    os.environ["XDG_DATA_HOME"] = TEST_TEMP_DIR_PATH


@pytest.mark.parametrize(
    "index, is_range, low, high",
    [
        # range on non zero index
        (0, True, 1, 1),
        # range on zero index
        (0, True, 0, 0),
        # zero index only
        (0, False, 0, 0),
    ],
)
def test_delete_rec_on_empty_database(bukuDb, index, is_range, low, high):
    """test delete rec, on empty database."""
    bdb = bukuDb()
    with mock.patch("builtins.input", return_value="y"):
        res = bdb.delete_rec(index, is_range, low, high)

    if (is_range and any([low == 0, high == 0])) or (not is_range and index == 0):
        assert res
        # teardown
        os.environ["XDG_DATA_HOME"] = TEST_TEMP_DIR_PATH
        return

    if is_range and low > 1 and high > 1:
        assert not res

    # teardown
    os.environ["XDG_DATA_HOME"] = TEST_TEMP_DIR_PATH


@pytest.mark.parametrize(
    "kwargs, exp_res, raise_error",
    [
        [{"index": 'a', "low": 'a', "high": 1, "is_range": True}, None, True],
        [{"index": 'a', "low": 'a', "high": 1, "is_range": False}, None, True],
        [{"index": 'a', "low": 1, "high": 'a', "is_range": True}, None, True],
        [{"index": 'a', "is_range": False}, None, True],
        [{"index": 'a', "is_range": True}, None, True],
    ],
)
def test_delete_rec_on_non_integer(
    bukuDb, tmp_path, monkeypatch, kwargs, exp_res, raise_error
):
    """test delete rec on non integer arg."""
    import buku

    bdb = bukuDb(dbfile=tmp_path / "tmp.db")

    for bookmark in TEST_BOOKMARKS:
        _add_rec(bdb, *bookmark)

    def mockreturn():
        return "y"

    exp_res = None
    res = None
    monkeypatch.setattr(buku, "read_in", mockreturn)
    if raise_error:
        with pytest.raises(TypeError):
            res = bdb.delete_rec(**kwargs)
    else:
        res = bdb.delete_rec(**kwargs)
    assert res == exp_res


@pytest.mark.parametrize("url", ["", False, None, 0])
def test_add_rec_add_invalid_url(bukuDb, caplog, url):
    """test method."""
    bdb = bukuDb()
    res = _add_rec(bdb, url=url)
    assert res is None
    caplog.records[0].levelname == "ERROR"
    caplog.records[0].getMessage() == "Invalid URL"


@pytest.mark.parametrize(
    "kwargs, exp_arg",
    [
        [{"url": "example.com"}, ("example.com", "Example Domain", ",", "", False)],
        [
            {"url": "http://example.com"},
            ("http://example.com", "Example Domain", ",", "", False),
        ],
        [
            {"url": "http://example.com", "immutable": True},
            ("http://example.com", "Example Domain", ",", "", True),
        ],
        [
            {"url": "http://example.com", "desc": "randomdesc"},
            ("http://example.com", "Example Domain", ",", "randomdesc", False),
        ],
        [
            {"url": "http://example.com", "title_in": "randomtitle"},
            ("http://example.com", "randomtitle", ",", "", False),
        ],
        [
            {"url": "http://example.com", "tags_in": "tag1"},
            ("http://example.com", "Example Domain", ",tag1,", "", False),
        ],
        [
            {"url": "http://example.com", "tags_in": ",tag1"},
            ("http://example.com", "Example Domain", ",tag1,", "", False),
        ],
        [
            {"url": "http://example.com", "tags_in": ",tag1,"},
            ("http://example.com", "Example Domain", ",tag1,", "", False),
        ],
    ],
)
def test_add_rec_exec_arg(bukuDb, kwargs, exp_arg):
    """test func."""
    bdb = bukuDb()
    _cur = bdb.cur
    try:
        bdb.cur = mock.Mock()
        bdb.get_rec_id = mock.Mock(return_value=None)
        with mock_fetch(title=exp_arg[1]):
            bdb.add_rec(**kwargs)
        assert bdb.cur.execute.call_args[0][1] == exp_arg
    finally:
        bdb.cur = _cur


def test_update_rec_index_0(bukuDb, caplog):
    """test method."""
    bdb = bukuDb()
    res = bdb.update_rec(index=0, url="http://example.com")
    assert not res
    assert caplog.records[0].getMessage() == "All URLs cannot be same"
    assert caplog.records[0].levelname == "ERROR"


@pytest.mark.parametrize(
    "kwargs, exp_res",
    [
        [{"index": 1}, False],
        [{"index": 1, "url": 'url'}, False],
        [{"index": 1, "url": ''}, False],
    ],
)
def test_update_rec(bukuDb, tmp_path, kwargs, exp_res):
    bdb = bukuDb(tmp_path / "tmp.db")
    res = bdb.update_rec(**kwargs)
    assert res == exp_res


@pytest.mark.parametrize("invalid_tag", ["+,", "-,"])
def test_update_rec_invalid_tag(bukuDb, caplog, invalid_tag):
    """test method."""
    url = "http://example.com"
    bdb = bukuDb()
    res = bdb.update_rec(index=1, url=url, tags_in=invalid_tag)
    assert not res
    assert caplog.records[0].getMessage() == "Please specify a tag"
    assert caplog.records[0].levelname == "ERROR"


@pytest.mark.parametrize(
    "read_in_retval, exp_res, record_tuples",
    [
        ["y", False, [("root", 40, "No matches found")]],
        ["n", False, []],
        ["", False, []],
    ],
)
def test_update_rec_update_all_bookmark(
    caplog, tmp_path, bukuDb, read_in_retval, exp_res, record_tuples
):
    """test method."""
    with mock.patch("buku.read_in", return_value=read_in_retval):
        bdb = bukuDb(tmp_path / "tmp.db")
        res = bdb.update_rec(index=0, tags_in="tags1")
        assert (res, caplog.record_tuples) == (exp_res, record_tuples)


@pytest.mark.parametrize(
    "get_system_editor_retval, index, exp_res",
    [
        ["none", 0, False],
        ["nano", -2, False],
    ],
)
def test_edit_update_rec_with_invalid_input(bukuDb, get_system_editor_retval, index, exp_res):
    """test method."""
    with mock.patch("buku.get_system_editor", return_value=get_system_editor_retval):
        assert bukuDb().edit_update_rec(index=index) == exp_res


@pytest.mark.vcr("tests/vcr_cassettes/test_browse_by_index.yaml")
@given(
    low=st.integers(min_value=-2, max_value=3),
    high=st.integers(min_value=-2, max_value=3),
    index=st.integers(min_value=-2, max_value=3),
    is_range=st.booleans(),
    empty_database=st.booleans(),
)
@example(low=0, high=0, index=0, is_range=False, empty_database=True)
@settings(max_examples=2, deadline=None)
def test_browse_by_index(low, high, index, is_range, empty_database):
    """test method."""
    n_low, n_high = (high, low) if low > high else (low, high)
    with mock.patch("buku.browse"):
        import buku

        bdb = buku.BukuDb(TEST_TEMP_DBFILE_PATH)
        try:
            bdb.delete_rec_all()
            db_len = 0
            if not empty_database:
                bdb.add_rec("https://www.google.com/ncr", "?")
                db_len += 1
            res = bdb.browse_by_index(index=index, low=low, high=high, is_range=is_range)
            if is_range and (low < 0 or high < 0):
                assert not res
            elif is_range and n_low > 0 and n_high > 0:
                assert res
            elif is_range:
                assert not res
            elif not is_range and index < 0:
                assert not res
            elif not is_range and index > db_len:
                assert not res
            elif not is_range and index >= 0 and empty_database:
                assert not res
            elif not is_range and 0 <= index <= db_len and not empty_database:
                assert res
            else:
                raise ValueError
        finally:
            rmdb(bdb)


@pytest.fixture()
def chrome_db():
    # compatibility
    dir_path = os.path.dirname(os.path.realpath(__file__))
    res_yaml_file = os.path.join(dir_path, "test_bukuDb", "25491522_res.yaml")
    res_nopt_yaml_file = os.path.join(dir_path, "test_bukuDb", "25491522_res_nopt.yaml")
    json_file = os.path.join(dir_path, "test_bukuDb", "Bookmarks")
    return json_file, res_yaml_file, res_nopt_yaml_file


@pytest.mark.parametrize("add_pt", [True, False])
def test_load_chrome_database(bukuDb, chrome_db, add_pt):
    """test method."""
    # compatibility
    json_file = chrome_db[0]
    res_yaml_file = chrome_db[1] if add_pt else chrome_db[2]
    dump_data = False  # NOTE: change this value to dump data
    if not dump_data:
        with open(res_yaml_file, "r", encoding="utf8", errors="surrogateescape") as f:
            try:
                res_yaml = yaml.load(f, Loader=yaml.FullLoader)
            except RuntimeError:
                res_yaml = yaml.load(f, Loader=PrettySafeLoader)
    # init
    bdb = bukuDb()
    bdb.add_rec = mock.Mock()
    bdb.load_chrome_database(json_file, None, add_pt)
    call_args_list_dict = dict(bdb.add_rec.call_args_list)
    # test
    if not dump_data:
        assert call_args_list_dict == res_yaml
    # dump data for new test
    if dump_data:
        with open(res_yaml_file, "w", encoding="utf8", errors="surrogateescape") as f:
            yaml.dump(call_args_list_dict, f)
        print("call args list dict dumped to:{}".format(res_yaml_file))


@pytest.fixture()
def firefox_db(tmpdir):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    res_yaml_file = os.path.join(dir_path, "test_bukuDb", "firefox_res.yaml")
    res_nopt_yaml_file = os.path.join(dir_path, "test_bukuDb", "firefox_res_nopt.yaml")
    ff_db_path = os.path.join(dir_path, "test_bukuDb", "places.sqlite")
    if not os.path.isfile(ff_db_path):
        db = sqlite3.connect(ff_db_path)
        with open(os.path.join(dir_path, 'test_bukuDb', 'places.sql'), encoding='utf-8') as sql:
            db.cursor().executescript(sql.read())
        db.commit()
    return ff_db_path, res_yaml_file, res_nopt_yaml_file


@pytest.mark.parametrize("add_pt", [True, False])
def test_load_firefox_database(bukuDb, firefox_db, add_pt):
    # compatibility
    ff_db_path = firefox_db[0]
    dump_data = False  # NOTE: change this value to dump data
    res_yaml_file = firefox_db[1] if add_pt else firefox_db[2]
    if not dump_data:
        with open(res_yaml_file, "r", encoding="utf8", errors="surrogateescape") as f:
            res_yaml = yaml.load(f, Loader=PrettySafeLoader)
    # init
    bdb = bukuDb()
    bdb.add_rec = mock.Mock()
    bdb.load_firefox_database(ff_db_path, None, add_pt)
    call_args_list_dict = dict(bdb.add_rec.call_args_list)
    # test
    if not dump_data:
        assert call_args_list_dict == res_yaml
    if dump_data:
        with open(res_yaml_file, "w", encoding="utf8", errors="surrogateescape") as f:
            yaml.dump(call_args_list_dict, f)
        print("call args list dict dumped to:{}".format(res_yaml_file))


@pytest.mark.parametrize('ignore_case, fields, expected', [
    (True, ['+id'],
     ['http://slashdot.org', 'http://www.zażółćgęśląjaźń.pl/', 'http://example.com/',
      'javascript:void(0)', 'javascript:void(1)', 'example.com/#']),
    (True, [],
     ['http://slashdot.org', 'http://www.zażółćgęśląjaźń.pl/', 'http://example.com/',
      'javascript:void(0)', 'javascript:void(1)', 'example.com/#']),
    (True, ['-metadata', '+netloc', '-url', 'id'],
     ['http://www.zażółćgęśląjaźń.pl/', 'http://example.com/', 'example.com/#',
      'http://slashdot.org', 'javascript:void(1)', 'javascript:void(0)']),
    (False, ['-metadata', '+netloc', 'url', 'id'],
     ['example.com/#', 'http://example.com/', 'javascript:void(0)',
      'javascript:void(1)', 'http://www.zażółćgęśląjaźń.pl/', 'http://slashdot.org']),
    (True, ['+title', '-tags', 'description', 'index', 'uri'],
     ['javascript:void(1)', 'javascript:void(0)', 'http://slashdot.org',
      'http://example.com/', 'example.com/#', 'http://www.zażółćgęśląjaźń.pl/']),
])
def test_sort(bukuDb, fields, ignore_case, expected):
    _bookmarks = (TEST_BOOKMARKS + [(f'javascript:void({i})', 'foo', parse_tags([f'tag{i}']), 'stuff') for i in range(2)] +
                  [('example.com/#', 'test', parse_tags(['test,tes,est,es']), 'a case for replace_tag test')])
    bookmarks = [(i,) + tuple(x) for i, x in enumerate(_bookmarks, start=1)]
    shuffle(bookmarks)  # making sure sorting by index works as well
    assert [x.url for x in bukuDb()._sort(bookmarks, fields, ignore_case=ignore_case)] == expected

@pytest.mark.parametrize('ignore_case, fields, expected', [
    (True, ['+id'], 'id ASC'),
    (True, [], 'id ASC'),
    (False, ['-metadata', '+netloc', 'url', 'id'], 'metadata DESC, LOWER(NETLOC(url)) ASC, url ASC, id ASC'),
    (True, ['-metadata', '+netloc', '-url', 'id'], 'LOWER(metadata) DESC, LOWER(NETLOC(url)) ASC, LOWER(url) DESC, id ASC'),
    (False, ['+title', '-tags', 'description', 'index', 'uri'], 'metadata ASC, tags DESC, desc ASC, id ASC, url ASC'),
    (True, ['+title', '-tags', 'description', 'index', 'uri'],
     'LOWER(metadata) ASC, LOWER(tags) DESC, LOWER(desc) ASC, id ASC, LOWER(url) ASC'),
])
def test_order(bukuDb, fields, ignore_case, expected):
    assert bukuDb()._order(fields, ignore_case=ignore_case) == expected

@pytest.mark.parametrize('order, expected', [
    (['netloc'], ['http://example.com/', 'https://example.com', '//example.com#',
                  'example.com?', 'http://slashdot.org', 'http://www.zażółćgęśląjaźń.pl/']),
    (['-netloc'], ['http://www.zażółćgęśląjaźń.pl/', 'http://slashdot.org', 'http://example.com/',
                   'https://example.com', '//example.com#', 'example.com?']),
    (['netloc', 'url'], ['//example.com#', 'example.com?', 'http://example.com/',
                         'https://example.com', 'http://slashdot.org', 'http://www.zażółćgęśląjaźń.pl/']),
    (['netloc', '-url'], ['https://example.com', 'http://example.com/', 'example.com?',
                          '//example.com#', 'http://slashdot.org', 'http://www.zażółćgęśląjaźń.pl/']),
])
def test_order_by_netloc(bukuDb, order, expected):
    bdb = bukuDb()
    _EXTRA = ['https://example.com', '//example.com#', 'example.com?']
    for bookmark in (TEST_BOOKMARKS + [(url, 'test', parse_tags(['test,tes,est,es']), 'a case for replace_tag test') for url in _EXTRA]):
        _add_rec(bdb, *bookmark)
    assert [x.url for x in bdb.get_rec_all(order=order)] == expected

@pytest.mark.parametrize('keyword, params, expected', [
    ('', {}, []),
    ('', {'markers': True}, []),
    ('*', {'markers': True}, []),
    (':', {'markers': True}, []),
    ('>', {'markers': True}, []),
    ('#', {'markers': True}, []),
    ('#,', {'markers': True}, []),
    ('# ,, ,', {'markers': True}, []),
    ('#, ,, ,', {'markers': True}, []),
    ('foo, bar?, , baz', {'regex': True}, [
        ('metadata', False, 'foo, bar?, , baz'), ('url', False, 'foo, bar?, , baz'),
        ('desc', False, 'foo, bar?, , baz'), ('tags', False, 'foo, bar?, , baz'),
    ]),
    ('foo, bar?, , baz', {}, [
        ('metadata', False, 'foo, bar?, , baz'), ('url', False, 'foo, bar?, , baz'),
        ('desc', False, 'foo, bar?, , baz'), ('tags', False, 'bar?', 'baz', 'foo'),
    ]),
    ('foo, bar?, , baz', {'deep': True}, [
        ('metadata', True, 'foo, bar?, , baz'), ('url', True, 'foo, bar?, , baz'),
        ('desc', True, 'foo, bar?, , baz'), ('tags', True, 'bar?', 'baz', 'foo'),
    ]),
    ('foo, bar?, , baz', {'markers': True}, [
        ('metadata', False, 'foo, bar?, , baz'), ('url', False, 'foo, bar?, , baz'),
        ('desc', False, 'foo, bar?, , baz'), ('tags', False, 'bar?', 'baz', 'foo'),
    ]),
    ('foo, bar?, , baz', {'deep': True, 'markers': True}, [
        ('metadata', True, 'foo, bar?, , baz'), ('url', True, 'foo, bar?, , baz'),
        ('desc', True, 'foo, bar?, , baz'), ('tags', True, 'bar?', 'baz', 'foo'),
    ]),
    ('*foo, bar?, , baz', {'markers': True}, [
        ('metadata', False, 'foo, bar?, , baz'), ('url', False, 'foo, bar?, , baz'),
        ('desc', False, 'foo, bar?, , baz'), ('tags', False, 'bar?', 'baz', 'foo'),
    ]),
    ('*foo, bar?, , baz', {'deep': True, 'markers': True}, [
        ('metadata', True, 'foo, bar?, , baz'), ('url', True, 'foo, bar?, , baz'),
        ('desc', True, 'foo, bar?, , baz'), ('tags', True, 'bar?', 'baz', 'foo'),
    ]),
    ('.foo, bar?, , baz', {'markers': True}, [('metadata', False, 'foo, bar?, , baz')]),
    ('.foo, bar?, , baz', {'deep': True, 'markers': True}, [('metadata', True, 'foo, bar?, , baz')]),
    (':foo, bar?, , baz', {'markers': True}, [('url', False, 'foo, bar?, , baz')]),
    (':foo, bar?, , baz', {'deep': True, 'markers': True}, [('url', True, 'foo, bar?, , baz')]),
    ('>foo, bar?, , baz', {'markers': True}, [('desc', False, 'foo, bar?, , baz')]),
    ('>foo, bar?, , baz', {'deep': True, 'markers': True}, [('desc', True, 'foo, bar?, , baz')]),
    ('#foo, bar?, , baz', {'markers': True}, [('tags', True, 'bar?', 'baz', 'foo')]),
    ('#foo, bar?, , baz', {'deep': True, 'markers': True}, [('tags', True, 'bar?', 'baz', 'foo')]),
    ('#foo, bar?, , baz', {'regex': True, 'markers': True}, [('tags', True, 'foo, bar?, , baz')]),
    ('#,foo, bar?, , baz', {'markers': True}, [('tags', False, 'bar?', 'baz', 'foo')]),
    ('#,foo, bar?, , baz', {'deep': True, 'markers': True}, [('tags', False, 'bar?', 'baz', 'foo')]),
    ('#,foo, bar?, , baz', {'regex': True, 'markers': True}, [('tags', False, 'foo, bar?, , baz')]),
])
def test_search_tokens(bukuDb, keyword, params, expected):
    assert bukuDb()._search_tokens(keyword, **params) == expected

@pytest.mark.parametrize('regex, tokens, args, clauses', [
    (True, [], [], ''),
    (True, [('metadata', False, 'foo, bar?, , baz')], [r'foo, bar?, , baz'], 'metadata REGEXP ?'),   # escape manually
    (True, [('tags', False, 'foo, bar?, , baz')], [r'foo, bar?, , baz'], 'tags REGEXP ?'),  # specify borders manually
    (True, [('metadata', False, 'foo, bar?, , baz'), ('url', False, 'foo, bar?, , baz'),
            ('desc', False, 'foo, bar?, , baz'), ('tags', False, 'foo, bar?, , baz')],
     [r'foo, bar?, , baz']*4, 'metadata REGEXP ? OR url REGEXP ? OR desc REGEXP ? OR tags REGEXP ?'),
    (False, [], [], ''),
    (False, [('desc', False, 'foo, bar?, , baz')], [r'\bfoo,\ bar\?,\ ,\ baz\b'], 'desc REGEXP ?'),
    (False, [('desc', True, 'foo, bar?, , baz')], ['foo, bar?, , baz'], "desc LIKE ('%' || ? || '%')"),
    (False, [('tags', False, 'bar?', 'baz', 'foo')], [r',bar\?,', r',baz,', r',foo,'],
     '(tags REGEXP ? AND tags REGEXP ? AND tags REGEXP ?)'),
    (False, [('tags', True, 'bar?', 'baz', 'foo')], ['bar?', 'baz', 'foo'],
     "(tags LIKE ('%' || ? || '%') AND tags LIKE ('%' || ? || '%') AND tags LIKE ('%' || ? || '%'))"),
    (False, [('metadata', False, 'foo, bar?, , baz'), ('url', False, 'foo, bar?, , baz'),
             ('desc', False, 'foo, bar?, , baz'), ('tags', False, 'bar?', 'baz', 'foo')],
     [r'\bfoo,\ bar\?,\ ,\ baz\b']*3 + [r',bar\?,', r',baz,', r',foo,'],
     'metadata REGEXP ? OR url REGEXP ? OR desc REGEXP ? OR (tags REGEXP ? AND tags REGEXP ? AND tags REGEXP ?)'),
    (False, [('metadata', True, 'foo, bar?, , baz'), ('url', True, 'foo, bar?, , baz'),
             ('desc', True, 'foo, bar?, , baz'), ('tags', True, 'bar?', 'baz', 'foo')],
     ['foo, bar?, , baz']*3 + ['bar?', 'baz', 'foo'],
     "metadata LIKE ('%' || ? || '%') OR url LIKE ('%' || ? || '%') OR desc LIKE ('%' || ? || '%')"
     " OR (tags LIKE ('%' || ? || '%') AND tags LIKE ('%' || ? || '%') AND tags LIKE ('%' || ? || '%'))"),
])
def test_search_clause(bukuDb, regex, tokens, args, clauses):
    assert bukuDb()._search_clause(tokens, regex=regex) == (clauses, args)

@pytest.mark.parametrize('keywords, params, expected', [
    (['slashdot'], {}, ['http://slashdot.org']),
    (['slashdot|example'], {'regex': True}, ['http://slashdot.org', 'http://example.com/']),
    (['slashdot|example'], {'regex': True, 'order': ['-title']}, ['http://example.com/', 'http://slashdot.org']),
    (['old,news,old'], {}, ['http://slashdot.org']),  # tags matching
    (['bold,news,old'], {}, []),  # ALL tags within a token must match
    (['#test'], {'markers': True}, ['http://example.com/']),
    (['#es,test'], {'markers': True}, ['http://example.com/']),
    (['#te'], {'markers': True}, ['http://example.com/']),
    (['#,te'], {'markers': True}, []),
    (['#,es'], {'markers': True}, ['http://example.com/']),
    (['#,es,te'], {'markers': True}, []),  # ALL tags within a token must match
    (['>for', ':com'], {'markers': True, 'all_keywords': True}, ['http://example.com/']),
    (['>for', ':com'], {'markers': True, 'all_keywords': False}, ['http://example.com/', 'http://slashdot.org']),
    (['>test'], {'markers': True, 'deep': False}, ['http://example.com/']),
    (['>test'], {'markers': True, 'deep': True, 'order': ['title']}, ['http://example.com/', 'http://www.zażółćgęśląjaźń.pl/']),
])
def test_searchdb(bukuDb, keywords, params, expected):
    bdb = bukuDb()
    for bookmark in TEST_BOOKMARKS:
        _add_rec(bdb, *bookmark)
    assert [x.url for x in bdb.searchdb(keywords, **params)] == expected


@pytest.mark.parametrize('keyword_results, stag_results, exp_res', [
    ([], [], []),
    (["item1"], ["item1", "item2"], ["item1"]),
    (["item2"], ["item1"], []),
])
def test_search_keywords_and_filter_by_tags(bukuDb, keyword_results, stag_results, exp_res):
    with mock.patch('buku.BukuDb.searchdb', return_value=keyword_results):
        with mock.patch('buku.BukuDb.search_by_tag', return_value=stag_results):
            assert exp_res == bukuDb().search_keywords_and_filter_by_tags(['keywords'], stag=['stag'])


@pytest.mark.parametrize('search_results, exclude_results, exp_res', [
    ([], [], []),
    (["item1", "item2"], ["item2"], ["item1"]),
    (["item2"], ["item1"], ["item2"]),
    (["item1", "item2"], ["item1", "item2"], []),
])
def test_exclude_results_from_search(bukuDb, search_results, exclude_results, exp_res):
    with mock.patch('buku.BukuDb.searchdb', return_value=exclude_results):
        assert exp_res == bukuDb().exclude_results_from_search(search_results, ['without'])


def test_exportdb_empty_db():
    with NamedTemporaryFile(delete=False) as f:
        db = BukuDb(dbfile=f.name)
        with NamedTemporaryFile(delete=False) as f2:
            res = db.exportdb(f2.name)
            assert not res


def test_exportdb_single_rec(tmpdir):
    f1 = NamedTemporaryFile(delete=False)
    f1.close()
    db = BukuDb(dbfile=f1.name)
    _add_rec(db, "http://example.com")
    exp_file = tmpdir.join("export")
    db.exportdb(exp_file.strpath)
    with open(exp_file.strpath, encoding="utf8", errors="surrogateescape") as f2:
        assert f2.read()


def test_exportdb_to_db():
    f1 = NamedTemporaryFile(delete=False)
    f1.close()
    f2 = NamedTemporaryFile(delete=False, suffix=".db")
    f2.close()
    db = BukuDb(dbfile=f1.name)
    _add_rec(db, "http://example.com")
    _add_rec(db, "http://google.com")
    with mock.patch("builtins.input", return_value="y"):
        db.exportdb(f2.name)
    db2 = BukuDb(dbfile=f2.name)
    assert db.get_rec_all() == db2.get_rec_all()


@pytest.mark.parametrize('pick', [None, 0, 3, 7, 10])
@mock.patch('builtins.print')
@mock.patch('builtins.open')
@mock.patch('random.sample')
@mock.patch('buku.convert_bookmark_set')
@mock.patch('buku.BukuDb._sort')
def test_exportdb_pick(_bukudb_sort, _convert_bookmark_set, _sample, _open, _print, bukuDb, pick):
    wrap = mock.Mock()
    wrap.attach_mock(_print, 'print')
    wrap.attach_mock(_open, 'open')
    wrap.attach_mock(_sample, 'sample')
    wrap.attach_mock(_convert_bookmark_set, 'convert_bookmark_set')
    wrap.attach_mock(_bukudb_sort, 'BukuDb_sort')
    _sample.return_value = _sampled = object()
    _bukudb_sort.return_value = _selection = object()
    _convert_bookmark_set.return_value = _converted = {'data': object(), 'count': 42}
    filepath, order, records, picked = 'output.md', object(), range(7), pick and pick < 7

    bdb = bukuDb()
    assert bdb.exportdb(filepath, records, order=order, pick=pick)
    pick_expected = [mock.call.sample(records, pick),
                     mock.call.BukuDb_sort(_sampled, order)]
    expected_calls = [mock.call.open(filepath, mode='w', encoding='utf-8'),
                      mock.call.open().__enter__(),                            # pylint: disable=unnecessary-dunder-call
                      mock.call.convert_bookmark_set((_selection if picked else records), 'markdown', {}),
                      mock.call.open().__enter__().write(_converted['data']),  # pylint: disable=unnecessary-dunder-call
                      mock.call.print('42 exported'),
                      mock.call.open().__exit__(None, None, None)]
    assert wrap.mock_calls == ([] if not picked else pick_expected) + expected_calls


@pytest.mark.parametrize(
    "urls, exp_res",
    [
        [[], None],
        [["http://example.com"], 1],
        [["http://example.com", "http://google.com"], 2],
    ],
)
def test_get_max_id(urls, exp_res):
    with NamedTemporaryFile(delete=False) as f:
        db = BukuDb(dbfile=f.name)
        if urls:
            list(map(lambda x: _add_rec(db, x), urls))
        assert db.get_max_id() == exp_res


# Helper functions for testcases


def split_and_test_membership(a, b):
    # :param a, b: comma separated strings to split
    # test everything in a in b
    return all(x in b.split(",") for x in a.split(","))


def inclusive_range(start, end):
    return list(range(start, end + 1))


def normalize_range(db_len, low, high):
    """normalize index and range.

    Args:
        db_len (int): database length.
        low (int): low limit.
        high (int): high limit.

    Returns:
        Tuple contain following normalized variables (low, high)
    """
    require_comparison = True
    # don't deal with non instance of the variable.
    if not isinstance(low, int):
        n_low = low
        require_comparison = False
    if not isinstance(high, int):
        n_high = high
        require_comparison = False

    max_value = db_len
    if low == "max" and high == "max":
        n_low = db_len
        n_high = max_value
    elif low == "max" and high != "max":
        n_low = high
        n_high = max_value
    elif low != "max" and high == "max":
        n_low = low
        n_high = max_value
    else:
        n_low = low
        n_high = high

    if require_comparison:
        if n_high < n_low:
            n_high, n_low = n_low, n_high

    return (n_low, n_high)


if __name__ == "__main__":
    unittest.main()
