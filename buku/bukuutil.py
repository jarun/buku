#! /usr/bin/env python3

import logging
import os
import sys

from .bukuconstants import DELIM

LOGGER = logging.getLogger()
LOGDBG = LOGGER.debug


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


def is_nongeneric_url(url):
    """Returns True for URLs which are non-http and non-generic.

    Parameters
    ----------
    url : str
        URL to scan.

    Returns
    -------
    bool
        True if URL is a non-generic URL, False otherwise.
    """

    ignored_prefix = [
        'about:',
        'apt:',
        'chrome://',
        'file://',
        'place:',
    ]

    for prefix in ignored_prefix:
        if url.startswith(prefix):
            return True

    return False


def delim_wrap(token):
    """Returns token string wrapped in delimiters.

    Parameters
    ----------
    token : str
        String item to wrap with DELIM.

    Returns
    -------
    str
        Token string wrapped by DELIM.
    """

    if token is None or token.strip() == '':
        return DELIM

    if token[0] != DELIM:
        token = DELIM + token

    if token[-1] != DELIM:
        token = token + DELIM

    return token


def parse_tags(keywords=[]):
    """Format and get tag string from tokens.

    Parameters
    ----------
    keywords : list, optional
        List of tags to parse. Default is empty list.

    Returns
    -------
    str
        Comma-delimited string of tags.
    DELIM : str
        If no keywords, returns the delimiter.
    None
        If keywords is None.
    """

    if keywords is None:
        return None

    if not keywords or len(keywords) < 1 or not keywords[0]:
        return DELIM

    tags = DELIM

    # Cleanse and get the tags
    tagstr = ' '.join(keywords)
    marker = tagstr.find(DELIM)

    while marker >= 0:
        token = tagstr[0:marker]
        tagstr = tagstr[marker + 1:]
        marker = tagstr.find(DELIM)
        token = token.strip()
        if token == '':
            continue

        tags += token + DELIM

    tagstr = tagstr.strip()
    if tagstr != '':
        tags += tagstr + DELIM

    LOGDBG('keywords: %s', keywords)
    LOGDBG('parsed tags: [%s]', tags)

    if tags == DELIM:
        return tags

    # original tags in lower case
    orig_tags = tags.lower().strip(DELIM).split(DELIM)

    # Create list of unique tags and sort
    unique_tags = sorted(set(orig_tags))

    # Wrap with delimiter
    return delim_wrap(DELIM.join(unique_tags))

# ---------------------
# Editor mode functions
# ---------------------


def get_system_editor():
    """Returns default system editor is $EDITOR is set."""

    return os.environ.get('EDITOR', 'none')
