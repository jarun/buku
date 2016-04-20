# Buku

![Screenshot](http://i.imgur.com/UPKcSuN.png)

`buku` is a powerful cmdline bookmark management utility written in Python3 and SQLite3. `buku` exists because of my monumental dependency on <a href="http://historio.us/">historious</a>. I wanted the same database on my local system. However, I couldn't find an equally flexible cmdline solution. Hence, `Buku` (after my son's nickname).

You can add bookmarks to `buku` with title and tags, optionally fetch page title from web, search, update and remove bookmarks. You can open the URLs from search results directly in the browser. Encryption is supported, optionally with custom number of hash passes for key generation.

`buku` can also handle piped input, which lets you combine it with `xsel` (on Linux) and use a shortcut to add selected or copied text as bookmark without touching the terminal.
Ref: [buku & xsel: add selected or copied URL as bookmark](http://tuxdiary.com/2016/03/26/buku-xsel/)

`buku` is **GPLv3** licensed. Copyright (C) 2015 [Arun Prakash Jana](mailto:engineerarun@gmail.com).

Find `buku` useful? If you would like to donate, visit the
[![Donate Button](https://img.shields.io/badge/paypal-donate-orange.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=RMLTQ76JSXJ4Q) page.

# Features

- Add, update or remove a bookmark
- Add tags to bookmarks
- Manual password protection using AES256 encryption algorithm
- Optionally fetch page title data from the web (default: disabled)
- Add a custom page title manually
- Use (partial) tags or keywords to search bookmarks
- Any or all search keyword match options
- Search bookmarks by tag
- Unique URLs to avoid duplicates, show index if URL already exists
- Open bookmark in browser using index
- Open search results in browser
- Optional Json formatted output
- Modify or delete tags in DB
- Show all unique tags sorted alphabetically
- Browser (Chromium and Firefox based) errors and warnings suppression
- Show single bookmark by ID or all bookmarks in a go
- Refresh all bookmarks online
- Auto-compact DB on a single bookmark removal
- Delete all bookmarks from DB
- Show all bookmarks with empty titles or no tags (for bookkeeping)
- Add a bookmark at N<sup>th</sup> index, to fill deleted bookmark indices
- Secure parameterized SQLite3 queries to access database
- Supports HTTP compression
- Handle multiple HTTP redirections (reports redirected URL, loops, IP blocking)
- Unicode in URL works
- UTF-8 request and response, page character set detection
- Handle piped input
- Coloured output for clarity
- Easily create compatible batch add or update scripts
- Unformatted selective output (for creating batch update scripts)
- Manpage for quick reference
- Optional debug information
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
 - [AUR](https://aur.archlinux.org/packages/buku/) for Arch Linux;
 - Void Linux repos.

        $ sudo xbps-install -S buku
 - [Homebrew](http://braumeister.org/formula/buku) for OS X, or its Linux fork, [Linuxbrew](https://github.com/Linuxbrew/linuxbrew/blob/master/Library/Formula/buku.rb).

# Usage

## Cmdline options

    Usage: buku OPTIONS [URL] [TAGS] [KEYWORDS ...]

    A private cmdline bookmark manager. Your mini web!

    General options
      -a URL [tags]        add URL as bookmark with comma separated tags
      -d N                 delete entry at DB index N (from -p 0), move last entry to N
      -g                   list all tags alphabetically
      -m title             manually specify the title, for -a, -i, -u
      -s keyword(s)        search bookmarks for any keyword
      -S keyword(s)        search bookmarks with all keywords
      -u N URL [tags]      update all fields of entry at DB index N
      -w                   fetch title from web, for -a, -i, -u

    Power toys
      -D                   delete ALL bookmarks
      -e                   show bookmarks with empty titles or no tags
      -i N                 insert new bookmark at free DB index N
      -j                   show results in Json format
      -k                   decrypt (unlock) database file
      -l                   encrypt (lock) database file
      -o N                 open URL at DB index N in browser
      -p N                 show details of bookmark record at DB index N (0 for all)
      -r oldtag [newtag]   replace oldtag with newtag, delete oldtag if newtag empty
      -R                   refresh title from web for all bookmarks, update if non-empty
      -t N                 use N (> 0) hash iterations to generate key, for -k, -l
      -x N                 modify -p behaviour, N=1: show only URL, N=2: show URL and tag
      -z                   show debug information

    Keys
      1-N                  open Nth search result in browser
      Enter                exit buku

## Operational notes

- The SQLite3 database file is stored in `$HOME/.local/share/buku/bookmarks.db` (or `$XDG_DATA_HOME/buku/bookmarks.db`, if XDG_DATA_HOME is defined) for each user. Before version 1.9, buku stored database in `$HOME/.cache/buku/bookmarks.db`. If the file exists, buku automatically moves it to new location.
- It's  advisable  to copy URLs directly from the browser address bar, i.e., along with the leading `http://` or `https://` token. `buku` looks up title data (found within <title></title> tags of HTML) from the web ONLY for fully-formed HTTP(S) URLs.
- If the URL contains characters like `;`, `&` or brackets they may be interpreted specially by the shell. To avoid it, add the URL within single `'` or double `"` quotes.
- The same URL cannot be added twice. You can update tags and re-fetch title data. You can also insert a new bookmark at a free index.
- You can either add or update or delete record(s) in one instance. A combination of these operations is not supported in a single run.
- Search works in mysterious ways:
  - Case-insensitive.
  - Substrings match (`match` matches `rematched`) for URL, title and tags.
  - `-s` : match any of the keywords in URL, title or tags.
  - `-S` : match all the keywords in URL, title or tags.
  - You can search bookmarks by tag (see example).
  - Search results are indexed serially. This index is different from actual database index of a bookmark record which is shown within `()` after the URL.
- AES256 is used for encryption. Optionally specify (`-t`) the number of hash iterations to use to generate key. Default is 8 iterations.
- Encryption is optional and manual. If you choose to use encryption, the database file should be unlocked (`-k`) before using buku and locked (`-l`) afterwards. Between these 2 operations, the database file lies unencrypted on the disk, and NOT in memory. Also, note that the database file is <i>unencrypted on creation</i>.

# Examples
1. **Add** a new bookmark with title `Linux magazine` & tags `linux news` and `open source`:

        $ buku -a -m 'Linux magazine' http://tuxdiary.com linux news, open source
        Added at index 15012014
Note that URL must precede tags. Multiple words in title must be within quotes.
The assigned automatic index 15012014 is unique, one greater than highest index already in use in database.
2. Add a bookmark, **fetch page title** information from web:

        $ buku -a -w http://tuxdiary.com linux news, open source
        Title: [TuxDiary | Linux, open source and a pinch of leisure.]
        Added at index 15012014
3. **Update** existing bookmark at index 15012014 with a new tag:

        $ buku -u 15012014 -w http://tuxdiary.com linux news, open source, magazine
        Title: [TuxDiary | Linux, open source and a pinch of leisure.]
        Updated index 15012014
Tags are updated too. Original tags are removed.
4. Update or **refresh full DB**:

        $ buku -R
This operation does not modify the indexes, URLs or tags. Only titles, if non-empty, are refreshed.
5. **Delete** bookmark at index 15012014:

        $ buku -d 15012014
        Index 15012020 moved to 15012014
The last index is moved to the deleted index to keep the DB compact.
6. **Delete all** bookmarks:

        $ buku -D
7. List **all unique tags** alphabetically:

        $ buku -g
8. **Insert** a bookmark at index 15012014 (fails if index or URL exists in database):

        $ buku -i 15012014 -w http://tuxdiary.com/about linux news, open source
        Title: [A journey with WordPress | TuxDiary]
        Added at index 15012014
9. **Replace a tag** with new one:

        $ buku -r 'old tag' 'new tag'
10. **Delete a tag** from DB:

        $ buku -r 'old tag'
11. **Show info** on bookmark at index 15012014:

        $ buku -p 15012014
12. **Show all** bookmarks with real index from database:

        $ buku -p 0
13. **Open URL** at index 15012014 in browser:

        $ buku -o 15012014
14. **Search** bookmarks for **ANY** of the keywords `*kernel*` and `*debugging*` in URL, title or tags:

        $ buku -s kernel debugging
15. **Search** bookmarks with **ALL** the keywords `*kernel*` and `*debugging*` in URL, title or tags:

        $ buku -S kernel debugging

16. **Search** bookmarks tagged `general kernel concepts`:

        $ buku -S ',general kernel concepts,'
Note the commas (,) before and after the tag.
17. Encrypt/decrypt DB with **custom number of iterations** to generate key:

        $ buku -l -t 15
        $ buku -k -t 15
The same number of iterations must be used for one lock & unlock instance.
18. Show **debug info**:

        $ buku -z ...
19. More **help**:

        $ buku
        $ man buku

## Bookkeeping

1. To list bookmarks with **no title or tags**:

        $ buku -e
Use the `-u` option to add title or tags to those entries, if you want to.
2. `buku` doesn't have any **import feature** of its own. To import URLs in **bulk**, create a script with URLs and tags like the following (check TIP below):

        #!/bin/bash
        buku -aw https://wireless.wiki.kernel.org/ networking, device drivers
        buku -aw https://courses.engr.illinois.edu/ece390/books/artofasm/ArtofAsm.html assembly
        buku -aw http://www.tittbit.in/
        buku -aw http://www.mikroe.com/chapters/view/65/ electronics
        buku -aw "http://msdn.microsoft.com/en-us/library/bb470206(v=vs.85).aspx" file systems
        buku -aw http://www.ibm.com/developerworks/linux/library/l-linuxboot/index.html boot process
Make the script executable and run to batch add bookmarks.
3. To **update selected URLs** (refresh) along with your tags, first get the unformatted selective output with URL and tags:

        $ buku -p 0 -x 2 | tee myurls
Remove the lines you don't need. Add `buku -wu ` in front of all the other lines (check TIP below). Should look like:

        #!/bin/bash
        buku -wu 50 https://wireless.wiki.kernel.org/ networking, device drivers
        buku -wu 51 https://courses.engr.illinois.edu/ece390/books/artofasm/ArtofAsm.html assembly
        buku -wu 52 http://www.tittbit.in/
        buku -wu 53 http://www.mikroe.com/chapters/view/65/ electronics
        buku -wu 54 "http://msdn.microsoft.com/en-us/library/bb470206(v=vs.85).aspx" file systems
        buku -wu 55 http://www.ibm.com/developerworks/linux/library/l-linuxboot/index.html boot process
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

    $ sed -i 's/^/buku -wu /' filename

# Contributions
Pull requests are welcome. Some of the features I have in mind are:
- Support subcommands using argparse
- Merge bookmark database files (for users who work on multiple systems)
- Exact word match (against substring in a word as it works currently. Hint: REGEXP)
- Parse full page data??? Might end up writing a search engine like Google. ;)
- Anything else which would add value (please raise an issue for discussion)

# Developers
[Arun Prakash Jana](mailto:engineerarun@gmail.com)

Special thanks to the community for valuable suggestions and ideas.
