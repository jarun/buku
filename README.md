<h1 align="center">Buku</h1>

<p align="center">
<a href="https://github.com/jarun/Buku/releases/latest"><img src="https://img.shields.io/github/release/jarun/buku.svg" alt="Latest release" /></a>
<a href="https://aur.archlinux.org/packages/buku"><img src="https://img.shields.io/aur/version/buku.svg" alt="AUR" /></a>
<a href="http://braumeister.org/formula/buku"><img src="https://img.shields.io/homebrew/v/buku.svg" alt="Homebrew" /></a>
<a href="https://github.com/jarun/buku/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-GPLv3-yellow.svg?maxAge=2592000" alt="License" /></a>
<a href="https://travis-ci.org/jarun/Buku"><img src="https://travis-ci.org/jarun/Buku.svg?branch=master" alt="Build Status" /></a>
</p>

<p align="center">
<a href="https://asciinema.org/a/93428"><img src="https://asciinema.org/a/93428.png" alt="Asciicast" width="734"/></a>
</p>

`buku` is a powerful bookmark management utility written in Python3 and SQLite3. When I started writing it, I couldn't find a flexible cmdline solution with a private, portable, merge-able database along with browser integration. Hence, `buku` (after my son's nickname).

With tagging and multiple options to search bookmarks, including regex and a deep scan mode (particularly for URLs), finding a bookmark is very easy. Multiple search results can be opened in the browser at once.

Though a terminal utility, it's possible to add bookmarks to `buku` without touching the terminal! Refer to the section on [GUI integration](#gui-integration). If you prefer the terminal, thanks to the shell completion scripts, you don't need to memorize any of the options. There's an Easter egg to revisit random forgotten bookmarks too.

<br>
<p align="center">
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=RMLTQ76JSXJ4Q"><img src="https://img.shields.io/badge/paypal-donate-orange.svg?maxAge=2592000" alt="Donate" /></a>
&nbsp;
<a href="https://gitter.im/jarun/Buku"><img src="https://img.shields.io/gitter/room/jarun/buku.svg?maxAge=2592000" alt="gitter chat" /></a>
</p>

## Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [Installing from this repository](#installing-from-this-repository)
    - [Running as a standalone utility](#running-as-a-standalone-utility)
    - [Debian package](#debian-package)
  - [Installing with a package manager](#installing-with-a-package-manager)
- [Shell completion](#shell-completion)
- [Usage](#usage)
  - [Cmdline options](#cmdline-options)
  - [Operational notes](#operational-notes)
- [GUI integration](#gui-integration)
  - [Add bookmarks from anywhere](#add-bookmarks-from-anywhere)
  - [Import bookmarks to browser](#import-bookmarks-to-browser)
- [As a library](#as-a-library)
- [Examples](#examples)
- [Contributions](#contributions)
- [Mentions](#mentions)
- [Copyright](#copyright)

## Features

- Add, open, tag, comment on, update, remove, shorten URLs
- Multiple search options, continuous search at prompt
- Portable, merge-able database, to sync between systems
- Import/export bookmarks in markdown or HTML (FF, Chrome compatible)
- Fetch page title from web, refresh all titles in a go
- Open (multiple) search results directly in default browser
- Manual password protection using AES256 encryption
- Tab-completion scripts (Bash, Fish, Zsh), man page with examples
- Several options for power users (see help or man page)
- Fast and clean interface, distinct symbols for record fields
- Minimal dependencies

## Installation

### Dependencies

`buku` requires Python 3.3 or later.

To install package dependencies, run:

    $ sudo pip3 install cryptography beautifulsoup4
or on Ubuntu:

    $ sudo apt-get install python3-cryptography python3-bs4

### Installing from this repository

If you have git installed, run:

    $ git clone https://github.com/jarun/Buku/
or download the latest [stable release](https://github.com/jarun/Buku/releases/latest) or [development version](https://github.com/jarun/Buku/archive/master.zip).

Install to default location (`/usr/local`):

    $ sudo make install

To remove, run:

    $ sudo make uninstall
`PREFIX` is supported. You may need to use `sudo` with `PREFIX` depending on your permissions on destination directory.

#### Running as a standalone utility

`buku` is a standalone utility. From the containing directory, run:

    $ chmod +x buku.py
    $ ./buku.py

#### Debian package

If you are on a Debian (including Ubuntu) based system visit [the latest stable release](https://github.com/jarun/Buku/releases/latest) and download the `.deb` package. To install, run:

    $ sudo dpkg -i buku-$version-all.deb

Please substitute `$version` with the appropriate package version.

### Installing with a package manager

`buku` is also available on
- [AUR](https://aur.archlinux.org/packages/buku/) for Arch Linux
- [Ubuntu](https://launchpad.net/ubuntu/+source/buku)
- [Homebrew](http://braumeister.org/formula/buku) for OS X
- [Debian Sid](https://packages.debian.org/sid/buku)
- [Ubuntu PPA](https://launchpad.net/~twodopeshaggy/+archive/ubuntu/jarun/)
- Void Linux repos ( `$ sudo xbps-install -S buku` )

## Shell completion

Shell completion scripts for Bash, Fish and Zsh can be found in respective subdirectories of [auto-completion/](https://github.com/jarun/Buku/blob/master/auto-completion). Please refer to your shell's manual for installation instructions.

`buku` has a [rofi frontend](https://github.com/carnager/buku_run) written by Rasmus Steinke.

## Usage

### Cmdline options

    usage: buku [OPTIONS] [KEYWORD [KEYWORD ...]]

    A powerful command-line bookmark manager. Your mini web!

    general options:
      -a, --add URL [tag, ...]
                           bookmark URL with comma-separated tags
      -u, --update [...]   update fields of bookmark at DB indices
                           accepts indices and ranges
                           refresh all titles, if no arguments
                           refresh titles of bookmarks at indices,
                           if no edit options are specified
      -d, --delete [...]   delete bookmarks. Valid inputs: either
                           a hyphenated single range (100-200),
                           OR space-separated indices (100 15 200)
                           delete search results with search options
                           delete all bookmarks, if no arguments
      -h, --help           show this information and exit

    edit options:
      --url keyword        specify url, works with -u only
      --tag [+|-] [...]    set comma-separated tags
                           clear tags, if no arguments
                           works with -a, -u
                           append specified tags, if preceded by '+'
                           remove specified tags, if preceded by '-'
      -t, --title [...]    manually set title, works with -a, -u
                           if no arguments:
                           -a: do not set title, -u: clear title
      -c, --comment [...]  description of the bookmark, works with
                           -a, -u; clears comment, if no arguments
      --immutable N        disable title fetch from web on update
                           works with -a, -u
                           N=0: mutable (default), N=1: immutable

    search options:
      -s, --sany keyword [...]
                           search records with ANY keyword
      -S, --sall keyword [...]
                           search records with ALL keywords
                           special keywords -
                           "blank": entries with empty title/tag
                           "immutable": entries with locked title
      --deep               match substrings ('pen' matches 'opened')
      --sreg expression    run a regex search
      --stag [...]         search bookmarks by a tag
                           list tags alphabetically, if no arguments

    encryption options:
      -l, --lock [N]       encrypt DB file with N (> 0, default 8)
                           hash iterations to generate key
      -k, --unlock [N]     decrypt DB file with N (> 0, default 8)
                           hash iterations to generate key

    power toys:
      -e, --export file    export bookmarks to Firefox format html
                           use --tag to export only specific tags
      -i, --import file    import bookmarks from html file; Firefox
                           and Google Chrome formats supported
      --markdown           use markdown with -e and -i
                           supported format: [title](url), 1 per line
      -m, --merge file     merge bookmarks from another buku database
      -p, --print [...]    show details of bookmark by DB index
                           accepts indices and ranges
                           show all bookmarks, if no arguments
      -f, --format N       fields to show in -p or search output
                           1: URL, 2: URL and tag, 3: title
      -r, --replace oldtag [newtag ...]
                           replace oldtag with newtag everywhere
                           delete oldtag, if no newtag
      -j, --json           Json formatted output for -p and search
      --noprompt           do not show the prompt, run and exit
      -o, --open [N]       open bookmark at DB index N in web browser
                           open a random index if N is omitted
      --shorten N/URL      shorten using tny.im url shortener service
                           accepts either a DB index or a URL
      --tacit              reduce verbosity
      --upstream           check latest upstream version available
      -z, --debug          show debug information and extra logs

    symbols:
      >                    title
      +                    comment
      #                    tags

### Operational notes

- The SQLite3 database file is stored in:
  - **$XDG_DATA_HOME/buku/bookmarks.db**, if XDG_DATA_HOME is defined (first preference) or
  - **$HOME/.local/share/buku/bookmarks.db**, if HOME is defined (second preference) or
  - the **current directory**.
- If the URL contains characters like `;`, `&` or brackets they may be interpreted specially by the shell. To avoid it, add the URL within single or double quotes (`'`/`"`).
- URLs are unique in DB. The same URL cannot be added twice.
- Bookmarks with immutable titles are listed with bold `(L)` after the URL.
- **Tags**:
  - Comma (`,`) is the tag delimiter in DB. A tag cannot have comma(s) in it. Tags are filtered (for unique tags) and sorted. Tags are stored in lower case and can be replaced, appended or deleted.
- **Update** operation:
  - If --title, --tag or --comment is passed without argument, clear the corresponding field from DB.
  - If --url is passed (and --title is omitted), update the title from web using the URL.
  - If indices are passed without any other options (--url, --title, --tag, --comment and --immutable), read the URLs from DB and update titles from web. Bookmarks marked immutable are skipped.
- **Delete** operation:
  - When a record is deleted, the last record is moved to the index.
  - Delete doesn't work with range and indices provided together as arguments. It's an intentional decision to avoid extra sorting, in-range checks and to keep the auto-DB compaction functionality intact. On the same lines, indices are deleted in descending order.
  - Can delete bookmarks matching a search, when combined with any of the search options.
- **Search** works in mysterious ways:
  - Case-insensitive.
  - Matches exact words in URL, title and tags.
  - --sany : match any of the keywords in URL, title or tags.
  - --sall : match all the keywords in URL, title or tags.
  - --deep : match **substrings** (`match` matches `rematched`) in URL, title and tags.
  - --sreg : match a regular expression (ignores --deep).
  - --stag : search bookmarks by a tag, or show all tags alphabetically with usage count (if no arguments).
  - Search results are indexed serially. This index is different from actual database index of a bookmark record which is shown in bold within `[]` after the URL.
- **Encryption** is optional and manual. AES256 algorithm is used. To use encryption, the database file should be unlocked (-k) before using buku and locked (-l) afterwards. Between these 2 operations, the database file lies unencrypted on the disk, and NOT in memory. Also, note that the database file is *unencrypted on creation*.
- **Proxy** support: environment variable *https_proxy*, if defined, is used to tunnel data for both http and https connections. The supported format is:

        http[s]://[username:password@]proxyhost:proxyport/

## GUI integration

![buku](http://i.imgur.com/8Y6PTPw.png)

`buku` can integrate in a GUI environment with simple tweaks.

### Add bookmarks from anywhere

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

#### Test drive

Select a URL anywhere or copy a link and press the keyboard shortcut to add it to the `buku` database. The addition might take a few seconds to reflect depending on your internet speed and the time `buku` needs to fetch the title from the URL. To avoid title fetch from the web, add the `-t` option to the script.

To verify that the bookmark has indeed been added, run:

    $ buku -p | tail -3
and check the entry.

#### Tips

- To add the last visited URL in Firefox to `buku`, use the following script:

        #!/bin/bash

        sqlite3 $HOME/.mozilla/firefox/*.default/places.sqlite "select url from moz_places where last_visit_date=(select max(last_visit_date) from moz_places)" | buku -a
- If you want to tag these bookmarks, look them up later using:

        $ buku -S blank
Use option `-u` to tag these bookmarks.

### Import bookmarks to browser

`buku` can export (or import) bookmarks in HTML format recognized by Firefox, Google Chrome and Internet Explorer.

To export all bookmarks, run:

    $ buku --export path_to_bookmarks.html
To export specific tags, run:

    $ buku --export path_to_bookmarks.html --tag tag 1, tag 2
Once exported, import the html file in your browser.

## As a library

`buku` can be used as a powerful bookmark management library. All functionality are available through carefully designed APIs. `main()` is a good usage example. It's also possible to use a custom database file in multi-user scenarios. Check out the documentation for the following APIs which accept an optional argument as database file:

    BukuDb.initdb(dbfile=None)
    BukuCrypt.encrypt_file(iterations, dbfile=None)
    BukuCrypt.decrypt_file(iterations, dbfile=None)
NOTE: This flexibility is not exposed in the program.

## Examples

1. **Add** a bookmark with **tags** `linux news` and `open source`, **comment** `Informative website on Linux and open source`, **fetch page title** from the web:

        $ buku -a https://tuxdiary.com linux news, open source -c Informative website on Linux and open source
        Title: [TuxDiary – Linux, open source, command-line, leisure.]
        Added at index 336

        336. https://tuxdiary.com
        > TuxDiary – Linux, open source, command-line, leisure.
        + Informative website on Linux and open source
        # linux news,open source
where, >: title, +: comment, #: tags
2. **Add** a bookmark with tags `linux news` and `open source` & **immutable custom title** `Linux magazine`:

        $ buku -a http://tuxdiary.com linux news, open source -t 'Linux magazine' --immutable 1
        336. http://tuxdiary.com (L)
        > Linux magazine
        # linux news,open source
Note that URL must precede tags.
3. **Add** a bookmark **without a title** (works for update too):

        $ buku -a http://tuxdiary.com linux news, open source -t
4. **Update** existing bookmark at index 15012014 with new URL, tags and comments, fetch title from the web:

        $ buku -u 15012014 --url http://tuxdiary.com/ --tag linux news, open source, magazine -c site for Linux utilities
5. **Fetch and update only title** for bookmark at 15012014:

        $ buku -u 15012014
6. **Update only comment** for bookmark at 15012014:

        $ buku -u 15012014 -c this is a new comment
Applies to --url, --title and --tag too.
7. **Export** bookmarks tagged `tag 1` or `tag 2` to HTML and markdown:

        $ buku -e bookmarks.html --tag tag 1, tag 2
        $ buku -e bookmarks.md --markdown --tag tag 1, tag 2
All bookmarks are exported if --tag is not specified.
8. **Import** bookmarks from HTML and markdown:

        $ buku -i bookmarks.html
        $ buku -i bookmarks.md --markdown
9. **Delete only comment** for bookmark at 15012014:

        $ buku -u 15012014 -c
Applies to --title and --tag too. URL cannot be deleted without deleting the bookmark.
10. **Update** or refresh **full DB** with page titles from the web:

        $ buku -u
        $ buku -u --tacit (show only failures and exceptions)
This operation does not modify the indexes, URLs, tags or comments. Only title is refreshed if fetched title is non-empty.
11. **Delete** bookmark at index 15012014:

        $ buku -d 15012014
        Index 15012020 moved to 15012014
The last index is moved to the deleted index to keep the DB compact.
12. **Delete all** bookmarks:

        $ buku -d
13. **Delete** a **range or list** of bookmarks:

        $ buku -d 100-200
        $ buku -d 100 15 200
14. **Search** bookmarks for **ANY** of the keywords `kernel` and `debugging` in URL, title or tags:

        $ buku -s kernel debugging
15. **Search** bookmarks with **ALL** the keywords `kernel` and `debugging` in URL, title or tags:

        $ buku -S kernel debugging
16. **Search** bookmarks **tagged** `general kernel concepts`:

        $ buku --stag general kernel concepts
17. List **all unique tags** alphabetically:

        $ buku --stag
18. **Encrypt or decrypt** DB with **custom number of iterations** (15) to generate key:

        $ buku -l 15
        $ buku -k 15
The same number of iterations must be specified for one lock & unlock instance. Default is 8, if omitted.
19. **Show details** of bookmark at index 15012014 and ranges 20-30, 40-50:

        $ buku -p 20-30 15012014 40-50
20. **Show all** bookmarks with real index from database:

        $ buku -p
        $ buku -p | more
21. **Replace tag** 'old tag' with 'new tag':

        $ buku -r 'old tag' new tag
22. **Delete tag** 'old tag' from DB:

        $ buku -r 'old tag'
23. **Append (or delete) tags** 'tag 1', 'tag 2' to (or from) existing tags of bookmark at index 15012014:

        $ buku -u 15012014 --tag + tag 1, tag 2
        $ buku -u 15012014 --tag - tag 1, tag 2
24. **Open URL** at index 15012014 in browser:

        $ buku -o 15012014
25. List bookmarks with **no title or tags** for bookkeeping:

        $ buku -S blank
26. List bookmarks with **immutable title**:

        $ buku -S immutable
27. **Shorten URL** www.google.com and the URL at index 20:

        $ buku --shorten www.google.com
        $ buku --shorten 20
28. More **help**:

        $ buku
        $ man buku

## Contributions

Pull requests are welcome. Please visit [#78](https://github.com/jarun/Buku/issues/78) for a list of TODOs.

## Mentions

- [One Thing Well](http://onethingwell.org/post/144952807044/buku)
- [It's F.O.S.S.](https://itsfoss.com/buku-command-line-bookmark-manager-linux/)

## Copyright

Copyright © 2015-2016 [Arun Prakash Jana](mailto:engineerarun@gmail.com)
