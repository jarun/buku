# Buku

![Screenshot](http://i.imgur.com/NIQlgDC.png)

`buku` (formerly `markit`) is a cmdline bookmark management utility written in Python3 and SQLite3. `buku` exists because of my monumental dependency on <a href="http://historio.us/">historious</a>. I wanted the same database on my local system. However, I couldn't find an equally flexible cmdline solution. Hence, `Buku` (after my son's nickname).

You can add bookmarks to `buku` with title and tags, optionally fetch page title from web, search by keywords for matching tags or title or URL, update and remove bookmarks. You can open the URLs from search results directly in the browser. You can encrypt or decrypt the database file manually, optionally with custom number of hash passes for key generation.  

The SQLite3 database file is stored in `$HOME/.cache/buku/bookmarks.db` for each user.  

`buku` is **GPLv3** licensed. Copyright (C) 2015 [Arun Prakash Jana](mailto:engineerarun@gmail.com).

If you find `buku` useful, please consider donating via PayPal.
[![Donate Button](https://www.paypal.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=RMLTQ76JSXJ4Q)

# Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [Installating from source](#installing-from-source)
  - [Running as a standalone utility](#running-as-a-standalone-utility)
  - [Installing with a package manager](#installing-with-a-package-manager)
- [Usage](#usage)
  - [Operational notes](#operational-notes)
  - [cmdline help](#cmdline-help)
- [Examples](#examples)
- [Contributions](#contributions)
- [Developers](#developers)

# Features
- Add, update or remove a bookmark
- Add tags to bookmarks
- Manual password protection using AES256 encryption algorithm
- Optionally fetch page title data from the web (default: disabled)
- Add or update page title offline manually
- Use (partial) tags or keywords to search bookmarks
- Any or all search keyword match options
- Unique URLs to avoid duplicates, show index if URL already exists
- Open bookmark in browser using index
- Open search results in browser
- Browser (Chromium and Firefox based) errors and warnings suppression
- Show single bookmark by ID or all bookmarks in a go
- Refresh all bookmarks online
- Delete all bookmarks
- Add a bookmark at N<sup>th</sup> index, to fill deleted bookmark indices
- Secure parameterized SQLite3 queries to access database
- Handle first level of redirections (reports IP blocking)
- Unicode in URL works
- UTF-8 request and response, page character set detection
- Works with Python 3.x
- Coloured output for clarity
- Easily create compatible batch add or update scripts
- Unformatted selective output (for creating batch update scripts)
- Manpage for quick reference
- Optional debug information
- Fast and clean (no ads or clutter)
- Minimal dependencies
- Open source and free

# Installation

## Dependencies
`buku` requires Python 3.x to work.

For optional encryption support, install PyCrypto module. Run:

    $ sudo pip3 install pycrypto
or on Ubuntu:

    $ sudo apt-get install python3-crypto
## Installing from source
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
 - Void Linux repos. Run: `$ sudo xbps-install -S buku`

# Usage
## Operational notes
- It's  advisable  to copy URLs directly from the browser address bar, i.e., along with the leading `http://` or `https://` token. `buku` looks up title data (found within <title></title> tags of HTML) from the web ONLY for fully-formed HTTP(S) URLs.
- If the URL contains characters like `;`, `&` or brackets they may be interpreted specially by the shell. To avoid it, add the URL within single `'` or double `"` quotes.
- The same URL cannot be added twice. You can update tags and re-fetch title data. You can also delete it and insert at the same index. 
- You can either add or update or delete record(s) in one instance. A combination of these operations is not supported in a single run.
- Search works in mysterious ways:
  - Substrings match (`match` matches `rematched`) for URL, tags and title.
  - All the keywords are treated together as a `single` tag in the `same order`. Bookmarks with partial or complete tag matches are shown in results.
  - `-s` : match any of the keywords in URL or title. Order is irrelevant.
  - `-S` : match all the keywords in URL or title. Order is irrelevant.
  - Search results are indexed serially. This index is different from actual database index of a bookmark reord which is shown within `()` after the URL.
- Encryption support is manual. Database file should be unlocked (`-k`) before using buku and locked (`-l`) afterwards. Note that the database file is <i>unecrypted on creation</i>. AES256 is used for encryption. Optionally specify (`-t`) the number of hash iterations to use to generate key. Default is 8 iterations.

## cmdline help

    Usage: buku [OPTIONS] KEYWORDS...
    Bookmark manager. Your private Google.

    Options
      -a URL tag 1, tag 2, ...   add URL as bookmark with comma separated tags
      -d N                       delete entry at DB index N (from -P output)
      -D                         delete ALL bookmarks
      -i N                       insert entry at DB index N, useful to fill deleted index
      -k                         decrypt (unlock) database file
      -l                         encrypt (lock) database file
      -m                         manually add or update the title offline
      -o N                       open URL at DB index N in browser
      -p N                       show details of bookmark record at DB index N
      -P                         show all bookmarks along with index from DB
      -R                         refresh all bookmarks, tags retained
      -s keyword(s)              search all bookmarks for a (partial) tag or any keyword
      -S keyword(s)              search all bookmarks for a (partial) tag or all keywords
      -t N                       use N (> 0) hash iterations to generate key, works with -k, -l
      -u N                       update entry at DB index N
      -w                         fetch title info from web, works with -a, -i, -u
      -x N                       works with -P, N=1: show only URL, N=2: show URL and tag
      -z                         show debug information
                                 any other option shows help and exits buku

    Keys
      1-N                        open Nth search result in browser. Enter exits buku.

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
        Updated
4. Update or **refresh full DB**:

        $ buku -R
5. **Delete** bookmark at index 15012014:

        $ buku -d 15012014
6. **Delete all** bookmarks:

        $ buku -D
7. **Insert** a bookmark at index 15012014 (fails if index or URL exists in database):

        $ buku -i 15012014 -w http://tuxdiary.com/about linux news, open source
        Title: [A journey with WordPress | TuxDiary]
        Added at index 15012014
This option is useful in filling deleted indices from database manually.
8. **Show info** on bookmark at index 15012014:

        $ buku -p 15012014
9. **Show all** bookmarks with real index from database:

        $ buku -P
10. **Open URL** at index 15012014 in browser:

        $ buku -o 15012014
11. **Search** bookmarks for a tag matching `*kernel debugging*` or any of the keywords `*kernel*` and `*debugging*` in URL or title (separately):

        $ buku -s kernel debugging
12. **Search** bookmarks for a tag matching `*kernel debugging*` or all the keywords `*kernel*` and `*debugging*` in URL or title (separately):

        $ buku -S kernel debugging

13. Encrypt/decrypt DB with **custom number of iterations** to generate key:

        $ buku -l -t 15
        $ buku -k -t 15
The same number of iterations must be used for one lock & unlock instance.
14. Show **debug info**:

        $ buku -z ...
15. Show **help**:

        $ buku
16. Check **manpage**:

        $ man buku
17. `buku` doesn't have any **import feature** of its own. To import URLs in bulk, create a script with URLs and tags like the following (check TIP below):

        #!/bin/bash
        buku -aw https://wireless.wiki.kernel.org/ networking, device drivers
        buku -aw https://courses.engr.illinois.edu/ece390/books/artofasm/ArtofAsm.html assembly
        buku -aw http://www.tittbit.in/
        buku -aw http://www.mikroe.com/chapters/view/65/ electronics
        buku -aw "http://msdn.microsoft.com/en-us/library/bb470206(v=vs.85).aspx" file systems
        buku -aw http://www.ibm.com/developerworks/linux/library/l-linuxboot/index.html boot process
Make the script executable and run to batch add bookmarks.
18. To **update selected URLs** (refresh) along with your tags, first get the unformatted selective output with URL and tags:

        $ buku -P -x 2 | tee myurls
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

**TIP:**  
To add the same text at the beginning of multiple lines using vim editor:  
  - Press `Ctrl-v` to select the first column of text in the lines you want to change (visual mode).
  - Press `Shift-i` and type the text you want to insert.
  - Hit `Esc`, wait 1 second and the inserted text will appear on every line.

Using sed:

    $ sed -i 's/^/buku -wu /' filename

# Contributions
I would love to see pull requests with the following features:
- Exact word match (against substring in a word as it works currently. Hint: REGEXP)
- Parse full page data??? Might end up writing a search engine like Google. ;)

# Developers
[Arun Prakash Jana](mailto:engineerarun@gmail.com)

Special thanks to the community for valuable suggestions and ideas.
