# MarkIt
`markit` is a cmdline bookmark management utility written using Python3 and SQLite3. Currently under development with implemented options working.  
  
`markit` exists because of my monumental dependency on <a href="http://historio.us/">historious</a>. I wanted the same database on my local system. However, I couldn't find any equally flexible solution. Hence, `MarkIt`!  
  
The SQLite3 database file is stored in `$HOME/.cache/markit/bookmarks.db` for each user.  
  
It's  advisable  to copy URLs directly from the browser address bar, i.e., along with the leading `http://` or `https://` token. `markit` looks up title data (found within <title></title> tags of HTML) from the web only for fully-formed HTTP or HTTPS URLs. If the URL contains characters like `;`, `&` or brackets they may be interpreted specially by the shell. To avoid it, add the URL within single ''' or double '"' qoutes.  
  
You can either add or update or delete record(s) in one instance. A combination of these operations are not supported in a single instance. The same URL cannot be added twice. You can update tags and title data or delete it.  
  
Search works in mysterious ways:
- Substrings match (`match` matches `rematched`).
- All the keywords are treated as a `single` tag together (order maintained). Bookmarks with partial or complete tag matches are shown in results.
- The same keywords are `separately` searched as unique tokens so that entries with matching URL or title data are also shown in results. Order is irrelevant in this case.
  
`markit` is GPLv3 licensed.

If you find `markit` useful, please consider donating via PayPal.  
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&amp;hosted_button_id=RMLTQ76JSXJ4Q"><img src="https://www.paypal.com/en_US/i/btn/btn_donateCC_LG.gif" alt="Donate Button with Credit Cards" /></a>

# Features
- Add, update or remove a bookmark
- Add tags to bookmarks
- Optionally fetch page title data from the web (default: disabled, use `-o`)
- Use (partial) tags or keywords to search bookmarks
- Unique URLs to avoid duplicates, show index if URL already exists
- Open search results in browser
- Browser (Chromium and Firefox based) errors and warnings suppression
- Show single bookmark by ID or all bookmarks in a go
- Delete all bookmarks
- Add a bookmark at N<sup>th</sup> index, to fill deleted bookmark indexes
- Secure SQLite3 queries to access database
- Handle first level of redirections (reports IP blocking)
- Unicode in URL works
- UTF-8 request and response, page character set detection
- Works with Python 3.x
- Coloured output for clarity
- Manpage for quick reference
- Optional debug information
- Fast and clean (no ads or clutter)
- Minimal dependencies
- Open source and free

# Installation

`markit` requires Python 3.x to work.

1. If you have git installed (the steps are tested on Ubuntu 14.04.3 x64_64):  
<pre>$ git clone https://github.com/jarun/markit/  
$ cd markit
$ sudo make install</pre>  
To remove, run:  
<pre>$ sudo make uninstall</pre>

2. If you do not have git installed:  
Download the <a href="https://github.com/jarun/markit/archive/master.zip">development version</a> source code. Extract, cd into the directory and run:
<pre>$ sudo make install</pre>
If you do not want to install, `markit` is standalone:
<pre>$ chmod +x markit
$ ./markit ...</pre>

# Usage
<pre>Usage: markit [OPTIONS] KEYWORDS...
Bookmark manager. Your private Google.

Options
  -a URL tag 1, tag 2, ...   add URL as bookmark with comma separated tags
  -d N                       delete entry at index N
  -D                         delete ALL bookmarks
  -i N                       add entry at index N, works with -a, use to fill deleted index
  -o                         fetch title info from web, works with -a or -u
  -p N                       show details of bookmark record at index N"
  -P                         show all bookmarks along with real index from database
  -s keyword(s)              search all bookmarks for a (partial) tag or keywords
  -u N                       update entry at index N (from output of -p)
  -z                         show debug information
                             you can either add or update or delete in one instance
                             any other option shows help and exits markit

Keys
  1-N                        open Nth search result in browser. Enter exits markit.</pre>
  
# Examples
1. Add a new bookmark with tags `linux news` and `open source`:
<pre>$ markit -a http://tuxdiary.com linux news, open source
Added at index 15012014</pre>
The assigned automatic index 15012014 is unique, one greater than highest index already in use in database.
2. Add a bookmark, fetch page Title information from web:
<pre>$ markit -a -o http://tuxdiary.com linux news, open source
Title: [TuxDiary | Linux, open source and a pinch of leisure.]
Added at index 15012014</pre>
3. Update existing bookmark at index 15012014 with a new tag:
<pre>$ markit -u 15012014 -o http://tuxdiary.com linux news, open source, magazine
Title: [TuxDiary | Linux, open source and a pinch of leisure.]
Updated</pre>
4. Delete bookmark at index 15012014:
<pre>$ markit -d 15012014</pre>
5. Delete all bookmarks:
<pre>$ markit -D</pre>
6. Insert a bookmark at deleted index 15012014 (fails if index or URL exists in database):
<pre>$ markit -i 15012014 -a -o http://tuxdiary.com/about linux news, open source
Title: [A journey with WordPress | TuxDiary]
Added at index 15012014</pre>
This option is useful in filling deleted indices from database manually.
7. Show info on bookmark at index 15012014:
<pre>$ markit -p 15012014</pre>
8. Show all bookmarks with real index from database:
<pre>$ markit -P</pre>
9. Search bookmarks:
<pre>$ markit -s kernel debugging</pre>
10. Show debug info:
<pre>$ markit -z</pre>
11. Show help:
<pre>$ markit</pre>
12. Show markit manpage:
<pre>$ man markit</pre>

#License
GPL v3  
Copyright (C) 2015 by Arun Prakash Jana &lt;engineerarun@gmail.com&gt;

# Contributions
I would love to see pull requests with the following features:
- Exact word match (against substring in a word as it works currently. Hint: REGEXP)
- Parse full page data??? Might end up writing a search engine like Google. ;)
- Optional password protection

# Developer(s)
Arun Prakash Jana &lt;engineerarun@gmail.com&gt;
