#!/usr/bin/env python
import os
import sys

try:
    from . import translations_compile, __version__
except ImportError:
    from bukuserver.translations import translations_compile, __version__

if __name__ == '__main__':
    if any(s in sys.argv[1:] for s in ['-h', '--help']):
        print(f'  Usage: python {sys.argv[0]} [new-locale [...]]')
        print('    This script updates Bukuserver translation files (and/or adds new locales)')
        print('    FUZZY=yes (or any other non-empty value) enables fuzzy matching')
        print(f'  [buku version: {__version__ or "???"}]')
    else:
        new_locales = [s for s in sys.argv[1:] if s[:1] not in ('', '-')]
        translations_compile(update=True, new_locales=new_locales, fuzzy=bool(os.environ.get('FUZZY')))
