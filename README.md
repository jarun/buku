# MarkIt
Cmdline bookmark management utility written using Python3 and SQLite3. Currently under development with implemented options working.  
  
The SQLite3 database file is stored in `$HOME/.cache/bookmarks.db` for each user.  
  
It's  advisable  to copy URLs directly from the browser address bar, i.e., along with the leading `http://` or `https://` token. `markit` looks up title data (found within <title></title> tags of HTML) from the web only for fully-formed HTTP or HTTPS URLs. If the URL contains characters like ';', '&' or brackets they may be interpreted specially by the shell. To avoid it, add the URL within single ''' or double '"' qoutes.  
  
You can either add or update or delete record(s) in one instance. A combination of these operations are not supported in a single instance. The same URL cannot be added twice. You can update tags and title data or delete it.  
  
Search works in mysterious ways. All the keywords are treated as a single tag together. Bookmarks with partial sequential tag matches are shown in results. The same keywords are separately searched as unique tokens so that entries with matching URL or title data are also shown in results.  
  
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
- Show all bookmarks in a go
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
To be added soon!

Goals
-
- Parse full page data??? Not sure, might end up writing a search engine like Google. ;)
- Optional password protection

#License
GPL v3  
Copyright (C) 2015 by Arun Prakash Jana &lt;engineerarun@gmail.com&gt;

# Developer(s)
Arun PraKash Jana &lt;engineerarun@gmail.com&gt;
