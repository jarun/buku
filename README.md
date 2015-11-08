# MarkIt
Cmdline bookmark management utility written using Python3 and SQLite3. Currently under development with implemented options working.

`markit` is GPLv3 licensed.

If you find `markit` useful, please consider donating via PayPal.  
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&amp;hosted_button_id=RMLTQ76JSXJ4Q"><img src="https://www.paypal.com/en_US/i/btn/btn_donateCC_LG.gif" alt="Donate Button with Credit Cards" /></a>

# Features
- Add, update or remove a bookmark
- Add tags to bookmarks
- Optionally fetch page title data from the web (default: disabled, use `-o`)
- Use (partial) tags or keywords to search bookmarks
- Open search results in browser
- Browser (Chromium and Firefox based) errors and warnings suppression
- Show all bookmarks in a go
- Delete all bookmarks
- Add a bookmark at N<sup>th</sub> index, to fill deleted bookmark indexes
- Secure SQLite3 queries to access database
- Handle first level of redirections (reports IP blocking)
- Unicode in URL works
- UTF-8 request and response
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
  
Goals
-
- Parse full page data??? Not sure, might end up writing a search engine like Google. ;)
- Optional password protection

#License
GPL v3  
Copyright (C) 2015 by Arun Prakash Jana &lt;engineerarun@gmail.com&gt;

# Developer(s)
Arun PraKash Jana &lt;engineerarun@gmail.com&gt;
