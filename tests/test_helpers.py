#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import imp, unittest

buku = imp.load_source('buku', '../buku')

from buku import *


class TestHelpers(unittest.TestCase):

    # @unittest.skip('skipping')
    def test_parse_tags(self):
        # call without arguments
        parsed = parse_tags()
        self.assertIsNone(parsed)
        # empty tags
        parsed = parse_tags([",,,,,"])
        self.assertEqual(parsed, ",")
        # sorting tags
        parsed = parse_tags(["z_tag,a_tag,n_tag"])
        self.assertEqual(parsed, ",a_tag,n_tag,z_tag,")
        # whitespaces
        parsed = parse_tags([" a tag , ,   ,  ,\t,\n,\r,\x0b,\x0c"])
        self.assertEqual(parsed, ",a tag,")
        # duplicates, excessive spaces
        parsed = parse_tags(["tag,tag, tag,  tag,tag , tag "])
        self.assertEqual(parsed, ",tag,")
        # escaping quotes
        parsed = parse_tags(["\"tag\",\'tag\',tag"])
        self.assertEqual(parsed, ",\"tag\",\'tag\',tag,")
        # combo
        parsed = parse_tags([",,z_tag, a tag ,\t,,,  ,n_tag ,n_tag, a_tag, \na tag  ,\r, \"a_tag\""])
        self.assertEqual(parsed, ",\"a_tag\",a tag,a_tag,n_tag,z_tag,")

    # @unittest.skip('skipping')
    def test_is_int(self):
        self.assertTrue(is_int('0'))
        self.assertTrue(is_int('1'))
        self.assertTrue(is_int('-1'))
        self.assertFalse(is_int(''))
        self.assertFalse(is_int('one'))

    # @unittest.skip('skipping')
    def test_sigint_handler(self):
        # class for mocking stderr object
        class StderrCapture:
            capture = ""
            def write(self, data):
                self.capture += data
        # assigning stderr to temp, mock object to stderr
        sys.stderr, temp = StderrCapture(), sys.stderr
        try:
            # sending SIGINT to self
            os.kill(os.getpid(), signal.SIGINT)
        except SystemExit as err:
            # assering exited with 1
            self.assertEqual(err.args[0], 1)
            # assering proper error message
            self.assertEqual(sys.stderr.capture, "\nInterrupted.\n")
        finally:
            # reassigning stderr
            sys.stderr = temp

if __name__ == "__main__":
    unittest.main()
