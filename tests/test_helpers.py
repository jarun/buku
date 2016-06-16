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


def test_sigint_handler(capsys):
    try:
        # sending SIGINT to self
        os.kill(os.getpid(), signal.SIGINT)
    except SystemExit as error:
        out, err = capsys.readouterr()
        # assering exited with 1
        assert error.args[0] == 1
        # assering proper error message
        assert out == ''
        assert err == "\nInterrupted.\n"

def test_printmsg(capsys):
    # call with two args
    printmsg("test", "ERROR")
    out, err = capsys.readouterr()
    assert out == "\x1b[1mERROR: \x1b[21mtest\x1b[0m\n"
    assert err == ''

    # call with one arg
    printmsg("message")
    out, err = capsys.readouterr()
    assert out == "message\n"
    assert err == ''


if __name__ == "__main__":
    unittest.main()
