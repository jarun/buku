#! /usr/bin/env python3

import os
import sys


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
