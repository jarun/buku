<h1 align="center">Buku</h1>

<p align="center">
<a href="https://aur.archlinux.org/packages/buku"><img src="https://img.shields.io/aur/version/buku.svg" alt="AUR" /></a>
<a href="http://braumeister.org/formula/buku"><img src="https://img.shields.io/homebrew/v/buku.svg" alt="Homebrew" /></a>
<a href="https://github.com/jarun/Buku/releases/latest"><img src="https://img.shields.io/github/release/jarun/buku.svg" alt="Latest release" /></a>
<a href="https://github.com/jarun/buku/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-GPLv3-yellow.svg?maxAge=2592000" alt="License" /></a>
</p>

<p align="center">
<a href="https://asciinema.org/a/6x3nu7ez9t0flk1knhiabwduv"><img src="https://asciinema.org/a/6x3nu7ez9t0flk1knhiabwduv.png" alt="Asciicast" width="600"/></a>
</p>

`buku` is a powerful cmdline bookmark management utility written in Python3 and SQLite3. When I started writing it, I couldn't find a flexible cmdline solution with a portable database. Hence, `Buku` (after my son's nickname).

You can add bookmarks to `buku` with tags and page title fetched from the web, search, update and remove bookmarks. You can open the URLs from search results directly in the browser. Encryption is supported, optionally with custom number of hash passes for key generation.

`buku` can also handle piped input, which lets you combine it with `xsel` (on Linux) and use a shortcut to add selected or copied text as bookmark without touching the terminal.
Ref: [buku & xsel: add selected or copied URL as bookmark](http://tuxdiary.com/2016/03/26/buku-xsel/)

Find `buku` useful? If you would like to donate, visit the
[![Donate Button](https://img.shields.io/badge/paypal-donate-orange.svg?maxAge=2592000)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=RMLTQ76JSXJ4Q) page.

Copyright (C) 2015 [Arun Prakash Jana](mailto:engineerarun@gmail.com).

# Features

- Add, update or remove a bookmark
- Tag bookmarks
- Manual password protection using AES256 encryption
- Fetch page title from the web (default) or add a custom page title manually
- Use (partial) tags or keywords to search bookmarks
- Any or all search keyword match options
- Unique URLs to avoid duplicates
- Open search results in browser
- Open bookmark in browser using index
- Handle piped input (combine with xsel and add bookmarks directly from browser)
- Supports HTTP compression
- Optional Json formatted output
- Modify or delete tags in DB
- Show all unique tags sorted alphabetically
- Show single bookmark by ID or all bookmarks in a go
- Refresh all bookmarks online
- Auto DB compaction on bookmark removal
- Delete all bookmarks from DB
- Show all bookmarks with empty titles or no tags (for bookkeeping)
- Supports Unicode characters in URL
- UTF-8 request and response, page character set detection
- Secure parameterized SQLite3 queries to access database
- Handle multiple HTTP redirections (reports redirected URL, loops, IP blocking)
- Coloured output for clarity
- Easily create compatible batch add or update scripts
- Unformatted selective output (for creating batch update scripts)
- Manpage with examples for quick reference
- Fast and clean (no ads or clutter)
- Minimal dependencies
- Open source and free

# Table of Contents

- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [Installing from this repository](#installing-from-this-repository)
  - [Running as a standalone utility](#running-as-a-standalone-utility)
  - [Installing with a package manager](#installing-with-a-package-manager)
- [Usage](#usage)
  - [Cmdline options](#cmdline-options)
  - [Operational notes](#operational-notes)
- [Examples](#examples)
  - [Bookkeeping](#bookkeeping)
- [Contributions](#contributions)
- [Developers](#developers)

# Installation

## Dependencies
`buku` requires Python 3.x to work.

For optional encryption support, install PyCrypto module. Run:

    $ sudo pip3 install pycrypto
or on Ubuntu:

    $ sudo apt-get install python3-crypto
## Installing from this repository
If you have git installed, run:

    $ git clone https://github.com/jarun/buku/
or download the latest [stable release](https://github.com/jarun/Buku/releases/latest) or [development version](https://github.com/jarun/buku/archive/master.zip).

Install to default location:

    $ sudo make install
or, a custom location (PREFIX):

    $ PREFIX=/path/to/prefix make install

To remove, run:

    $ sudo make uninstall
or, if you have installed to a custom location (PREFIX):

    $ PREFIX=/path/to/prefix make uninstall
You may need to use `sudo` with `PREFIX` depending on your permissions on destination directory.

## Running as a standalone utility
`buku` is a standalone utility. From the containing directory, run:

    $ ./buku
## Installing with a package manager
`buku` is also available on
 - [AUR](https://aur.archlinux.org/packages/buku/) for Arch Linux
 - Void Linux repos ( `$ sudo xbps-install -S buku` )
 - [Homebrew](http://braumeister.org/formula/buku) for OS X, or its Linux fork, [Linuxbrew](https://github.com/Linuxbrew/linuxbrew/blob/master/Library/Formula/buku.rb)

# Usage

## Cmdline options

**NOTE:** If you are using `buku` v1.9 or below please refer to the installed manpage or program help. The development version has significant changes.

    usage: buku [-a URL [tags ...]] [-u [N [URL tags ...]]]
                [-t [...]] [-d [N]] [-h]
                [-s keyword [...]] [-S keyword [...]]
                [-k [N]] [-l [N]] [-p [N]] [-f N]
                [-r oldtag [newtag ...]] [-j] [-o N] [-z]

    A private cmdline bookmark manager. Your mini web!

    general options:
      -a, --add URL [tags ...]
                           bookmark URL with comma separated tags
      -u, --update [N [URL tags ...]]
                           update fields of bookmark at DB index N
                           refresh all titles, if no arguments
                           if URL omitted and -t is unused, update
                           title of bookmark at index N from web
      -t, --title [...]    manually set title, works with -a, -u
                           do not set title, if no arguments
      -d, --delete [N]     delete bookmark at DB index N
                           delete all bookmarks, if no arguments
      -h, --help           show this information

    search options:
      -s, --sany keyword [...]
                           search bookmarks for ANY matching keyword
      -S, --sall keyword [...]
                           search bookmarks with ALL keywords
                           special keywords -
                           "tags" : list all tags alphabetically
                           "blank": list entries with empty title/tag

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
                           replace oldtag with newtag in all bookmarks
                           delete oldtag, if no newtag
      -j, --jason          Json formatted output, works with -p, -s
      -o, --open           open bookmark at DB index N in web browser
      -z, --debug          show debug information and additional logs

    prompt keys:
      1-N                  open the Nth search result in web browser
      Enter                exit buku

## Operational notes

- The SQLite3 database file is stored in:
  - **$XDG_DATA_HOME/buku/bookmarks.db**, if XDG_DATA_HOME is defined (first preference) or
  - **$HOME/.local/share/buku/bookmarks.db**, if HOME is defined (second preference) or
  - the **current directory**, e.g. on Windows.
- Before version 1.9, `buku`stored its database in **$HOME/.cache/buku/bookmarks.db**. If the file exists, buku automatically moves it to new location.
- It's  advisable  to copy URLs directly from the browser address bar, i.e., along with the leading `http://` or `https://` token. `buku` looks up title data (found within <title></title> tags of HTML) from the web ONLY for fully-formed HTTP(S) URLs.
- If the URL contains characters like `;`, `&` or brackets they may be interpreted specially by the shell. To avoid it, add the URL within single or double (`'`/`"`) quotes.
- URLs are unique in DB. The same URL cannot be added twice. You can update tags and re-fetch title data.
- Search works in mysterious ways:
  - Case-insensitive.
  - Substrings match (`match` matches `rematched`) for URL, title and tags.
  - `-s` : match any of the keywords in URL, title or tags.
  - `-S` : match all the keywords in URL, title or tags.
  - You can search bookmarks by tag (refer examples).
  - Search results are indexed serially. This index is different from actual database index of a bookmark record which is shown within `[]` after the URL.
- When a record is deleted, the last record is moved to the index.
- Encryption is optional and manual. AES256 algorithm is used. If you choose to use encryption, the database file should be unlocked (`-k`) before using buku and locked (`-l`) afterwards. Between these 2 operations, the database file lies unencrypted on the disk, and NOT in memory. Also, note that the database file is <i>unencrypted on creation</i>.

# Examples
1. **Add** a bookmark with **tags** `linux news` and `open source`, **fetch page title** from the web:

        $ buku -a http://tuxdiary.com linux news, open source
        Title: [TuxDiary | Linux, open source and a pinch of leisure.]
        Added at index 15012014
2. **Add** a bookmark with tags `linux news` and `open source` & **custom title** `Linux magazine`:

        $ buku -a http://tuxdiary.com linux news, open source -t 'Linux magazine'
        Added at index 15012014
Note that URL must precede tags.
3. **Add** a bookmark **without a title** (works for update too):

        $ buku -a http://tuxdiary.com linux news, open source -t
4. **Update** existing bookmark at index 15012014 with new URL and tags, fetch title from the web:

        $ buku -u 15012014 http://tuxdiary.com/ linux news, open source, magazine
        Title: [TuxDiary | Linux, open source and a pinch of leisure.]
        Updated index 15012014
Tags are updated too. Original tags are removed.
5. **Update** or refresh **full DB** with page titles from the web:

        $ buku -u
This operation does not modify the indexes, URLs or tags. Only title is refreshed if fetched title is non-empty.
6. **Delete** bookmark at index 15012014:

        $ buku -d 15012014
        Index 15012020 moved to 15012014
The last index is moved to the deleted index to keep the DB compact.
7. **Delete all** bookmarks:

        $ buku -d
8. List **all unique tags** alphabetically:

        $ buku -S tags
9. **Replace tag** 'old tag' with 'new tag':

        $ buku -r 'old tag' new tag
10. **Delete tag** 'old tag' from DB:

        $ buku -r 'old tag'
11. **Show details** of bookmark at index 15012014:

        $ buku -p 15012014
12. **Show all** bookmarks with real index from database:

        $ buku -p
13. **Open URL** at index 15012014 in browser:

        $ buku -o 15012014
14. **Search** bookmarks for **ANY** of the keywords `*kernel*` and `*debugging*` in URL, title or tags:

        $ buku -s kernel debugging
15. **Search** bookmarks with **ALL** the keywords `*kernel*` and `*debugging*` in URL, title or tags:

        $ buku -S kernel debugging

16. **Search** bookmarks with **tag** *general kernel concepts*:

        $ buku -S ',general kernel concepts,'
Note the commas (,) before and after the tag. Comma is the tag delimiter in DB.
17. Encrypt/decrypt DB with **custom number of iterations** (15) to generate key:

        $ buku -l 15
        $ buku -k 15
The same number of iterations must be used for one lock & unlock instance.
18. More **help**:

        $ buku
        $ man buku

## Bookkeeping

1. To list bookmarks with **no title or tags**:

        $ buku -e
Use the `-u` option to add title or tags to those entries, if you want to.
2. `buku` doesn't have any **import feature** of its own. To import URLs in **bulk**, create a script with URLs and tags like the following (check TIP below):

        #!/bin/bash
        buku -a https://wireless.wiki.kernel.org/ networking, device drivers
        buku -a https://courses.engr.illinois.edu/ece390/books/artofasm/ArtofAsm.html assembly
        buku -a http://www.tittbit.in/
        buku -a http://www.mikroe.com/chapters/view/65/ electronics
        buku -a "http://msdn.microsoft.com/en-us/library/bb470206(v=vs.85).aspx" file systems
        buku -a http://www.ibm.com/developerworks/linux/library/l-linuxboot/index.html boot process
Make the script executable and run to batch add bookmarks.
3. To **update selected URLs** (refresh) along with your tags, first get the unformatted selective output with URL and tags:

        $ buku -p 0 -x 2 | tee myurls
Remove the lines you don't need. Add `buku -u ` in front of all the other lines (check TIP below). Should look like:

        #!/bin/bash
        buku -u 50 https://wireless.wiki.kernel.org/ networking, device drivers
        buku -u 51 https://courses.engr.illinois.edu/ece390/books/artofasm/ArtofAsm.html assembly
        buku -u 52 http://www.tittbit.in/
        buku -u 53 http://www.mikroe.com/chapters/view/65/ electronics
        buku -u 54 "http://msdn.microsoft.com/en-us/library/bb470206(v=vs.85).aspx" file systems
        buku -u 55 http://www.ibm.com/developerworks/linux/library/l-linuxboot/index.html boot process
Run the script:

        $ chmod +x myurls
        $ ./myurls


####TIP

Add the same text at the beginning of multiple lines:

**vim**
  - Press `Ctrl-v` to select the first column of text in the lines you want to change (visual mode).
  - Press `Shift-i` and type the text you want to insert.
  - Hit `Esc`, wait 1 second and the inserted text will appear on every line.

**sed**

    $ sed -i 's/^/buku -u /' filename

# Contributions
Pull requests are welcome. Please visit [issue #14](https://github.com/jarun/Buku/issues/14) for a list of TODOs.

# Developers
[Arun Prakash Jana](mailto:engineerarun@gmail.com)

Special thanks to the community for valuable suggestions and ideas.
