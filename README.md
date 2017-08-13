<h1 align="center">Buku</h1>

<p align="center">
<a href="https://github.com/jarun/Buku/releases/latest"><img src="https://img.shields.io/github/release/jarun/buku.svg?maxAge=600" alt="Latest release" /></a>
<a href="https://aur.archlinux.org/packages/buku"><img src="https://img.shields.io/aur/version/buku.svg?maxAge=600" alt="AUR" /></a>
<a href="http://braumeister.org/formula/buku"><img src="https://img.shields.io/homebrew/v/buku.svg?maxAge=600" alt="Homebrew" /></a>
<a href="https://pypi.python.org/pypi/buku"><img src="https://img.shields.io/pypi/v/buku.svg?maxAge=600" alt="PyPI" /></a>
<a href="https://packages.debian.org/search?keywords=buku&searchon=names&exact=1"><img src="https://img.shields.io/badge/debian-9+-blue.svg?maxAge=2592000" alt="Debian Strech+" /></a>
<a href="http://packages.ubuntu.com/search?keywords=buku&searchon=names&exact=1"><img src="https://img.shields.io/badge/ubuntu-17.04+-blue.svg?maxAge=2592000" alt="Ubuntu Zesty+" /></a>
<a href="https://github.com/jarun/buku/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-GPLv3-yellow.svg?maxAge=2592000" alt="License" /></a>
<a href="https://travis-ci.org/jarun/Buku"><img src="https://travis-ci.org/jarun/Buku.svg?branch=master" alt="Build Status" /></a>
</p>

<p align="center">
<a href="https://asciinema.org/a/8pm3q3n5s95tvat8naam68ejv"><img src="https://asciinema.org/a/8pm3q3n5s95tvat8naam68ejv.png" alt="Asciicast" width="734"/></a>
</p>

### Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [Installing with a package manager](#installing-with-a-package-manager)
  - [Installing from this repository](#installing-from-this-repository)
    - [Running as a standalone utility](#running-as-a-standalone-utility)
    - [Release packages](#release-packages)
- [Shell completion](#shell-completion)
- [Usage](#usage)
  - [Cmdline options](#cmdline-options)
  - [Operational notes](#operational-notes)
- [GUI integration](#gui-integration)
  - [Add bookmarks from anywhere](#add-bookmarks-from-anywhere)
  - [Import bookmarks to browser](#import-bookmarks-to-browser)
- [Sync database across systems](#sync-database-across-systems)
- [As a library](#as-a-library)
- [Related projects](#related-projects)
- [Mentions](#mentions)
- [Examples](#examples)
- [Third-party integration](#third-party-integration)
- [Running tests](#running-tests)
- [Collaborators](#collaborators)

### Introduction

`buku` is a powerful bookmark manager written in Python3 and SQLite3. When I started writing it, I couldn't find a flexible cmdline solution with a private, portable, merge-able database along with browser integration. Hence, `Buku` (after my son's nickname, meaning *close to the heart* in my language).

`buku` fetches the title of a bookmarked web page and stores it along with any additional comments and tags. You can use your favourite editor to compose and update bookmarks. With multiple search options, including regex and a deep scan mode (particularly for URLs), it can find any bookmark instantly. Multiple search results can be opened in the browser at once.

Though a terminal utility, it's possible to add bookmarks to `buku` without touching the terminal! Refer to the section on [GUI integration](#gui-integration). If you prefer the terminal, thanks to the [shell completion](#shell-completion) scripts, you don't need to memorize any of the options. There's an Easter egg to revisit random forgotten bookmarks too.

*Buku* is too busy to track you - no history, obsolete records, usage analytics or homing.

There are several [projects](#related-projects) based on `buku`, including a browser plug-in.

PRs are welcome. Please visit [#174](https://github.com/jarun/Buku/issues/174) for a list of TODOs.

<p align="center">
<a href="https://saythanks.io/to/jarun"><img src="https://img.shields.io/badge/say-thanks!-ff69b4.svg" /></a>
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=RMLTQ76JSXJ4Q"><img src="https://img.shields.io/badge/PayPal-donate-FC746D.svg" alt="Donate via PayPal!" /></a>
</p>

### Features

- Lightweight, clean interface
- Flexible text editor integration
- Fetch, edit page title; add tags and notes
- Powerful search modes including regex, substring
- Continuous search at prompt, on the fly mode switch
- Open bookmarks and search results in browser
- Manual encryption support
- Auto-import Firefox and Google Chrome bookmarks
- Import/export bookmarks from/to HTML or Markdown
- Shorten and expand URLs
- Smart tag management using redirection (>>, >, <<)
- Portable, merge-able database to sync between systems
- Multithreaded full DB refresh
- Shell completion scripts, man page with handy examples

### Installation

#### Dependencies

| Feature | Dependency |
| --- | --- |
| Scripting language | Python 3.3+ |
| HTTP(S) | urllib3 |
| Encryption | cryptography |
| Import browser exported html | beautifulsoup4 |
| Shorten URL, check latest release | requests |

To install package dependencies using pip3, run:

    $ sudo pip3 install urllib3 cryptography beautifulsoup4 requests
or on Ubuntu:

    $ sudo apt-get install python3-urllib3 python3-cryptography python3-bs4 python3-requests

#### Installing with a package manager

- [AUR](https://aur.archlinux.org/packages/buku/)
- [Debian](https://packages.debian.org/search?keywords=buku&searchon=names&exact=1)
- [Homebrew](http://braumeister.org/formula/buku)
- [NixOS](https://github.com/NixOS/nixpkgs/tree/master/pkgs/applications/misc/buku) (`sudo nix-env -i buku`)
- [PyPi](https://pypi.python.org/pypi/buku/) (`sudo pip3 install buku`)
- [Ubuntu](http://packages.ubuntu.com/search?keywords=buku&searchon=names&exact=1)
- [Ubuntu PPA](https://launchpad.net/~twodopeshaggy/+archive/ubuntu/jarun/)
- [Void Linux](https://github.com/voidlinux/void-packages/tree/master/srcpkgs/buku) (`sudo xbps-install -S buku`)

#### Installing from this repository

If you have git installed, clone this repository. Otherwise download the [latest stable release](https://github.com/jarun/Buku/releases/latest) or [development version](https://github.com/jarun/Buku/archive/master.zip) (*risky*).

Install to default location (`/usr/local`):

    $ sudo make install

To remove, run:

    $ sudo make uninstall
`PREFIX` is supported. You may need to use `sudo` with `PREFIX` depending on your permissions on destination directory.

##### Running as a standalone utility

`buku` is a standalone utility. From the containing directory, run:

    $ chmod +x buku.py
    $ ./buku.py

##### Release packages

Packages for Arch Linux, CentOS, Fedora and Ubuntu are available with the [latest stable release](https://github.com/jarun/Buku/releases/latest).

### Shell completion

Shell completion scripts for Bash, Fish and Zsh can be found in respective subdirectories of [auto-completion/](https://github.com/jarun/Buku/blob/master/auto-completion). Please refer to your shell's manual for installation instructions.

### Usage

#### Cmdline options

```
usage: buku [OPTIONS] [KEYWORD [KEYWORD ...]]

Powerful command-line bookmark manager. Your mini web!

POSITIONAL ARGUMENTS:
      KEYWORD              search keywords

GENERAL OPTIONS:
      -a, --add URL [tag, ...]
                           bookmark URL with comma-separated tags
      -u, --update [...]   update fields of an existing bookmark
                           accepts indices and ranges
                           refresh the title, if no edit options
                           if no arguments:
                           - update results when used with search
                           - otherwise refresh all titles
      -w, --write [editor|index]
                           open editor to edit a fresh bookmark
                           to update by index, EDITOR must be set
      -d, --delete [...]   remove bookmarks from DB
                           accepts indices or a single range
                           if no arguments:
                           - delete results when used with search
                           - otherwise delete all bookmarks
      -h, --help           show this information and exit
      -v, --version        show the program version and exit

EDIT OPTIONS:
      --url keyword        bookmark link
      --tag [+|-] [...]    comma-separated tags
                           clear bookmark tagset, if no arguments
                           '+' appends to, '-' removes from tagset
      --title [...]        bookmark title; if no arguments:
                           -a: do not set title, -u: clear title
      -c, --comment [...]  notes or description of the bookmark
                           clears description, if no arguments
      --immutable N        disable title fetch from web on update
                           N=0: mutable (default), N=1: immutable

SEARCH OPTIONS:
      -s, --sany           find records with ANY matching keyword
                           this is the default search option
      -S, --sall           find records matching ALL the keywords
                           special keywords -
                           "blank": entries with empty title/tag
                           "immutable": entries with locked title
      --deep               match substrings ('pen' matches 'opens')
      -r, --sreg           run a regex search
      -t, --stag           search bookmarks by a tag
                           list all tags, if no search keywords

ENCRYPTION OPTIONS:
      -l, --lock [N]       encrypt DB file with N (> 0, default 8)
                           hash iterations to generate key
      -k, --unlock [N]     decrypt DB file with N (> 0, default 8)
                           hash iterations to generate key

POWER TOYS:
      --ai                 auto-import from Firefox and Chrome
      -e, --export file    export bookmarks in Firefox format html
                           export markdown, if file ends with '.md'
                           format: [title](url), 1 entry per line
                           use --tag to export only specific tags
      -i, --import file    import Firefox or Chrome bookmarks html
                           import markdown, if file ends with '.md'
      -m, --merge file     add bookmarks from another buku DB file
      -p, --print [...]    show record details by indices, ranges
                           print all bookmarks, if no arguments
                           -n shows the last n results (like tail)
      -f, --format N       limit fields in -p or Json search output
                           N=1: URL, N=2: URL and tag, N=3: title,
                           N=4: URL, title and tag
      -j, --json           Json formatted output for -p and search
      --nc                 disable color output
      --np                 do not show the prompt, run and exit
      -o, --open [...]     browse bookmarks by indices and ranges
                           open a random bookmark, if no arguments
      --oa                 browse all search results immediately
      --replace old new    replace old tag with new tag everywhere
                           delete old tag, if new tag not specified
      --shorten index|URL  fetch shortened url from tny.im service
      --expand index|URL   expand a tny.im shortened url
      --suggest            show similar tags when adding bookmarks
      --tacit              reduce verbosity
      --threads N          max network connections in full refresh
                           default N=4, min N=1, max N=10
      -V                   check latest upstream version available
      -z, --debug          show debug information and verbose logs

SYMBOLS:
      >                    url
      +                    comment
      #                    tags

PROMPT KEYS:
    1-N                    browse search result indices and/or ranges
    a                      open all results in browser
    s keyword [...]        search for records with ANY keyword
    S keyword [...]        search for records with ALL keywords
    d                      match substrings ('pen' matches 'opened')
    r expression           run a regex search
    t [...]                search bookmarks by a tag or show taglist
                           list index after a tag listing shows records with the tag
    o id|range [...]       browse bookmarks by indices and/or ranges
    p id|range [...]       print bookmarks by indices and/or ranges
    g [taglist id|range ...] [>>|>|<<] record id|range [...]
                           append, set, remove (all or specific) tags
    w [editor|id]          edit and add or update a bookmark
    ?                      show this help
    q, ^D, double Enter    exit buku
```

#### Operational notes

- The database file is stored in:
  - **$XDG_DATA_HOME/buku/bookmarks.db**, if XDG_DATA_HOME is defined (first preference) or
  - **$HOME/.local/share/buku/bookmarks.db**, if HOME is defined (second preference) or
  - **%APPDATA%\buku\bookmarks.db**, if you are on Windows or
  - **the current directory**.
- If the URL contains characters like `;`, `&` or brackets they may be interpreted specially by the shell. To avoid it, add the URL within single or double quotes (`'`/`"`).
- URLs are unique in DB. The same URL cannot be added twice.
- Bookmarks with immutable titles are listed with `(L)` after the title.
- **Tags**:
  - Comma (`,`) is the tag delimiter in DB. A tag cannot have comma(s) in it. Tags are filtered (for unique tags) and sorted. Tags are stored in lower case and can be replaced, appended or deleted.
  - Folder names are converted to all-lowercase tags during bookmarks html import.
  - Releases prior to [v2.7](https://github.com/jarun/Buku/releases/tag/v2.7) support both capital and lower cases in tags. From v2.7 all tags are stored in lowercase. An undocumented option `--fixtags` is introduced to modify the older tags. It also fixes another issue where the same tag appears multiple times in the tagset of a record. Run `buku --fixtags` once.
  - Tags can be edited from the prompt very easily using `>>` (append), `>` (overwrite) and `<<` (remove) symbols. The LHS of the operands denotes the indices and ranges of tags to apply (as listed by --tag or key `t` at prompt) and the RHS denotes the actual DB indices and ranges of the bookmarks to apply the change to.
- **Update** operation:
  - If --title, --tag or --comment is passed without argument, clear the corresponding field from DB.
  - If --url is passed (and --title is omitted), update the title from web using the URL.
  - If indices are passed without any other options (--url, --title, --tag, --comment and --immutable), read the URLs from DB and update titles from web. Bookmarks marked immutable are skipped.
  - Can update bookmarks matching a search, when combined with any of the search options and no arguments to update are passed.
- **Delete** operation:
  - When a record is deleted, the last record is moved to the index.
  - Delete doesn't work with range and indices provided together as arguments. It's an intentional decision to avoid extra sorting, in-range checks and to keep the auto-DB compaction functionality intact. On the same lines, indices are deleted in descending order.
  - Can delete bookmarks matching a search, when combined with any of the search options and no arguments to delete are passed.
- **Search** works in mysterious ways:
  - Case-insensitive.
  - Matches words in URL, title and tags.
  - --sany : match any of the keywords in URL, title or tags. Default search option.
  - --sall : match all the keywords in URL, title or tags.
  - --deep : match **substrings** (`match` matches `rematched`) in URL, title and tags.
  - --sreg : match a regular expression (ignores --deep).
  - --stag : search bookmarks by a tag, or list all tags alphabetically with usage count (if no arguments).
  - Search results are indexed serially. This index is different from actual database index of a bookmark record which is shown within `[]` after the title.
- **Import**:
  - URLs starting with `place:`, `file://` and `apt:` are ignored during import.
  - Folder names are automatically imported as tags if --tacit is used.
  - Auto-import looks in the default installation path and default user profile.
- **Encryption** is optional and manual. AES256 algorithm is used. To use encryption, the database file should be unlocked (-k) before using `buku` and locked (-l) afterwards. Between these 2 operations, the database file lies unencrypted on the disk, and NOT in memory. Also, note that the database file is *unencrypted on creation*.
- **Editor** support:
  - A single bookmark can be edited before adding. The editor can be set using the environment variable *EDITOR* or by explicitly specifying the editor. The latter takes preference. If -a is used along with -w, the details are populated in the editor template.
  - In case of edit and update (a single bookmark), the existing record details are fetched from DB and populated in the editor template. The environment variable EDITOR must be set Note that -u works independently of -w.
  - All lines beginning with "#" will be stripped. Then line 1 will be treated as the URL, line 2 will be the title, line 3 will be comma separated tags, and the rest of the lines will be parsed as descriptions.
- **Proxy** support: environment variable *https_proxy*, if defined, is used to tunnel data for both http and https connections. The supported format is:

      http[s]://[username:password@]proxyhost:proxyport/

### GUI integration

![buku](http://i.imgur.com/8Y6PTPw.png)

`buku` can be integrated in a GUI environment with simple tweaks.

#### Add bookmarks from anywhere

With support for piped input, it's possible to add bookmarks to `buku` using keyboard shortcuts on Linux and OS X. CLIPBOARD (plus PRIMARY on Linux) text selections can be added directly this way. The additional utility required is `xsel` (on Linux) or `pbpaste` (on OS X).

The following steps explore the procedure on Linux with Ubuntu as the reference platform.

1. To install `xsel` on Ubuntu, run:

        $ sudo apt install xsel
2. Create a new script `bukuadd` with the following content:

        #!/bin/bash

        xsel | buku -a

      `-a` is the option to add a bookmark.
3. Make the script executable:

        $ chmod +x bukuadd
4. Copy it somewhere in your `PATH`.
5. Add a new keyboard shortcut to run the script. I use `<Alt-b>`.

##### Test drive

Copy or select a URL with mouse and press the keyboard shortcut to add it to the `buku` database. The addition might take a few seconds to reflect depending on your internet speed and the time `buku` needs to fetch the title from the URL. To avoid title fetch from the web, add the `--title` option to the script.

To verify that the bookmark has indeed been added, run:

    $ buku -p -1
and check the entry.

##### Tips

- To add the last visited URL in Firefox to `buku`, use the following script:

        #!/bin/bash

        sqlite3 $HOME/.mozilla/firefox/*.default/places.sqlite "select url from moz_places where last_visit_date=(select max(last_visit_date) from moz_places)" | buku -a
- If you want to tag these bookmarks, look them up later using:

        $ buku -S blank
  Use option `-u` to tag these bookmarks.

#### Import bookmarks to browser

`buku` can export (or import) bookmarks in HTML format recognized by Firefox, Google Chrome and Internet Explorer.

To export all bookmarks, run:

    $ buku --export path_to_bookmarks.html
To export specific tags, run:

    $ buku --export path_to_bookmarks.html --tag tag 1, tag 2
Once exported, import the html file in your browser.

### Sync database across systems

`buku` has the capability to import records from another `buku` database file. However, users with a cloud service client installed on multiple systems can keep the database synced across these systems automatically. To achieve this store the actual database file in a synced directory and create a symbolic link to it in the location where the database file would exist otherwise. For example, `$HOME/.local/share/buku/bookmarks.db` can be a symbolic link to `~/synced_dir/bookmarks.db`.

### As a library

`buku` is developed as a powerful python library for bookmark management. All functionality are available through carefully designed APIs. `main()` is a good usage example. It's also possible to use a custom database file in multi-user scenarios. Check out the documentation for the following APIs which accept an optional argument as database file:

    BukuDb.initdb(dbfile=None)
    BukuCrypt.encrypt_file(iterations, dbfile=None)
    BukuCrypt.decrypt_file(iterations, dbfile=None)
NOTE: This flexibility is not exposed in the program.

The [api](https://github.com/jarun/Buku/tree/master/api) directory has several example wrapper web APIs, not necessarily updated. Feel free to update if you need them.

An example to print the http status code of urls saved in `buku` goes below. To run, install [grequests](https://github.com/kennethreitz/grequests).

```python
import buku
import grequests

bdb = buku.BukuDb()
recs = bdb.get_rec_all()
recs[0]
# output: (1, 'example.com', 'example', 'tag1,tag2', 'page description', 0)
# Records have following structure:
# - id,
# - url,
# - metadata,
# - tags,
# - description,
# - flags
urls = [x[1] for x in recs]
rs = (grequests.get(u) for u in urls)
gr_results = grequests.map(rs)
for resp, url in zip(gr_results, urls):
  stat_code = None if resp.status_code is None else resp.status_code
  print('{}: {}'.format(stat_code, url))
# output
# 200: http://example.com
# None: http://website1.com/
# 200: http://website2.com/
# ...
```

### Related projects

- [bukubrow](https://github.com/SamHH/bukubrow), WebExtension for browser integration
- [oil](https://github.com/AndreiUlmeyda/oil), search-as-you-type cli frontend
- [buku_run](https://github.com/carnager/buku_run), rofi frontend

### Mentions

- [One Thing Well](http://onethingwell.org/post/144952807044/buku)
- [It's F.O.S.S.](https://itsfoss.com/buku-command-line-bookmark-manager-linux/)
- [Make Tech Easier](https://www.maketecheasier.com/manage-browser-bookmarks-ubuntu-command-line/)
- [LinuxUser Magazine 01/2017 Issue](http://www.linux-community.de/LU/2017/01/Das-Beste-aus-zwei-Welten)
- [2daygeek](http://www.2daygeek.com/buku-command-line-bookmark-manager-linux/)

### Examples

1. **Edit and add** a bookmark from editor:

        $ buku -w
        $ buku -w 'macvim -f' -a https://ddg.gg search engine, privacy
    The first command picks editor from the environment variable `EDITOR`. The second command will open macvim with option -f and the URL and tags populated in template.
2. **Add** a bookmark with **tags** `search engine` and `privacy`, **comment** `Search engine with perks`, **fetch page title** from the web:

        $ buku -a https://ddg.gg search engine, privacy -c Search engine with perks
        336. DuckDuckGo
        > https://ddg.gg
        + Alternative search engine with perks
        # privacy,search engine
    where, >: url, +: comment, #: tags
3. **Add** a bookmark with tags `search engine` & `privacy` and **immutable custom title** `DDG`:

        $ buku -a https://ddg.gg search engine, privacy --title 'DDG' --immutable 1
        336. DDG (L)
        > https://ddg.gg
        # privacy,search engine
    Note that URL must precede tags.
4. **Add** a bookmark **without a title** (works for update too):

        $ buku -a https://ddg.gg search engine, privacy --title
5. **Edit and update** a bookmark from editor:

        $ buku -w 15012014
    This will open the existing bookmark's details in the editor for modifications. Environment variable `EDITOR` must be set.
6. **Update** existing bookmark at index 15012014 with new URL, tags and comments, fetch title from the web:

        $ buku -u 15012014 --url http://ddg.gg/ --tag web search, utilities -c Private search engine
7. **Fetch and update only title** for bookmark at 15012014:

        $ buku -u 15012014
8. **Update only comment** for bookmark at 15012014:

        $ buku -u 15012014 -c this is a new comment
    Applies to --url, --title and --tag too.
9. **Export** bookmarks tagged `tag 1` or `tag 2` to HTML and markdown:

        $ buku -e bookmarks.html --tag tag 1, tag 2
        $ buku -e bookmarks.md --tag tag 1, tag 2
    All bookmarks are exported if --tag is not specified.
10. **Import** bookmarks from HTML and markdown:

        $ buku -i bookmarks.html
        $ buku -i bookmarks.md
11. **Delete only comment** for bookmark at 15012014:

        $ buku -u 15012014 -c
    Applies to --title and --tag too. URL cannot be deleted without deleting the bookmark.
12. **Update** or refresh **full DB** with page titles from the web:

        $ buku -u
        $ buku -u --tacit (show only failures and exceptions)
    This operation does not modify the indexes, URLs, tags or comments. Only title is refreshed if fetched title is non-empty.
13. **Delete** bookmark at index 15012014:

        $ buku -d 15012014
        Index 15012020 moved to 15012014
    The last index is moved to the deleted index to keep the DB compact.
14. **Delete all** bookmarks:

        $ buku -d
15. **Delete** a **range or list** of bookmarks:

        $ buku -d 100-200
        $ buku -d 100 15 200
16. **Search** bookmarks for **ANY** of the keywords `kernel` and `debugging` in URL, title or tags:

        $ buku kernel debugging
        $ buku -s kernel debugging
17. **Search** bookmarks with **ALL** the keywords `kernel` and `debugging` in URL, title or tags:

        $ buku -S kernel debugging
18. **Search** bookmarks **tagged** `general kernel concepts`:

        $ buku --stag general kernel concepts
19. List **all unique tags** alphabetically:

        $ buku --stag
20. Run a **search and update** the results:

        $ buku -s kernel debugging -u --tag + linux kernel
21. Run a **search and delete** the results:

        $ buku -s kernel debugging -d
22. **Encrypt or decrypt** DB with **custom number of iterations** (15) to generate key:

        $ buku -l 15
        $ buku -k 15
    The same number of iterations must be specified for one lock & unlock instance. Default is 8, if omitted.
23. **Show details** of bookmarks at index 15012014 and ranges 20-30, 40-50:

        $ buku -p 20-30 15012014 40-50
24. Show details of the **last 10 bookmarks**:

        $ buku -p -10
25. **Show all** bookmarks with real index from database:

        $ buku -p
        $ buku -p | more
26. **Replace tag** 'old tag' with 'new tag':

        $ buku --replace 'old tag' 'new tag'
27. **Delete tag** 'old tag' from DB:

        $ buku --replace 'old tag'
28. **Append (or delete) tags** 'tag 1', 'tag 2' to (or from) existing tags of bookmark at index 15012014:

        $ buku -u 15012014 --tag + tag 1, tag 2
        $ buku -u 15012014 --tag - tag 1, tag 2
29. **Open URL** at index 15012014 in browser:

        $ buku -o 15012014
30. List bookmarks with **no title or tags** for bookkeeping:

        $ buku -S blank
31. List bookmarks with **immutable title**:

        $ buku -S immutable
32. **Shorten URL** www.google.com and the URL at index 20:

        $ buku --shorten www.google.com
        $ buku --shorten 20
33. **Append, remove tags at prompt** (taglist index to the left, bookmark index to the right):

        // append tags at taglist indices 4 and 6-9 to existing tags in bookmarks at indices 5 and 2-3
        buku (? for help) g 4 9-6 >> 5 3-2
        // set tags at taglist indices 4 and 6-9 as tags in bookmarks at indices 5 and 2-3
        buku (? for help) g 4 9-6 > 5 3-2
        // remove all tags from bookmarks at indices 5 and 2-3
        buku (? for help) g > 5 3-2
        // remove tags at taglist indices 4 and 6-9 from tags in bookmarks at indices 5 and 2-3
        buku (? for help) g 4 9-6 << 5 3-2
34. More **help**:

        $ buku -h
        $ man buku

### Third-party integration

1. `buku` waits until its input is closed when not started in a tty. For example, the following hangs:

        $ cat | buku
   This is the intended behaviour as the primary reason behind supporting piped input is to add bookmarks with a keyboard shortcut. Third-party applications should explicitly close the input stream or use a wrapper script like the following one:

        #!/bin/bash

        echo $1 | buku -a

### Running tests

We use [tox](http://readthedocs.org/docs/tox/) to manage virtualenvs and run tests.
Alternatively, tests can be run using [detox](https://pypi.python.org/pypi/detox/) which allows for running tests in parallel

        $ pip install tox detox

Run all of the tests with:
        $ tox

Run all of the tests in parallel with detox:

        $ detox

If you running into this error check you buku setting.

```
>       self.assertEqual(dbdir_local_expected, BukuDb.get_default_dbdir())
E       AssertionError: '/home/user/.local/share/buku' != '/home/user/projects/buku'
E       - /home/user/.local/share/buku
E       + /home/user/projects/buku
```

### Collaborators

- [Arun Prakash Jana](https://github.com/jarun)
- [Rachmadani Haryono](https://github.com/rachmadaniHaryono)
- [Johnathan Jenkins](https://github.com/shaggytwodope)
- [SZ Lin](https://github.com/szlin)
- [Alex Bender](https://github.com/alex-bender)

Copyright © 2015-2017 [Arun Prakash Jana](mailto:engineerarun@gmail.com)
<br>
<p><a href="https://gitter.im/jarun/Buku"><img src="https://img.shields.io/gitter/room/jarun/buku.svg?maxAge=2592000" alt="gitter chat" /></a></p>
