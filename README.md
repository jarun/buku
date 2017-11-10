<h1 align="center">Buku</h1>

<p align="center">
<a href="https://github.com/jarun/Buku/releases/latest"><img src="https://img.shields.io/github/release/jarun/buku.svg?maxAge=600" alt="Latest release" /></a>
<a href="https://aur.archlinux.org/packages/buku"><img src="https://img.shields.io/aur/version/buku.svg?maxAge=600" alt="AUR" /></a>
<a href="http://braumeister.org/formula/buku"><img src="https://img.shields.io/homebrew/v/buku.svg?maxAge=600" alt="Homebrew" /></a>
<a href="https://pypi.python.org/pypi/buku"><img src="https://img.shields.io/pypi/v/buku.svg?maxAge=600" alt="PyPI" /></a>
<a href="https://packages.debian.org/search?keywords=buku&searchon=names&exact=1"><img src="https://img.shields.io/badge/debian-9+-blue.svg?maxAge=2592000" alt="Debian Strech+" /></a>
<a href="https://packages.ubuntu.com/search?keywords=buku&searchon=names&exact=1"><img src="https://img.shields.io/badge/ubuntu-17.04+-blue.svg?maxAge=2592000" alt="Ubuntu Zesty+" /></a>
<a href="https://launchpad.net/~twodopeshaggy/+archive/ubuntu/jarun/"><img src="https://img.shields.io/badge/ubuntu-PPA-blue.svg?maxAge=2592000" alt="Ubuntu PPA" /></a>
</p>

<p align="center">
<a href="https://github.com/jarun/buku/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-GPLv3-yellow.svg?maxAge=2592000" alt="License" /></a>
<a href="http://buku.readthedocs.io/en/latest/?badge=latest"><img src="https://readthedocs.org/projects/buku/badge/?version=latest" alt="Docs Status" /></a>
<a href="https://travis-ci.org/jarun/Buku"><img src="https://travis-ci.org/jarun/Buku.svg?branch=master" alt="Build Status" /></a>
</p>

<p align="center">
<a href="https://asciinema.org/a/137065"><img src="https://s26.postimg.org/o6lka0dw9/buku_demo.png" alt="Buku in action!" width="734"/></a>
</p>

<p align="center"><i>Buku in action!</i></p>

### Introduction

`buku` is a powerful bookmark manager written in Python3 and SQLite3. When I started writing it, I couldn't find a flexible cmdline solution with a private, portable, merge-able database along with browser integration. Hence, `Buku` (after my son's nickname, meaning *close to the heart* in my language).

`buku` fetches the title of a bookmarked web page and stores it along with any additional comments and tags. You can use your favourite editor to compose and update bookmarks. With multiple search options, including regex and a deep scan mode (particularly for URLs), it can find any bookmark instantly. Multiple search results can be opened in the browser at once.

For GUI integration (or to sync bookmarks with your favourite bookmark management service), refer to the wiki page on [System integration](https://github.com/jarun/Buku/wiki/System-integration). If you prefer the terminal, thanks to the [shell completion](#shell-completion) scripts, you don't need to memorize any of the options. There's an Easter egg to revisit random forgotten bookmarks too.

We have one of the best documentation around. You can start with the [Examples](#examples). *Buku* is too busy to track you - no hidden history, obsolete records, usage analytics or homing. To learn more on how it works or to contribute to the project, please refer to the wiki page on [Operational notes](https://github.com/jarun/Buku/wiki/Operational-notes).

There are several [projects based on `buku`](#related-projects), including a browser plug-in.

PRs are welcome. Please visit [#174](https://github.com/jarun/Buku/issues/174) for a list of TODOs. Visit the [wiki](https://github.com/jarun/Buku/wiki) for guidelines.

<p align="center">
<a href="https://saythanks.io/to/jarun"><img src="https://img.shields.io/badge/say-thanks!-ff69b4.svg" /></a>
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=RMLTQ76JSXJ4Q"><img src="https://img.shields.io/badge/Donate-$5-FC746D.svg" alt="Donate via PayPal!" /></a>
</p>

### Table of Contents

- [Features](#features)
- [Installation](#installation)
  - [Dependencies](#dependencies)
  - [From a package manager](#from-a-package-manager)
  - [Release packages](#release-packages)
  - [From source](#from-source)
  - [Running standalone](#running-standalone)
- [Shell completion](#shell-completion)
- [Usage](#usage)
  - [Cmdline options](#cmdline-options)
  - [Colors](#colors)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
  - [Editor integration](#editor-integration)
- [Collaborators](#collaborators)
- [Related projects](#related-projects)
- [In the Press](#in-the-press)

### Features

- Lightweight, clean interface, custom colors
- Text editor integration
- Fetch, edit page title; add tags and notes
- Powerful search modes (regex, substring...)
- Continuous search with on the fly mode switch
- Open bookmarks and search results in browser
- Manual encryption support
- Auto-import from Firefox, Google Chrome and Chromium
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

#### From a package manager

- [AUR](https://aur.archlinux.org/packages/buku/)
- [Debian](https://packages.debian.org/search?keywords=buku&searchon=names&exact=1)
- [Homebrew](http://braumeister.org/formula/buku)
- [NixOS](https://github.com/NixOS/nixpkgs/tree/master/pkgs/applications/misc/buku) (`sudo nix-env -i buku`)
- [PyPi](https://pypi.python.org/pypi/buku/) (`sudo pip3 install buku`)
- [Ubuntu](http://packages.ubuntu.com/search?keywords=buku&searchon=names&exact=1)
- [Ubuntu PPA](https://launchpad.net/~twodopeshaggy/+archive/ubuntu/jarun/)
- [Void Linux](https://github.com/voidlinux/void-packages/tree/master/srcpkgs/buku) (`sudo xbps-install -S buku`)

#### Release packages

Packages for Arch Linux, CentOS, Fedora and Ubuntu are available with the [latest stable release](https://github.com/jarun/Buku/releases/latest).

#### From source

If you have git installed, clone this repository. Otherwise download the [latest stable release](https://github.com/jarun/Buku/releases/latest) or [development version](https://github.com/jarun/Buku/archive/master.zip) (*risky*).

Install to default location (`/usr/local`):

    $ sudo make install

To remove, run:

    $ sudo make uninstall

`PREFIX` is supported, in case you want to install to a different location.

#### Running standalone

`buku` is a standalone utility. From the containing directory, run:

    $ chmod +x buku.py
    $ ./buku.py

### Shell completion

Shell completion scripts for Bash, Fish and Zsh can be found in respective subdirectories of [auto-completion/](https://github.com/jarun/Buku/blob/master/auto-completion). Please refer to your shell's manual for installation instructions.

### Usage

#### Cmdline options

```
usage: buku [OPTIONS] [KEYWORD [KEYWORD ...]]

Powerful command-line bookmark manager.

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
                           edit last bookmark, if index=-1
                           to specify index, EDITOR must be set
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
      -t, --stag [tag [,|+] ...] [- tag, ...]
                           search bookmarks by tags
                           use ',' to find entries matching ANY tag
                           use '+' to find entries matching ALL tags
                           excludes entries with tags after ' - '
                           list all tags, if no search keywords

ENCRYPTION OPTIONS:
      -l, --lock [N]       encrypt DB in N (default 8) # iterations
      -k, --unlock [N]     decrypt DB in N (default 8) # iterations

POWER TOYS:
      --ai                 auto-import from Firefox/Chrome/Chromium
      -e, --export file    export bookmarks to Firefox format html
                           export markdown, if file ends with '.md'
                           format: [title](url), 1 entry per line
                           export buku DB, if file ends with '.db'
                           use --tag to export specific tags
      -i, --import file    import bookmarks html in Firefox format
                           import markdown, if file ends with '.md'
                           import buku DB, if file ends with '.db'
      -p, --print [...]    show record details by indices, ranges
                           print all bookmarks, if no arguments
                           -n shows the last n results (like tail)
      -f, --format N       limit fields in -p or Json search output
                           N=1: URL, N=2: URL and tag, N=3: title,
                           N=4: URL, title and tag. To omit DB index,
                           use N0, e.g., 10, 20, 30, 40.
      -j, --json           Json formatted output for -p and search
      --colors COLORS      set output colors in five-letter string
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
    t [...]                search bookmarks by tags or show taglist
                           list index after a tag listing shows records with the tag
    o id|range [...]       browse bookmarks by indices and/or ranges
    p id|range [...]       print bookmarks by indices and/or ranges
    g [taglist id|range ...] [>>|>|<<] record id|range [...]
                           append, set, remove (all or specific) tags
    w [editor|id]          edit and add or update a bookmark
    ?                      show this help
    q, ^D, double Enter    exit buku
```

#### Colors

`buku` supports custom colors. Visit the wiki page on how to [customize colors](https://github.com/jarun/Buku/wiki/Customize-colors) for more details.

### Examples

1. **Edit and add** a bookmark from editor:

       $ buku -w
       $ buku -w 'gedit -w'
       $ buku -w 'macvim -f' -a https://ddg.gg search engine, privacy
    The first command picks editor from the environment variable `EDITOR`. The second command opens gedit in blocking mode. The third command opens macvim with option -f and the URL and tags populated in template.
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
       $ buku -e bookmarks.db --tag tag 1, tag 2
    All bookmarks are exported if --tag is not specified.
10. **Import** bookmarks from HTML and markdown:

        $ buku -i bookmarks.html
        $ buku -i bookmarks.md
        $ buku -i bookmarks.db
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
19. **Search** for bookmarks matching **ANY** of the tags `kernel`, `debugging`, `general kernel concepts`:

        $ buku --stag kernel, debugging, general kernel concepts
20. **Search** for bookmarks matching **ALL** of the tags `kernel`, `debugging`, `general kernel concepts`:

        $ buku --stag kernel + debugging + general kernel concepts
21. **Search** for bookmarks matching both the tags `kernel` and `debugging`, but **excluding** bookmarks matching the tag `general kernel concepts`:

        $ buku --stag kernel + debugging - general kernel concepts
22. List **all unique tags** alphabetically:

        $ buku --stag
23. Run a **search and update** the results:

        $ buku -s kernel debugging -u --tag + linux kernel
24. Run a **search and delete** the results:

        $ buku -s kernel debugging -d
25. **Encrypt or decrypt** DB with **custom number of iterations** (15) to generate key:

        $ buku -l 15
        $ buku -k 15
    The same number of iterations must be specified for one lock & unlock instance. Default is 8, if omitted.
26. **Show details** of bookmarks at index 15012014 and ranges 20-30, 40-50:

        $ buku -p 20-30 15012014 40-50
27. Show details of the **last 10 bookmarks**:

        $ buku -p -10
28. **Show all** bookmarks with real index from database:

        $ buku -p
        $ buku -p | more
29. **Replace tag** 'old tag' with 'new tag':

        $ buku --replace 'old tag' 'new tag'
30. **Delete tag** 'old tag' from DB:

        $ buku --replace 'old tag'
31. **Append (or delete) tags** 'tag 1', 'tag 2' to (or from) existing tags of bookmark at index 15012014:

        $ buku -u 15012014 --tag + tag 1, tag 2
        $ buku -u 15012014 --tag - tag 1, tag 2
32. **Open URL** at index 15012014 in browser:

        $ buku -o 15012014
33. List bookmarks with **no title or tags** for bookkeeping:

        $ buku -S blank
34. List bookmarks with **immutable title**:

        $ buku -S immutable
35. **Shorten URL** www.google.com and the URL at index 20:

        $ buku --shorten www.google.com
        $ buku --shorten 20
36. **Append, remove tags at prompt** (taglist index to the left, bookmark index to the right):

        // append tags at taglist indices 4 and 6-9 to existing tags in bookmarks at indices 5 and 2-3
        buku (? for help) g 4 9-6 >> 5 3-2
        // set tags at taglist indices 4 and 6-9 as tags in bookmarks at indices 5 and 2-3
        buku (? for help) g 4 9-6 > 5 3-2
        // remove all tags from bookmarks at indices 5 and 2-3
        buku (? for help) g > 5 3-2
        // remove tags at taglist indices 4 and 6-9 from tags in bookmarks at indices 5 and 2-3
        buku (? for help) g 4 9-6 << 5 3-2
37. List bookmarks with **colored output**:

        $ buku --colors oKlxm -p
38. More **help**:

        $ buku -h
        $ man buku

### Troubleshooting

#### Editor integration

You may encounter issues with GUI editors which maintain only one instance by default and return immediately from other instances. Use the appropriate editor option to block the caller when a new document is opened. See issue [#210](https://github.com/jarun/Buku/issues/210) for gedit.

### Collaborators

- [Arun Prakash Jana](https://github.com/jarun)
- [Rachmadani Haryono](https://github.com/rachmadaniHaryono)
- [Johnathan Jenkins](https://github.com/shaggytwodope)
- [SZ Lin](https://github.com/szlin)
- [Alex Gontar](https://github.com/mosegontar)

Copyright © 2015-2017 [Arun Prakash Jana](mailto:engineerarun@gmail.com)
<br>
<p><a href="https://gitter.im/jarun/Buku"><img src="https://img.shields.io/gitter/room/jarun/buku.svg?maxAge=2592000" alt="gitter chat" /></a></p>

### Related projects

- [bukubrow](https://github.com/SamHH/bukubrow), WebExtension for browser integration
- [oil](https://github.com/AndreiUlmeyda/oil), search-as-you-type cli frontend
- [buku_run](https://github.com/carnager/buku_run), rofi frontend
- [pinku](https://github.com/mosegontar/pinku), A Pinboard-to-Buku importation utility

<a href="http://buku.readthedocs.io/en/stable/?badge=stable"><img src="https://img.shields.io/badge/docs-stable-brightgreen.svg?maxAge=2592000" alt="Stable Docs" /></a>

### In the Press

- [2daygeek](http://www.2daygeek.com/buku-command-line-bookmark-manager-linux/)
- [It's F.O.S.S.](https://itsfoss.com/buku-command-line-bookmark-manager-linux/)
- [LinOxide](https://linoxide.com/linux-how-to/buku-browser-bookmarks-linux/)
- [LinuxUser Magazine 01/2017 Issue](http://www.linux-community.de/LU/2017/01/Das-Beste-aus-zwei-Welten)
- [Make Tech Easier](https://www.maketecheasier.com/manage-browser-bookmarks-ubuntu-command-line/)
- [One Thing Well](http://onethingwell.org/post/144952807044/buku)
- [ulno.net](https://ulno.net/blog/2017-07-19/of-bookmarks-tags-and-browsers/)
