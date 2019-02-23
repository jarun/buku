#! /usr/bin/env python3

import argparse
import sys

from .bukuutil import get_system_editor
from .bukuconstants import __version__, __author__, __license__, COLORMAP


class ExtendedArgumentParser(argparse.ArgumentParser):
    """Extend classic argument parser."""

    @staticmethod
    def program_info(file=sys.stdout):
        """Print program info.

        Parameters
        ----------
        file : file, optional
            File to write program info to. Default is sys.stdout.
        """
        if sys.platform == 'win32' and file == sys.stdout:
            file = sys.stderr

        file.write('''
SYMBOLS:
      >                    url
      +                    comment
      #                    tags

Version %s
Copyright © 2015-2019 %s
License: %s
Webpage: https://github.com/jarun/Buku
''' % (__version__, __author__, __license__))

    @staticmethod
    def prompt_help(file=sys.stdout):
        """Print prompt help.

        Parameters
        ----------
        file : file, optional
            File to write program info to. Default is sys.stdout.
        """
        file.write('''
PROMPT KEYS:
    1-N                    browse search result indices and/or ranges
    O [id|range [...]]     open search results/indices in GUI browser
                           toggle try GUI browser if no arguments
    a                      open all results in browser
    s keyword [...]        search for records with ANY keyword
    S keyword [...]        search for records with ALL keywords
    d                      match substrings ('pen' matches 'opened')
    r expression           run a regex search
    t [tag, ...]           search by tags; show taglist, if no args
    g taglist id|range [...] [>>|>|<<] [record id|range ...]
                           append, set, remove (all or specific) tags
                           search by taglist id(s) if records are omitted
    n                      show next page of search results
    o id|range [...]       browse bookmarks by indices and/or ranges
    p id|range [...]       print bookmarks by indices and/or ranges
    w [editor|id]          edit and add or update a bookmark
    c id                   copy url at search result index to clipboard
    ?                      show this help
    q, ^D, double Enter    exit buku

''')

    @staticmethod
    def is_colorstr(arg):
        """Check if a string is a valid color string.

        Parameters
        ----------
        arg : str
            Color string to validate.

        Returns
        -------
        str
            Same color string that was passed as an argument.

        Raises
        ------
        ArgumentTypeError
            If the arg is not a valid color string.
        """
        try:
            assert len(arg) == 5
            for c in arg:
                assert c in COLORMAP
        except AssertionError:
            raise argparse.ArgumentTypeError('%s is not a valid color string' % arg)
        return arg

    # Help
    def print_help(self, file=sys.stdout):
        """Print help prompt.

        Parameters
        ----------
        file : file, optional
            File to write program info to. Default is sys.stdout.
        """
        super(ExtendedArgumentParser, self).print_help(file)
        self.program_info(file)


def create_argparser():
    # Setup custom argument parser
    argparser = ExtendedArgumentParser(
        description='''Bookmark manager like a text-based mini-web.

POSITIONAL ARGUMENTS:
      KEYWORD              search keywords''',
        formatter_class=argparse.RawTextHelpFormatter,
        usage='''buku [OPTIONS] [KEYWORD [KEYWORD ...]]''',
        add_help=False
    )
    hide = argparse.SUPPRESS
    argparser.add_argument('keywords', nargs='*', metavar='KEYWORD', help=hide)
    # ---------------------
    # GENERAL OPTIONS GROUP
    # ---------------------
    general_grp = argparser.add_argument_group(
        title='GENERAL OPTIONS',
        description='''    -a, --add URL [tag, ...]
                         bookmark URL with comma-separated tags
    -u, --update [...]   update fields of an existing bookmark
                         accepts indices and ranges
                         refresh title and desc if no edit options
                         if no arguments:
                         - update results when used with search
                         - otherwise refresh all titles and desc
    -w, --write [editor|index]
                         open editor to edit a fresh bookmark
                         edit last bookmark, if index=-1
                         to specify index, EDITOR must be set
    -d, --delete [...]   remove bookmarks from DB
                         accepts indices or a single range
                         if no arguments:
                         - delete results when used with search
                         - otherwise delete all bookmarks
    -h, --help           show this information and exit
    -v, --version        show the program version and exit''')
    addarg = general_grp.add_argument
    addarg('-a', '--add', nargs='+', help=hide)
    addarg('-u', '--update', nargs='*', help=hide)
    addarg('-w', '--write', nargs='?', const=get_system_editor(), help=hide)
    addarg('-d', '--delete', nargs='*', help=hide)
    addarg('-h', '--help', action='store_true', help=hide)
    addarg('-v', '--version', action='version', version=__version__, help=hide)
    # ------------------
    # EDIT OPTIONS GROUP
    # ------------------
    edit_grp = argparser.add_argument_group(
        title='EDIT OPTIONS',
        description='''    --url keyword        bookmark link
    --tag [+|-] [...]    comma-separated tags
                         clear bookmark tagset, if no arguments
                         '+' appends to, '-' removes from tagset
    --title [...]        bookmark title; if no arguments:
                         -a: do not set title, -u: clear title
    -c, --comment [...]  notes or description of the bookmark
                         clears description, if no arguments
    --immutable N        disable web-fetch during auto-refresh
                         N=0: mutable (default), N=1: immutable''')
    addarg = edit_grp.add_argument
    addarg('--url', nargs=1, help=hide)
    addarg('--tag', nargs='*', help=hide)
    addarg('--title', nargs='*', help=hide)
    addarg('-c', '--comment', nargs='*', help=hide)
    addarg('--immutable', type=int, default=-1, choices={0, 1}, help=hide)
    # --------------------
    # SEARCH OPTIONS GROUP
    # --------------------
    search_grp = argparser.add_argument_group(
        title='SEARCH OPTIONS',
        description='''    -s, --sany [...]     find records with ANY matching keyword
                         this is the default search option
    -S, --sall [...]     find records matching ALL the keywords
                         special keywords -
                         "blank": entries with empty title/tag
                         "immutable": entries with locked title
    --deep               match substrings ('pen' matches 'opens')
    -r, --sreg expr      run a regex search
    -t, --stag [tag [,|+] ...] [- tag, ...]
                         search bookmarks by tags
                         use ',' to find entries matching ANY tag
                         use '+' to find entries matching ALL tags
                         excludes entries with tags after ' - '
                         list all tags, if no search keywords
    -x, --exclude [...]  omit records matching specified keywords''')
    addarg = search_grp.add_argument
    addarg('-s', '--sany', nargs='*', help=hide)
    addarg('-S', '--sall', nargs='*', help=hide)
    addarg('-r', '--sreg', nargs='*', help=hide)
    addarg('--deep', action='store_true', help=hide)
    addarg('-t', '--stag', nargs='*', help=hide)
    addarg('-x', '--exclude', nargs='*', help=hide)
    # ------------------------
    # ENCRYPTION OPTIONS GROUP
    # ------------------------
    crypto_grp = argparser.add_argument_group(
        title='ENCRYPTION OPTIONS',
        description='''    -l, --lock [N]       encrypt DB in N (default 8) # iterations
    -k, --unlock [N]     decrypt DB in N (default 8) # iterations''')
    addarg = crypto_grp.add_argument
    addarg('-k', '--unlock', nargs='?', type=int, const=8, help=hide)
    addarg('-l', '--lock', nargs='?', type=int, const=8, help=hide)
    # ----------------
    # POWER TOYS GROUP
    # ----------------
    power_grp = argparser.add_argument_group(
        title='POWER TOYS',
        description='''    --ai                 auto-import from Firefox/Chrome/Chromium
    -e, --export file    export bookmarks to Firefox format HTML
                         export Markdown, if file ends with '.md'
                         format: [title](url), 1 entry per line
                         export Orgfile, if file ends with '.org'
                         format: *[[url][title]], 1 entry per line
                         export buku DB, if file ends with '.db'
                         combines with search results, if opted
    -i, --import file    import bookmarks based on file extension
                         supports 'html', 'json', 'md', 'org', 'db'
    -p, --print [...]    show record details by indices, ranges
                         print all bookmarks, if no arguments
                         -n shows the last n results (like tail)
    -f, --format N       limit fields in -p or JSON search output
                         N=1: URL, N=2: URL and tag, N=3: title,
                         N=4: URL, title and tag. To omit DB index,
                         use N0, e.g., 10, 20, 30, 40.
    -j, --json           JSON formatted output for -p and search
    --colors COLORS      set output colors in five-letter string
    --nc                 disable color output
    -n, --count N        show N results per page (default 10)
    --np                 do not show the prompt, run and exit
    -o, --open [...]     browse bookmarks by indices and ranges
                         open a random bookmark, if no arguments
    --oa                 browse all search results immediately
    --replace old new    replace old tag with new tag everywhere
                         delete old tag, if new tag not specified
    --shorten index|URL  fetch shortened url from tny.im service
    --expand index|URL   expand a tny.im shortened url
    --cached index|URL   browse a cached page from Wayback Machine
    --suggest            show similar tags when adding bookmarks
    --tacit              reduce verbosity
    --threads N          max network connections in full refresh
                         default N=4, min N=1, max N=10
    -V                   check latest upstream version available
    -z, --debug          show debug information and verbose logs''')
    addarg = power_grp.add_argument
    addarg('--ai', action='store_true', help=hide)
    addarg('-e', '--export', nargs=1, help=hide)
    addarg('-i', '--import', nargs=1, dest='importfile', help=hide)
    addarg('-p', '--print', nargs='*', help=hide)
    addarg('-f', '--format', type=int, default=0, choices={1, 2, 3, 4, 10, 20, 30, 40}, help=hide)
    addarg('-j', '--json', action='store_true', help=hide)
    addarg('--colors', dest='colorstr', type=argparser.is_colorstr, metavar='COLORS', help=hide)
    addarg('--nc', action='store_true', help=hide)
    addarg('-n', '--count', nargs='?', const=10, type=int, default=0, help=hide)
    addarg('--np', action='store_true', help=hide)
    addarg('-o', '--open', nargs='*', help=hide)
    addarg('--oa', action='store_true', help=hide)
    addarg('--replace', nargs='+', help=hide)
    addarg('--shorten', nargs=1, help=hide)
    addarg('--expand', nargs=1, help=hide)
    addarg('--cached', nargs=1, help=hide)
    addarg('--suggest', action='store_true', help=hide)
    addarg('--tacit', action='store_true', help=hide)
    addarg('--threads', type=int, default=4, choices=range(1, 11), help=hide)
    addarg('-V', dest='upstream', action='store_true', help=hide)
    addarg('-z', '--debug', action='store_true', help=hide)
    # Undocumented APIs
    addarg('--fixtags', action='store_true', help=hide)
    addarg('--db', nargs=1, help=hide)
    return argparser
