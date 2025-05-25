<h1 align="center">buku</h1>

<p align="center">
<a href="https://github.com/jarun/buku/releases/latest"><img src="https://img.shields.io/github/release/jarun/buku.svg?maxAge=600" alt="Latest release" /></a>
<a href="https://repology.org/project/buku/versions"><img src="https://repology.org/badge/tiny-repos/buku.svg?header=repos" alt="Availability"></a>
<a href="https://pypi.org/project/buku/"><img src="https://img.shields.io/pypi/v/buku.svg?maxAge=600" alt="PyPI" /></a>
<a href="https://circleci.com/gh/jarun/workflows/buku"><img src="https://img.shields.io/circleci/project/github/jarun/buku.svg" alt="Build Status" /></a>
<a href="https://buku.readthedocs.io/en/latest/?badge=latest"><img src="https://readthedocs.org/projects/buku/badge/?version=latest" alt="Docs Status" /></a>
<a href="https://en.wikipedia.org/wiki/Privacy-invasive_software"><img src="https://img.shields.io/badge/privacy-✓-crimson" alt="Privacy Awareness" /></a>
<a href="https://github.com/jarun/buku/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-GPLv3-yellowgreen.svg?maxAge=2592000" alt="License" /></a>
</p>

<p align="center">
<a href="https://asciinema.org/a/137065"><img src="https://asciinema.org/a/137065.svg" alt="buku in action!" width="734"/></a>
</p>

<p align="center"><i>buku in action!</i></p>

### Introduction

`buku` is a powerful bookmark manager and a personal textual mini-web.

For those who prefer the GUI, `bukuserver` exposes a browsable front-end on a local web host server. See [bukuserver page](https://github.com/jarun/buku/tree/master/bukuserver#readme) for config and screenshots.

When I started writing it, I couldn't find a flexible command-line solution with a private, portable, merge-able database along with seamless GUI integration. Hence, `buku`.

`buku` can import bookmarks from browser(s) or fetch the title, tags and description of a URL from the web. Use your favourite editor to add, compose and update bookmarks. Search bookmarks instantly with multiple search options, including regex and a deep scan mode (handy with URLs).

It can look up broken links on the Wayback Machine. There's an Easter Egg to revisit random bookmarks.

There's no tracking, hidden history, obsolete records, usage analytics or homing.

To get started right away, jump to the [Quickstart](#quickstart) section. `buku` has one of the best documentation around. The man page comes with examples. For internal details, please refer to the [operational notes](https://github.com/jarun/buku/wiki/Operational-notes).

`buku` is a library too! There are several related projects, including a browser plug-in.

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
  - [Command-line options](#command-line-options)
  - [Colors](#colors)
- [Quickstart](#quickstart)
- [Examples](#examples)
- [Automation](#automation)
- [Troubleshooting](#troubleshooting)
  - [Editor integration](#editor-integration)
- [Collaborators](#collaborators)
- [Contributions](#contributions)
- [Related projects](#related-projects)
- [In the Press](#in-the-press)

### Features

- Store bookmarks with auto-fetched title, tags and description
- Auto-import from Firefox, Google Chrome, Chromium and MS Edge
- Open bookmarks and search results in browser
- Browse cached page from the Wayback Machine
- Text editor integration
- Lightweight, clean interface, custom colors
- Powerful search options (regex, substring...)
- Continuous search with on the fly mode switch
- Portable, merge-able database to sync between systems
- Import/export bookmarks from/to HTML, XBEL, Markdown, RSS/Atom or Orgfile
- Smart tag management using redirection (>>, >, <<)
- Multi-threaded full DB refresh
- Manual encryption support
- Shell completion scripts, man page with handy examples
- Privacy-aware (no unconfirmed user data collection)
- Can be used as a Python library ([_API documentation_](https://buku.readthedocs.io/en/latest/?badge=latest))
- Has a compation Web-application ([Bukuserver](https://github.com/jarun/buku/wiki/Bukuserver-%28WebUI%29)) with an HTTP-based API (for personal use only)

### Installation

#### Dependencies

| Feature | Dependency |
| --- | --- |
| Lang, SQLite | Python 3.8+ |
| HTTPS | certifi, urllib3 |
| Encryption | cryptography |
| HTML | beautifulsoup4, html5lib |

To copy URL to clipboard `buku` uses `xsel` (or `xclip`) on Linux, `pbcopy` (default installed) on OS X, `clip` (default installed) on Windows, `termux-clipboard` on Termux (terminal emulation for Android), `wl-copy` on Wayland. If X11 is missing, GNU Screen or tmux copy-paste buffers are recognized.

#### From a package manager

To install buku with all its dependencies from PyPI, run:

    # pip3 install buku

You can also install `buku` from your package manager. If the version available is dated try an alternative installation method.

<details><summary>Packaging status (expand)</summary>
<p>
<br>
<a href="https://repology.org/project/buku/versions"><img src="https://repology.org/badge/vertical-allrepos/buku.svg" alt="Packaging status"></a>
</p>
Unlisted packagers:
<p>
<br>
● <a href="https://pypi.org/project/buku/">PyPI</a> (<code>pip3 install buku</code>)<br>
● Termux (<code>pip3 install buku</code>)<br>
</p>
</details>

#### Release packages

Auto-generated packages (with only the cli component) for Arch Linux, CentOS, Debian, Fedora, openSUSE Leap and Ubuntu are available with the [latest stable release](https://github.com/jarun/buku/releases/latest).

NOTE: CentOS may not have the python3-beautifulsoup4 package in the repos. Install it using pip3.

#### From source

If you have git installed, clone this repository. Otherwise download the [latest stable release](https://github.com/jarun/buku/releases/latest) or [development version](https://github.com/jarun/buku/archive/master.zip) (*risky*).

Install the dependencies. For example, on Ubuntu:

    $ apt-get install ca-certificates python3-urllib3 python3-cryptography python3-bs4

Install the cli component to default location (`/usr/local`):

    $ sudo make install

To remove, run:

    $ sudo make uninstall

`PREFIX` is supported, in case you want to install to a different location.

#### Running standalone

`buku` is a standalone utility. From the containing directory, run:

    $ chmod +x buku
    $ ./buku

### Shell completion

Shell completion scripts for Bash, Fish and Zsh can be found in respective subdirectories of [auto-completion/](https://github.com/jarun/buku/blob/master/auto-completion). Please refer to your shell's manual for installation instructions.

### Usage

#### Command-line options

```
usage: buku [OPTIONS] [KEYWORD [KEYWORD ...]]

Bookmark manager like a text-based mini-web.

POSITIONAL ARGUMENTS:
      KEYWORD              search keywords

GENERAL OPTIONS:
      -a, --add URL [+|-] [tag, ...]
                           bookmark URL with comma-separated tags
                           (prepend tags with '+' or '-' to use fetched tags)
      -u, --update [...]   update fields of an existing bookmark
                           accepts indices and ranges
                           refresh title and desc if no edit options
                           if no arguments:
                           - update results when used with search
                           - otherwise refresh all titles and desc
      -w, --write [editor|index]
                           edit and add a new bookmark in editor
                           else, edit bookmark at index in EDITOR
                           edit last bookmark, if index=-1
                           if no args, edit new bookmark in EDITOR
      -d, --delete [...]   remove bookmarks from DB
                           accepts indices or a single range
                           if no arguments:
                           - delete results when used with search
                           - otherwise delete all bookmarks
      --retain-order       prevents reordering after deleting a bookmark
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
      --immutable N        disable web-fetch during auto-refresh
                           N=0: mutable (default), N=1: immutable
      --swap N M           swap two records at specified indices

SEARCH OPTIONS:
      -s, --sany [...]     find records with ANY matching keyword
                           this is the default search option
      -S, --sall [...]     find records matching ALL the keywords
                           special keywords -
                           "blank": entries with empty title/tag
                           "immutable": entries with locked title
      --deep               match substrings ('pen' matches 'opens')
      --markers            search for keywords in specific fields
                           based on (optional) prefix markers:
                           '.' - title, '>' - description, ':' - URL,
                           '#' - tags (comma-separated, PARTIAL matches)
                           '#,' - tags (comma-separated, EXACT matches)
                           '*' - any field (same as no prefix)
      -r, --sreg expr      run a regex search
      -t, --stag [tag [,|+] ...] [- tag, ...]
                           search bookmarks by tags
                           use ',' to find entries matching ANY tag
                           use '+' to find entries matching ALL tags
                           excludes entries with tags after ' - '
                           list all tags, if no search keywords
      -x, --exclude [...]  omit records matching specified keywords
      --random [N]         output random bookmarks out of the selection (default 1)
      --order fields [...] comma-separated list of fields to order the output by
                           (prepend with '+'/'-' to choose sort direction)

ENCRYPTION OPTIONS:
      -l, --lock [N]       encrypt DB in N (default 8) # iterations
      -k, --unlock [N]     decrypt DB in N (default 8) # iterations

POWER TOYS:
      --ai                 auto-import bookmarks from web browsers
                           Firefox, Chrome, Chromium, Vivaldi, Edge
      -e, --export file    export bookmarks to Firefox format HTML
                           export XBEL, if file ends with '.xbel'
                           export Markdown, if file ends with '.md'
                           format: [title](url) <!-- TAGS -->
                           export Orgfile, if file ends with '.org'
                           format: *[[url][title]] :tags:
                           export rss feed if file ends with '.rss'/'.atom'
                           export buku DB, if file ends with '.db'
                           combines with search results, if opted
      -i, --import file    import bookmarks from file
                           supports .html .xbel .json .md .org .rss .atom .db
      -p, --print [...]    show record details by indices, ranges
                           print all bookmarks, if no arguments
                           -n shows the last n results (like tail)
      -f, --format N       limit fields in -p or JSON search output
                           N=1: URL; N=2: URL, tag; N=3: title;
                           N=4: URL, title, tag; N=5: title, tag;
                           N0 (10, 20, 30, 40, 50) omits DB index
      -j, --json [file]    JSON formatted output for -p and search.
                           prints to stdout if argument missing.
                           otherwise writes to given file
      --colors COLORS      set output colors in five-letter string
      --nc                 disable color output
      -n, --count N        show N results per page (default 10)
      --np                 do not show the subprompt, run and exit
      -o, --open [...]     browse bookmarks by indices and ranges
                           open a random bookmark, if no arguments
      --oa                 browse all search results immediately
      --replace old new    replace old tag with new tag everywhere
                           delete old tag, if new tag not specified
      --url-redirect       when fetching an URL, use the resulting
                           URL from following *permanent* redirects
                           (when combined with --export, the old URL
                           is included as additional metadata)
      --tag-redirect [tag] when fetching an URL that causes permanent
                           redirect, add a tag in specified pattern
                           (using 'http:{}' if not specified)
      --tag-error [tag]    when fetching an URL that causes an HTTP
                           error, add a tag in specified pattern
                           (using 'http:{}' if not specified)
      --del-error [...]    when fetching an URL causes any (given)
                           HTTP error, delete/do not add it
      --export-on [...]    export records affected by the above
                           options, including removed info
                           (requires --update and --export; specific
                           HTTP response filter can be provided)
      --cached index|URL   browse a cached page from Wayback Machine
      --offline            add a bookmark without connecting to web
      --suggest            show similar tags when adding bookmarks
      --tacit              reduce verbosity, skip some confirmations
      --nostdin            do not wait for input (must be first arg)
      --threads N          max network connections in full refresh
                           default N=4, min N=1, max N=10
      -V                   check latest upstream version available
      -g, --debug          show debug information and verbose logs

SYMBOLS:
      >                    url
      +                    comment
      #                    tags

PROMPT KEYS:
    1-N                    browse search result indices and/or ranges
    R [N]                  print out N random search results
                           (or random bookmarks if negative or N/A)
    ^ id1 id2              swap two records at specified indices
    O [id|range [...]]     open search results/indices in GUI browser
                           toggle try GUI browser if no arguments
    a                      open all results in browser
    s keyword [...]        search for records with ANY keyword
    S keyword [...]        search for records with ALL keywords
    d                      match substrings ('pen' matches 'opened')
    m                      search with markers - search string is split
                           into keywords by prefix markers, which determine
                           what field the keywords is searched in:
                           '.', '>' or ':' - title, description or URL
                           '#'/'#,' - tags (comma-separated, partial/full match)
                           '*' - all fields (can be omitted in the 1st keyword)
                           note: tag marker is not affected by 'd' (deep search)
    v fields               change sorting order (default is '+index')
                           multiple comma/space separated fields can be specified
    r expression           run a regex search
    t [tag, ...]           search by tags; show taglist, if no args
    g taglist id|range [...] [>>|>|<<] [record id|range ...]
                           append, set, remove (all or specific) tags
                           search by taglist id(s) if records are omitted
    n                      show next page of search results
    N                      show previous page of search results
    o id|range [...]       browse bookmarks by indices and/or ranges
    p id|range [...]       print bookmarks by indices and/or ranges
    w [editor|id]          edit and add or update a bookmark
    c id                   copy URL at search result index to clipboard
    DB [name]              check existing DB list or switch to another DB
                           (use full/dir path to switch folders)
                           '~.' can be used as shortcut for default DB
    ?                      show this help
    q, ^D, double Enter    exit buku
```

#### Colors

`buku` supports custom colors. Visit the wiki page on how to [customize colors](https://github.com/jarun/buku/wiki/Customize-colors) for more details.

### Quickstart

1. Export `VISUAL` or `EDITOR` to point to your favourite editor. Note that `VISUAL` takes precedence over `EDITOR`.
2. Create a sweeter shortcut with some convenience.

       alias b='buku --suggest'
3. Auto-import bookmarks from your browser(s). Please quit the relevant browsers beforehand to ensure the databases are not locked.

       b --ai
4. Manually add a bookmark (for hands-on).

       b -w
5. List your bookmarks with DB index.

       b -p
6. For GUI and browser integration (or to sync bookmarks with your favourite bookmark management service) refer to the wiki page on [System integration](https://github.com/jarun/buku/wiki/System-integration).
7. Quick (bash/zsh) commands to fuzzy search with fzf and open the selection in Firefox:

       firefox $(buku -p -f 10 | fzf)
       firefox $(buku -p -f 40 | fzf | cut -f1)

   POSIX script to show a preview of the bookmark as well:

   ```sh
   #!/usr/bin/env sh

   url=$(buku -p -f4 | fzf -m --reverse --preview "buku -p {1}" --preview-window=wrap | cut -f2)

   if [ -n "$url" ]; then
       echo "$url" | xargs firefox
   fi
   ```

### Examples

1. **Edit and add** a bookmark from editor:

       $ buku -w
       $ buku -w 'gedit -w'
       $ buku -w 'macvim -f' -a https://ddg.gg search engine, privacy
    The first command picks editor from the environment variable `EDITOR`. The second command opens gedit in blocking mode. The third command opens macvim with option -f and the URL and tags populated in template.
2. **Add** a simple bookmark:

       $ buku --nostdin -a https://github.com/
       2648. GitHub: Let’s build from here · GitHub
       > https://github.com/
       + GitHub is where over 94 million developers shape the future of software, together. Contribute to the open source community, manage your Git repositories, review code like a pro, track bugs
        and features, power your CI/CD and DevOps workflows, and secure code before you commit it.

       $ buku --nostdin -a https://github.com/
       [ERROR] URL [https://github.com/] already exists at index 2648

      `>`: URL, `+`: comment, `#`: tags

      Title, description and tags will be fetched from site. Buku only stores unique URLs and will raise error if the URL already present in the database:
3. **Add** a bookmark with **tags** `search engine` and `privacy`, **comment** `Search engine with perks`, **fetch page title** from the web:

       $ buku -a https://ddg.gg search engine, privacy -c Search engine with perks
       336. DuckDuckGo
       > https://ddg.gg
       + Alternative search engine with perks
       # privacy,search engine
    where, `>`: URL, `+`: comment, `#`: tags
4. **Add** a bookmark with tags `search engine` & `privacy` and **immutable custom title** `DDG`:

       $ buku -a https://ddg.gg search engine, privacy --title 'DDG' --immutable 1
       336. DDG (L)
       > https://ddg.gg
       # privacy,search engine
    Note that URL must precede tags.
5. **Add** a bookmark **without a title** (works for update too):

       $ buku -a https://ddg.gg search engine, privacy --title
6. **Edit and update** a bookmark from editor:

       $ buku -w 15012014
    This will open the existing bookmark's details in the editor for modifications. Environment variable `EDITOR` must be set.
7. **Update** existing bookmark at index 15012014 with new URL, tags and comments, fetch title from the web:

       $ buku -u 15012014 --url http://ddg.gg/ --tag web search, utilities -c Private search engine
8. **Fetch and update only title** for bookmark at 15012014:

       $ buku -u 15012014
9. **Update only comment** for bookmark at 15012014:

       $ buku -u 15012014 -c this is a new comment
    Applies to --url, --title and --tag too.
10. **Export** bookmarks tagged `tag 1` or `tag 2` to HTML, XBEL, Markdown, Orgfile or a new database:

       $ buku -e bookmarks.html --stag tag 1, tag 2
       $ buku -e bookmarks.xbel --stag tag 1, tag 2
       $ buku -e bookmarks.md --stag tag 1, tag 2
       $ buku -e bookmarks.org --stag tag 1, tag 2
       $ buku -e bookmarks.db --stag tag 1, tag 2
    All bookmarks are exported if search is not opted.
11. **Import** bookmarks from HTML, XBEL, Markdown or Orgfile:

        $ buku -i bookmarks.html
        $ buku -i bookmarks.xbel
        $ buku -i bookmarks.md
        $ buku -i bookmarks.org
        $ buku -i bookmarks.db
12. **Delete only comment** for bookmark at 15012014:

        $ buku -u 15012014 -c
    Applies to --title and --tag too. URL cannot be deleted without deleting the bookmark.
13. **Update** or refresh **full DB** with page titles from the web:

        $ buku -u
        $ buku -u --tacit (show only failures and exceptions)
    This operation can update the title or description fields of non-immutable bookmarks by parsing the fetched page. Fields are updated only if the fetched fields are non-empty. Tags remain untouched.
14. **Delete** bookmark at index 15012014:

        $ buku -d 15012014
        Index 15012020 moved to 15012014
    The last index is moved to the deleted index to keep the DB compact. Add `--tacit` to delete without confirmation.
15. **Delete all** bookmarks:

        $ buku -d
16. **Delete** a **range or list** of bookmarks:

        $ buku -d 100-200
        $ buku -d 100 15 200
17. **Search** bookmarks for **ANY** of the keywords `kernel` and `debugging` in URL, title or tags:

        $ buku kernel debugging
        $ buku -s kernel debugging
18. **Search** bookmarks with **ALL** the keywords `kernel` and `debugging` in URL, title or tags:

        $ buku -S kernel debugging
19. **Search** bookmarks **tagged** `general kernel concepts`:

        $ buku --stag general kernel concepts
20. **Search** for bookmarks matching **ANY** of the tags `kernel`, `debugging`, `general kernel concepts`:

        $ buku --stag kernel, debugging, general kernel concepts
21. **Search** for bookmarks matching **ALL** of the tags `kernel`, `debugging`, `general kernel concepts`:

        $ buku --stag kernel + debugging + general kernel concepts
22. **Search** for bookmarks matching any of the keywords `hello` or `world`, excluding the keywords `real` and `life`, matching both the tags `kernel` and `debugging`, but **excluding** the tags `general kernel concepts` and `books`:

        $ buku hello world --exclude real life --stag 'kernel + debugging - general kernel concepts, books'
23. **Search** for bookmarks with different tokens for each field, and print them out sorted by the tags (ascending) and URL (descending)

        $ buku --order +tags,-url --markers --sall 'global substring' '.title substring' ':url substring' :https '> description substring' '#partial,tags:' '#,exact,tags' '*another global substring'
24. List **all unique tags** alphabetically:

        $ buku --stag
25. Run a **search and update** the results:

        $ buku -s kernel debugging -u --tag + linux kernel
26. Run a **search and delete** the results:

        $ buku -s kernel debugging -d
27. **Encrypt or decrypt** DB with **custom number of iterations** (15) to generate key:

        $ buku -l 15
        $ buku -k 15
    The same number of iterations must be specified for one lock & unlock instance. Default is 8, if omitted.
28. **Show details** of bookmarks at index 15012014 and ranges 20-30, 40-50:

        $ buku -p 20-30 15012014 40-50
29. Show details of the **last 10 bookmarks**:

        $ buku -p -10
30. **Show all** bookmarks with real index from database:

        $ buku -p
        $ buku -p | more
31. **Replace tag** 'old tag' with 'new tag':

        $ buku --replace 'old tag' 'new tag'
32. **Delete tag** 'old tag' from DB:

        $ buku --replace 'old tag'
33. **Append (or delete) tags** 'tag 1', 'tag 2' to (or from) existing tags of bookmark at index 15012014:

        $ buku -u 15012014 --tag + tag 1, tag 2
        $ buku -u 15012014 --tag - tag 1, tag 2
34. **Open URL** at index 15012014 in browser:

        $ buku -o 15012014
35. List bookmarks with **no title or tags** for bookkeeping:

        $ buku -S blank
36. List bookmarks with **immutable title**:

        $ buku -S immutable
37. **Append, remove tags at prompt** (taglist index to the left, bookmark index to the right):

        // append tags at taglist indices 4 and 6-9 to existing tags in bookmarks at indices 5 and 2-3
        buku (? for help) g 4 9-6 >> 5 3-2
        // set tags at taglist indices 4 and 6-9 as tags in bookmarks at indices 5 and 2-3
        buku (? for help) g 4 9-6 > 5 3-2
        // remove all tags from bookmarks at indices 5 and 2-3
        buku (? for help) g > 5 3-2
        // remove tags at taglist indices 4 and 6-9 from tags in bookmarks at indices 5 and 2-3
        buku (? for help) g 4 9-6 << 5 3-2
38. List bookmarks with **colored output**:

        $ buku --colors oKlxm -p
39. Add a bookmark after following all permanent redirects, but only if the server doesn't respond with an error (and there's no network failure)

        $ buku --add http://wikipedia.net --url-redirect --del-error
        2. Wikipedia
           > https://www.wikipedia.org/
           + Wikipedia is a free online encyclopedia, created and edited by volunteers around the world and hosted by the Wikimedia Foundation.
40. Add a bookmark with tag `http redirect` if the server responds with a permanent redirect, or tag shaped like `http 404` on an error response:

        $ buku --add http://wikipedia.net/notfound --tag-redirect 'http redirect' --tag-error 'http {}'
        [ERROR] [404] Not Found
        3. Not Found
           > http://wikipedia.net/notfound
           # http 404,http redirect
41. Update all bookmarks matching the search by updating the URL if the server responds with a permanent redirect, deleting the bookmark if the server responds with HTTP error 400, 401, 402, 403, 404 or 500, or adding a tag shaped like `http:{}` in case of any other HTTP error; then export those affected by such changes into an HTML file, marking deleted records as well as old URLs for those replaced by redirect.

        $ buku -S ://wikipedia.net -u --url-redirect --tag-error --del-error 400-404,500 --export-on --export backup.html

42. Print out a single **random** bookmark:

        $ buku --random --print

43. Print out 3 **random** bookmarks **ordered** by netloc (reversed), title and url:

        $ buku --random 3 --order ,-netloc,title,+url --print

44. Print out a single **random** bookmark matching **search** criteria, and **export** into a Markdown file (in DB order):

        $ buku --random -S kernel debugging --export random.md

45. Swap positions of records #4 and #5:

        $ buku --swap 4 5

46. More **help**:

        $ buku -h
        $ man buku

### Automation

Interactive workflows can be automated using expect. Issue [#368](https://github.com/jarun/buku/issues/368) has a working example on automating auto-import.

### Troubleshooting

#### Editor integration

You may encounter issues with GUI editors which maintain only one instance by default and return immediately from other instances. Use the appropriate editor option to block the caller when a new document is opened. See issue [#210](https://github.com/jarun/buku/issues/210) for gedit.

### Collaborators

- [Arun Prakash Jana](https://github.com/jarun)
- [Alexey Gulenko](https://github.com/LeXofLeviafan)
- [Rachmadani Haryono](https://github.com/rachmadaniHaryono)
- [Johnathan Jenkins](https://github.com/shaggytwodope)
- [SZ Lin](https://github.com/szlin)

Copyright © 2015-2025 [Arun Prakash Jana](mailto:engineerarun@gmail.com)
<br>
<p><a href="https://gitter.im/jarun/buku"><img src="https://img.shields.io/gitter/room/jarun/buku.svg?maxAge=2592000" alt="gitter chat" /></a></p>

### Contributions

Missing a feature? There's a rolling [ToDo List](https://github.com/jarun/buku/issues/484) with identified tasks. Contributions are welcome! Please follow the [PR guidelines](https://github.com/jarun/buku/wiki/PR-guidelines).

See also our documentation here <a href="http://buku.readthedocs.io/en/stable/?badge=stable"><img src="https://img.shields.io/badge/docs-stable-brightgreen.svg?maxAge=2592000" alt="Stable Docs" /></a>

### Related projects

- [bukubrow](https://github.com/SamHH/bukubrow), WebExtension for browser integration
- [oil](https://github.com/AndreiUlmeyda/oil), search-as-you-type cli front-end
- [buku_run](https://github.com/carnager/buku_run), rofi front-end
- [pinku](https://github.com/mosegontar/pinku), a Pinboard-to-buku import utility
- [buku-dmenu](https://gitlab.com/benoliver999/buku-dmenu), a simple bash dmenu wrapper
- [poku](https://github.com/shanedabes/poku), sync between Pocket and buku
- [Ebuku](https://github.com/flexibeast/ebuku), Emacs interface to buku
- [diigoku](https://github.com/dppdppd/diigoku), buku importer for Diigo
- [BukuBot](https://git.xmpp-it.net/sch/BukuBot), Chat bot for XMPP with an extended visual interface


### Videos

- [Buku: Take Your Bookmarks Everywhere You Go](https://www.youtube.com/embed/9HzEHrUBQXE)
- [Buku is a great open-source bookmark manager](https://www.youtube.com/embed/7VxgKMWm-J8)

### In the Press

- [2daygeek](http://www.2daygeek.com/buku-command-line-bookmark-manager-linux/)
- [Hacker Milk](https://hackermilk.blogspot.com/2020/01/how-to-manage-your-browsers-bookmarks.html)
- [It's F.O.S.S.](https://itsfoss.com/buku-command-line-bookmark-manager-linux/)
- [LinOxide](https://linoxide.com/linux-how-to/buku-browser-bookmarks-linux/)
- [LinuxUser Magazine 01/2017 Issue](http://www.linux-community.de/LU/2017/01/Das-Beste-aus-zwei-Welten)
- [Make Tech Easier](https://www.maketecheasier.com/manage-browser-bookmarks-ubuntu-command-line/)
- [One Thing Well](http://onethingwell.org/post/144952807044/buku)
- [Open Source For You](https://opensourceforu.com/2018/05/buku-a-bookmark-manager-in-the-command-line/)
- [ulno.net](https://ulno.net/blog/2017-07-19/of-bookmarks-tags-and-browsers/)
