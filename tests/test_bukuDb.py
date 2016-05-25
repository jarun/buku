# -*- coding: utf-8 -*-
import imp
from unittest import TestCase

foobar = imp.load_source('buku', '../buku')

from buku import BukuDb

class TestBukuDb(TestCase):
    def test_get_dbfile_path(self):
        self.fail()

    def test_move_legacy_dbfile(self):
        self.fail()

    def test_initdb(self):
        self.fail()

    def test_get_bookmark_index(self):
        self.fail()

    def test_add_bookmark(self):
        self.fail()

    def test_update_bookmark(self):
        self.fail()

    def test_refreshdb(self):
        self.fail()

    def test_searchdb(self):
        self.fail()

    def test_search_by_tag(self):
        self.fail()

    def test_compactdb(self):
        self.fail()

    def test_delete_bookmark(self):
        self.fail()

    def test_print_bookmark(self):
        self.fail()

    def test_list_tags(self):
        self.fail()

    def test_replace_tag(self):
        self.fail()

    def test_browse_by_index(self):
        self.fail()

    def test_close_quit(self):
        self.fail()

    def test_import_bookmark(self):
        self.fail()