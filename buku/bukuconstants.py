#! /usr/bin/env python3

__version__ = '4.1'
__author__ = 'Arun Prakash Jana <engineerarun@gmail.com>'
__license__ = 'GPLv3'

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

DELIM = ','  # Delimiter used to store tags in DB

SKIP_MIMES = {'.pdf', '.txt'}

USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'
TEXT_BROWSERS = ['elinks', 'links', 'links2', 'lynx', 'w3m', 'www-browser']
