<h1 align="center">Buku</h1>

<p align="center">
<a href="https://github.com/jarun/Buku/releases/latest"><img src="https://img.shields.io/github/release/jarun/buku.svg" alt="Latest release" /></a>
<a href="https://aur.archlinux.org/packages/buku"><img src="https://img.shields.io/aur/version/buku.svg" alt="AUR" /></a>
<a href="http://braumeister.org/formula/buku"><img src="https://img.shields.io/homebrew/v/buku.svg" alt="Homebrew" /></a>
<a href="https://github.com/jarun/buku/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-GPLv3-yellow.svg?maxAge=2592000" alt="License" /></a>
</p>

<p align="center">
<a href="https://asciinema.org/a/b7ymahqwgt92jev32q4cmcm8h"><img src="https://asciinema.org/a/b7ymahqwgt92jev32q4cmcm8h.png" alt="Asciicast" width="600"/></a>
</p>

`buku` is a powerful cmdline bookmark management utility written in Python3 and SQLite3. When I started writing it, I couldn't find a flexible cmdline solution with a portable database. Hence, `Buku` (after my son's nickname).

`buku` can handle piped input, which lets you combine it with `xsel` (on Linux) and add bookmarks from anywhere without touching the terminal.

Ref: [buku & xsel: add selected or copied URL as bookmark](http://tuxdiary.com/2016/03/26/buku-xsel/)

Got some suggestions? [![gitter chat](https://img.shields.io/gitter/room/jarun/buku.svg?maxAge=2592000)](https://gitter.im/jarun/Buku) with us.

Find `buku` useful? If you would like to donate, visit the
[![Donate Button](https://img.shields.io/badge/paypal-donate-orange.svg?maxAge=2592000)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=RMLTQ76JSXJ4Q) page.

Copyright (C) 2015-2016 [Arun Prakash Jana](mailto:engineerarun@gmail.com).

# Features

- Add, tag, comment on, search, update, remove bookmarks
- Fetch page title from the web (default) or add manually
- Import HTML bookmark exports from Firefox, Google Chrome or IE
- Open search results directly in browser
- Manual password protection using AES256 encryption
- Modify or delete tags, list all unique tags alphabetically
- Refresh all bookmarks online in one shot
- Tab-completion scripts for Bash, Fish and Zsh
- Man page with examples
- Several options for power users (see help or man page)
- Fast and clean interface
- Minimal dependencies

# Table of Contents

- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [Installing from this repository](#installing-from-this-repository)
  - [Running as a standalone utility](#running-as-a-standalone-utility)
  - [Shell completion](#shell-completion)
  - [Installing with a package manager](#installing-with-a-package-manager)
- [Usage](#usage)
  - [Cmdline options](#cmdline-options)
  - [Operational notes](#operational-notes)
- [Examples](#examples)
- [Contributions](#contributions)
- [Developers](#developers)

# Installation

## Dependencies

`buku` requires Python 3.x to work.

Optional dependencies:
- Encryption: PyCrypto
- Import bookmarks: Beautiful Soup

Run:

    $ sudo pip3 install pycrypto beautifulsoup4
or on Ubuntu:

    $ sudo apt-get install python3-crypto python3-bs4

## Installing from this repository

If you have git installed, run:

    $ git clone https://github.com/jarun/buku/
or download the latest [stable release](https://github.com/jarun/Buku/releases/latest) or [development version](https://github.com/jarun/buku/archive/master.zip).

Install to default location (`/usr/local`):

    $ sudo make install

To remove, run:

    $ sudo make uninstall
`PREFIX` is supported. You may need to use `sudo` with `PREFIX` depending on your permissions on destination directory.

## Running as a standalone utility

`buku` is a standalone utility. From the containing directory, run:

    $ ./buku

## Shell completion

Shell completion scripts for Bash, Fish and Zsh can be found in respective subdirectories of [auto-completion/](https://github.com/jarun/buku/blob/master/auto-completion). Please refer to your shell's manual for installation instructions.

## Installing with a package manager

`buku` is also available on
 - [AUR](https://aur.archlinux.org/packages/buku/) for Arch Linux
 - Void Linux repos ( `$ sudo xbps-install -S buku` )
 - [Homebrew](http://braumeister.org/formula/buku) for OS X, or its Linux fork, [Linuxbrew](https://github.com/Linuxbrew/linuxbrew/blob/master/Library/Formula/buku.rb)

# Usage

## Cmdline options

**NOTE:** If you are using `buku` v1.9 or below please refer to the installed man page or program help.

    usage: buku [-a URL [tags ...]] [-u [N]] [-i file] [-d [N]]
                [--url keyword] [--tag [...]] [-t [...]] [-c [...]]
                [-s keyword [...]] [-S keyword [...]] [--st [...]]
                [-k [N]] [-l [N]] [-p [N]] [-f N] [-r oldtag [newtag ...]]
                [-j] [--merge file] [--noprompt] [-o N] [-z] [-h]

    A private command-line bookmark manager. Your mini web!

    general options:
      -a, --add URL [tags ...]
                           bookmark URL with comma-separated tags
      -u, --update [N]     update fields of bookmark at DB index N
                           refresh all titles, if no arguments
                           refresh title of bookmark at N, if only
                           N is specified without any edit options
      -d, --delete [N]     delete bookmark at DB index N
                           delete all bookmarks, if no arguments
      -i, --import file    import bookmarks from html file; Firefox,
                           Google Chrome and IE formats supported
      -h, --help           show this information

    edit options:
      --url keyword        specify url, works with -u only
      --tag [...]          set comma-separated tags, works with -a, -u
                           clears tags, if no arguments
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
      --st, --stag [...]   search bookmarks by tag
                           list all tags alphabetically, if no arguments

    encryption options:
      -l, --lock [N]       encrypt DB file with N (> 0, default 8)
                           hash iterations to generate key
      -k, --unlock [N]     decrypt DB file with N (> 0, default 8)
                           hash iterations to generate key

    power toys:
      -p, --print [N]      show details of bookmark at DB index N
                           show all bookmarks, if no arguments
      -f, --format N       modify -p output
                           N=1: show only URL, N=2: show URL and tag
      -r, --replace oldtag [newtag ...]
                           replace oldtag with newtag everywhere
                           delete oldtag, if no newtag
      -j, --json           Json formatted output for -p, -s, -S, --st
      --merge file         merge bookmarks from another buku database
      --noprompt           do not show the prompt, run and exit
      -o, --open N         open bookmark at DB index N in web browser
      -z, --debug          show debug information and additional logs

    prompt keys:
      1-N                  open the Nth search result in web browser
      double Enter         exit buku

## Operational notes

- The SQLite3 database file is stored in:
  - **$XDG_DATA_HOME/buku/bookmarks.db**, if XDG_DATA_HOME is defined (first preference) or
  - **$HOME/.local/share/buku/bookmarks.db**, if HOME is defined (second preference) or
  - the **current directory**.
- Before version 1.9, buku stored its database in $HOME/.cache/buku/bookmarks.db. If the file exists, buku automatically moves it to new location.
- It's  advisable  to copy URLs directly from the browser address bar, i.e., along with the leading `http://` or `https://` token. buku looks up title data (found within <title></title> tags of HTML) from the web ONLY for fully-formed HTTP(S) URLs.
- If the URL contains characters like `;`, `&` or brackets they may be interpreted specially by the shell. To avoid it, add the URL within single or double (`'`/`"`) quotes.
- URLs are unique in DB. The same URL cannot be added twice. You can update tags and re-fetch title data.
- **Update** operation:
  - If --title, --tag or --comment is passed without argument, clear the corresponding field from DB.
  - If --url is passed (and --title is omitted), update the title from web using the URL.
  - If index number is passed without any other options (--url, --title, --tag and --comment), read the URL from DB and update title from web.
- **Search** works in mysterious ways:
  - Case-insensitive.
  - Substrings match (`match` matches `rematched`) for URL, title and tags.
  - -s : match any of the keywords in URL, title or tags.
  - -S : match all the keywords in URL, title or tags.
  - --st : search bookmarks by tag, or show all tags alphabetically.
  - You can search bookmarks by tag (see [examples](#examples)).
  - Search results are indexed serially. This index is different from actual database index of a bookmark record which is shown within `[]` after the URL.
- Auto DB compaction: when a record is deleted, the last record is moved to the index.
- **Encryption** is optional and manual. AES256 algorithm is used. If you choose to use encryption, the database file should be unlocked (-k) before using buku and locked (-l) afterwards. Between these 2 operations, the database file lies unencrypted on the disk, and NOT in memory. Also, note that the database file is *unencrypted on creation*.

# Examples

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
7. Import bookmarks:

        $ buku -i bookmarks.html
HTML exports from Firefox, Google Chrome and IE are supported.
8. **Delete only comment** for bookmark at 15012014:

        $ buku -u 15012014 -c
Applies to --title and --tag too. URL cannot be deleted without deleting the bookmark.
9. **Update** or refresh **full DB** with page titles from the web:

        $ buku -u
This operation does not modify the indexes, URLs, tags or comments. Only title is refreshed if fetched title is non-empty.
10. **Delete** bookmark at index 15012014:

        $ buku -d 15012014
        Index 15012020 moved to 15012014
The last index is moved to the deleted index to keep the DB compact.
11. **Delete all** bookmarks:

        $ buku -d
12. **Search** bookmarks for **ANY** of the keywords `kernel` and `debugging` in URL, title or tags:

        $ buku -s kernel debugging
13. **Search** bookmarks with **ALL** the keywords `kernel` and `debugging` in URL, title or tags:

        $ buku -S kernel debugging

14. **Search** bookmarks with **tag** `general kernel concepts`:

        $ buku --st general kernel concepts
Note the commas (,) before and after the tag. Comma is the tag delimiter in DB.
15. List **all unique tags** alphabetically:

        $ buku --st
16. **Encrypt or decrypt** DB with **custom number of iterations** (15) to generate key:

        $ buku -l 15
        $ buku -k 15
The same number of iterations must be used for one lock & unlock instance. Default is 8.
17. **Show details** of bookmark at index 15012014:

        $ buku -p 15012014
18. **Show all** bookmarks with real index from database:

        $ buku -p
        $ buku -p | more
19. **Replace tag** 'old tag' with 'new tag':

        $ buku -r 'old tag' new tag
20. **Delete tag** 'old tag' from DB:

        $ buku -r 'old tag'
21. **Open URL** at index 15012014 in browser:

        $ buku -o 15012014
22. To list bookmarks with no title or tags for **bookkeeping**:

        $ buku -S blank
23. More **help**:

        $ buku
        $ man buku

# Contributions

Pull requests are welcome. Please visit [#14](https://github.com/jarun/Buku/issues/14) for a list of TODOs.

# Developers

[Arun Prakash Jana](mailto:engineerarun@gmail.com)

Special thanks to the community for valuable suggestions and ideas.
