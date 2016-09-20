<h1 align="center">Buku</h1>

<p align="center">
<a href="https://github.com/jarun/Buku/releases/latest"><img src="https://img.shields.io/github/release/jarun/buku.svg" alt="Latest release" /></a>
<a href="https://aur.archlinux.org/packages/buku"><img src="https://img.shields.io/aur/version/buku.svg" alt="AUR" /></a>
<a href="http://braumeister.org/formula/buku"><img src="https://img.shields.io/homebrew/v/buku.svg" alt="Homebrew" /></a>
<a href="https://github.com/jarun/buku/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-GPLv3-yellow.svg?maxAge=2592000" alt="License" /></a>
<a href="https://travis-ci.org/jarun/Buku"><img src="https://travis-ci.org/jarun/Buku.svg?branch=master" alt="Build Status" /></a>
</p>

<p align="center">
<a href="https://asciinema.org/a/2bc3vq5ndxfvg0sm9jp8xlz03"><img src="https://asciinema.org/a/2bc3vq5ndxfvg0sm9jp8xlz03.png" alt="Asciicast" width="625"/></a>
</p>

`buku` is a powerful bookmark management utility written in Python3 and SQLite3. When I started writing it, I couldn't find a flexible cmdline solution with a private, portable, merge-able database along with browser integration. Hence, `Buku` (after my son's nickname).

`buku` can handle piped input, which lets you combine it with `xsel` (on Linux) or `pbpaste` (on Mac) and add bookmarks from anywhere without touching the terminal. Ref: [buku & xsel: add selected or copied URL as bookmark](http://tuxdiary.com/2016/03/26/buku-xsel/)

`buku` has a [rofi frontend](https://github.com/carnager/buku_run) written by Rasmus Steinke.

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
  - [Installing with a package manager](#installing-with-a-package-manager)
  - [Debian package](#debian-package)
- [Shell completion](#shell-completion)
- [Usage](#usage)
  - [Cmdline options](#cmdline-options)
  - [Operational notes](#operational-notes)
- [Examples](#examples)
- [Contributions](#contributions)
- [Mentions](#mentions)
- [Copyright](#copyright)

## Features

- Add, open, tag, comment on, search, update, remove URLs
- Merge-able portable database, to sync between systems
- Import/export bookmarks HTML (Firefox, Google Chrome, IE compatible)
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

### Running as a standalone utility

`buku` is a standalone utility. From the containing directory, run:

    $ ./buku

### Installing with a package manager

`buku` is also available on
 - [AUR](https://aur.archlinux.org/packages/buku/) for Arch Linux
 - Void Linux repos ( `$ sudo xbps-install -S buku` )
 - [Homebrew](http://braumeister.org/formula/buku) for OS X
 - [Debian Sid](https://packages.debian.org/unstable/main/buku)

### Debian package

If you are on a Debian (including Ubuntu) based system visit [the latest stable release](https://github.com/jarun/Buku/releases/latest) and download the`.deb`package. To install, run:

    $ sudo dpkg -i buku-$version-all.deb

Please substitute `$version` with the appropriate package version.

## Shell completion

Shell completion scripts for Bash, Fish and Zsh can be found in respective subdirectories of [auto-completion/](https://github.com/jarun/Buku/blob/master/auto-completion). Please refer to your shell's manual for installation instructions.

## Usage

### Cmdline options

    usage: buku [OPTIONS] [KEYWORD [KEYWORD ...]]

    A powerful command-line bookmark manager. Your mini web!

    general options:
      -a, --add URL [tags ...]
                           bookmark URL with comma-separated tags
      -u, --update [...]   update fields of bookmark at DB indices
                           refresh all titles, if no arguments
                           refresh titles of bookmarks at indices,
                           if no edit options are specified
                           accepts indices and ranges
      -d, --delete [...]   delete bookmarks. Valid inputs: either
                           a hyphenated single range (100-200),
                           OR space-separated indices (100 15 200)
                           delete search results with search options
                           delete all bookmarks, if no arguments
      -h, --help           show this information and exit

    edit options:
      --url keyword        specify url, works with -u only
      --tag [+|-] [...]    set comma-separated tags, works with -a, -u
                           clear tags, if no arguments
                           append specified tags, if preceded by '+'
                           remove specified tags, if preceded by '-'
      -t, --title [...]    manually set title, works with -a, -u
                           if no arguments:
                           -a: do not set title, -u: clear title
      -c, --comment [...]  description of the bookmark, works with
                           -a, -u; clears comment, if no arguments

    search options:
      -s, --sany keyword [...]
                           search bookmarks for ANY matching keyword
      -S, --sall keyword [...]
                           search bookmarks with ALL keywords
                           special keyword -
                           "blank": list entries with empty title/tag
      --deep               match substrings ('pen' matches 'opened')
      --st, --stag [...]   search bookmarks by tag
                           list tags alphabetically, if no arguments

    encryption options:
      -l, --lock [N]       encrypt DB file with N (> 0, default 8)
                           hash iterations to generate key
      -k, --unlock [N]     decrypt DB file with N (> 0, default 8)
                           hash iterations to generate key

    power toys:
      -e, --export file    export bookmarks to Firefox format html
                           use --tag to export only specific tags
      -i, --import file    import bookmarks from html file; Firefox,
                           Google Chrome and IE formats supported
      -m, --merge file     merge bookmarks from another buku database
      -p, --print [N]      show details of bookmark at DB index N
                           show all bookmarks, if no arguments
      -f, --format N       modify -p output
                           N=1: show only URL, N=2: show URL and tag
      -r, --replace oldtag [newtag ...]
                           replace oldtag with newtag everywhere
                           delete oldtag, if no newtag
      -j, --json           Json formatted output for -p, -s, -S, --st
      --noprompt           do not show the prompt, run and exit
      -o, --open N         open bookmark at DB index N in web browser
      -z, --debug          show debug information and additional logs

    prompt keys:
      1-N                  open the Nth search result in web browser
                           ranges, space-separated result indices work
      double Enter         exit buku

    symbols:
      >                    title
      +                    comment
      #                    tags

### Operational notes

- The SQLite3 database file is stored in:
  - **$XDG_DATA_HOME/buku/bookmarks.db**, if XDG_DATA_HOME is defined (first preference) or
  - **$HOME/.local/share/buku/bookmarks.db**, if HOME is defined (second preference) or
  - the **current directory**.
- It's  advisable  to copy URLs directly from the browser address bar, i.e., along with the leading `http://` or `https://` token. buku looks up title data (found within <title></title> tags of HTML) from the web ONLY for fully-formed HTTP(S) URLs.
- If the URL contains characters like `;`, `&` or brackets they may be interpreted specially by the shell. To avoid it, add the URL within single or double quotes (`'`/`"`).
- URLs are unique in DB. The same URL cannot be added twice. You can update tags and re-fetch title data.
- **Tags**:
  - Comma (`,`) is the tag delimiter in DB. Any tag cannot have comma(s) in it. Tags are filtered (for unique tags) and sorted.
- **Update** operation:
  - If --title, --tag or --comment is passed without argument, clear the corresponding field from DB.
  - If --url is passed (and --title is omitted), update the title from web using the URL.
  - If indices are passed without any other options (--url, --title, --tag and --comment), read the URLs from DB and update titles from web.
- **Delete** operation:
  - When a record is deleted, the last record is moved to the index.
  - Delete doesn't work with range and indices provided together as arguments. It's an intentional decision to avoid extra sorting, in-range checks and to keep the auto-DB compaction functionality intact. On the same lines, indices are deleted in descending order.
  - Can delete bookmarks matching a search, when combined with any of the search options.
- **Search** works in mysterious ways:
  - Case-insensitive.
  - Matches exact words in URL, title and tags.
  - -s : match any of the keywords in URL, title or tags.
  - -S : match all the keywords in URL, title or tags.
  - --deep : match **substrings** (`match` matches `rematched`) in URL, title and tags.
  - --st : search bookmarks by tag, or show all tags alphabetically.
  - Search results are indexed serially. This index is different from actual database index of a bookmark record which is shown in bold within `[]` after the URL.
- **Encryption** is optional and manual. AES256 algorithm is used. If you choose to use encryption, the database file should be unlocked (-k) before using buku and locked (-l) afterwards. Between these 2 operations, the database file lies unencrypted on the disk, and NOT in memory. Also, note that the database file is *unencrypted on creation*.

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
2. **Add** a bookmark with tags `linux news` and `open source` & **custom title** `Linux magazine`:

        $ buku -a http://tuxdiary.com linux news, open source -t 'Linux magazine'
        Added at index 15012014
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
7. **Export** bookmarks tagged `tag 1` or `tag 2`:

        $ buku -e bookmarks.html tag 1, tag 2
All bookmarks are exported if --tag is not specified.
8. **Import** bookmarks:

        $ buku -i bookmarks.html
HTML exports from Firefox, Google Chrome and IE are supported.
9. **Delete only comment** for bookmark at 15012014:

        $ buku -u 15012014 -c
Applies to --title and --tag too. URL cannot be deleted without deleting the bookmark.
10. **Update** or refresh **full DB** with page titles from the web:

        $ buku -u
This operation does not modify the indexes, URLs, tags or comments. Only title is refreshed if fetched title is non-empty.
11. **Delete** bookmark at index 15012014:

        $ buku -d 15012014
        Index 15012020 moved to 15012014
The last index is moved to the deleted index to keep the DB compact.
12. **Delete all** bookmarks:

        $ buku -d
13. **Delete** a **range or list** of bookmarks:

        $ buku -d 100-200     // delete bookmarks from index 100 to 200
        $ buku 100 15 200     // delete bookmarks at indices 100, 15 and 200
14. **Search** bookmarks for **ANY** of the keywords `kernel` and `debugging` in URL, title or tags:

        $ buku -s kernel debugging
15. **Search** bookmarks with **ALL** the keywords `kernel` and `debugging` in URL, title or tags:

        $ buku -S kernel debugging

16. **Search** bookmarks **tagged** `general kernel concepts`:

        $ buku --st general kernel concepts
17. List **all unique tags** alphabetically:

        $ buku --st
18. **Encrypt or decrypt** DB with **custom number of iterations** (15) to generate key:

        $ buku -l 15
        $ buku -k 15
The same number of iterations must be specified for one lock & unlock instance. Default is 8, if omitted.
19. **Show details** of bookmark at index 15012014:

        $ buku -p 15012014
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
25. To list bookmarks with no title or tags for **bookkeeping**:

        $ buku -S blank
26. More **help**:

        $ buku
        $ man buku

## Contributions

Pull requests are welcome. Please visit [#39](https://github.com/jarun/Buku/issues/39) for a list of TODOs.

## Mentions

- [One Thing Well](http://onethingwell.org/post/144952807044/buku)

## Copyright

Copyright (C) 2015-2016 [Arun Prakash Jana](mailto:engineerarun@gmail.com)
