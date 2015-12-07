# MarkIt

![Screenshot](markit.png)

`markit` is a cmdline bookmark management utility written in Python3 and SQLite3. `markit` exists because of my monumental dependency on <a href="http://historio.us/">historious</a>. I wanted the same database on my local system. However, I couldn't find an equally flexible cmdline solution. Hence, `MarkIt`!  
  
The SQLite3 database file is stored in `$HOME/.cache/markit/bookmarks.db` for each user.  
  
`markit` is GPLv3 licensed.

If you find `markit` useful, please consider donating via PayPal.  
<a href="https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&amp;hosted_button_id=RMLTQ76JSXJ4Q"><img src="https://www.paypal.com/en_US/i/btn/btn_donateCC_LG.gif" alt="Donate Button with Credit Cards" /></a>

# Features
- Add, update or remove a bookmark
- Add tags to bookmarks
- Optionally fetch page title data from the web (default: disabled)
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

`markit` requires Python 3.x to work.

1. If you have git installed (the steps are tested on Ubuntu 14.04.3 x64_64):  
<pre>$ git clone https://github.com/jarun/markit/  
$ cd markit
$ sudo make install</pre>  
To remove, run:  
<pre>$ sudo make uninstall</pre>

2. If you do not have git installed:  
Download the <a href="https://github.com/jarun/markit/releases/latest">latest stable release</a> or <a href="https://github.com/jarun/markit/archive/master.zip">development version</a> source code. Extract, cd into the directory and run:
<pre>$ sudo make install</pre>
If you do not want to install, `markit` is standalone:
<pre>$ chmod +x markit
$ ./markit ...</pre>

# Usage
<b>Operational notes:</b>
- It's  advisable  to copy URLs directly from the browser address bar, i.e., along with the leading `http://` or `https://` token. `markit` looks up title data (found within <title></title> tags of HTML) from the web ONLY for fully-formed HTTP(S) URLs.
- If the URL contains characters like `;`, `&` or brackets they may be interpreted specially by the shell. To avoid it, add the URL within single `'` or double `"` quotes.
- The same URL cannot be added twice. You can update tags and re-fetch title data. You can also delete it and insert at the same index. 
- You can either add or update or delete record(s) in one instance. A combination of these operations is not supported in a single run.
- Search works in mysterious ways:
  - Substrings match (`match` matches `rematched`) for URL, tags and title.
  - All the keywords are treated together as a `single` tag in the `same order`. Bookmarks with partial or complete tag matches are shown in results.
  - `-s` : match any of the keywords in URL or title. Order is irrelevant.
  - `-S` : match all the keywords in URL or title. Order is irrelevant.
  - Search results are indexed serially. This index is different from actual database index of a bookmark reord which is shown within `()` after the URL.
  
<b>Cmdline help:</b>
  
<pre>Usage: markit [OPTIONS] KEYWORDS...
Bookmark manager. Your private Google.

Options
  -a URL tag 1, tag 2, ...   add URL as bookmark with comma separated tags
  -d N                       delete entry at DB index N (from -P output)
  -D                         delete ALL bookmarks
  -i N                       insert entry at DB index N, useful to fill deleted index
  -o N                       open URL at DB index N in browser
  -p N                       show details of bookmark record at DB index N
  -P                         show all bookmarks along with index from DB
  -R                         refresh all bookmarks, tags retained
  -s keyword(s)              search all bookmarks for a (partial) tag or any keyword
  -S keyword(s)              search all bookmarks for a (partial) tag or all keywords
  -u N                       update entry at DB index N
  -w                         fetch title info from web, works with -a, -i, -u
  -x N                       works with -P, N=1: show only URL, N=2: show URL and tag
  -z                         show debug information
                             you can either add or update or delete in one instance
                             any other option shows help and exits markit

Keys
  1-N                        open Nth search result in browser. Enter exits markit.</pre>
  
# Examples
1. <b>Add</b> a new bookmark with tags `linux news` and `open source`:
<pre>$ markit -a http://tuxdiary.com linux news, open source
Added at index 15012014</pre>
The assigned automatic index 15012014 is unique, one greater than highest index already in use in database.
2. Add a bookmark, <b>fetch page title</b> information from web:
<pre>$ markit -a -w http://tuxdiary.com linux news, open source
Title: [TuxDiary | Linux, open source and a pinch of leisure.]
Added at index 15012014</pre>
3. <b>Update</b> existing bookmark at index 15012014 with a new tag:
<pre>$ markit -u 15012014 -w http://tuxdiary.com linux news, open source, magazine
Title: [TuxDiary | Linux, open source and a pinch of leisure.]
Updated</pre>
4. Update or <b>refresh full DB</b>:
<pre>$ markit -R</pre>
5. <b>Delete</b> bookmark at index 15012014:
<pre>$ markit -d 15012014</pre>
6. <b>Delete all</b> bookmarks:
<pre>$ markit -D</pre>
7. <b>Insert</b> a bookmark at index 15012014 (fails if index or URL exists in database):
<pre>$ markit -i 15012014 -w http://tuxdiary.com/about linux news, open source
Title: [A journey with WordPress | TuxDiary]
Added at index 15012014</pre>
This option is useful in filling deleted indices from database manually.
8. <b>Show info</b> on bookmark at index 15012014:
<pre>$ markit -p 15012014</pre>
9. <b>Show all</b> bookmarks with real index from database:
<pre>$ markit -P</pre>
10. <b>Open URL</b> at index 15012014 in browser:
<pre>$ markit -o 15012014</pre>
11. <b>Search</b> bookmarks for a tag matching `*kernel debugging*` or any of the keywords `*kernel*` and `*debugging*` in URL or title (separately):
<pre>$ markit -s kernel debugging</pre>
12. <b>Search</b> bookmarks for a tag matching `*kernel debugging*` or all the keywords `*kernel*` and `*debugging*` in URL or title (separately):
<pre>$ markit -S kernel debugging</pre>
13. Show <b>debug info</b>:
<pre>$ markit -z</pre>
14. Show <b>help</b>:
<pre>$ markit</pre>
15. Check <b>manpage</b>:
<pre>$ man markit</pre>
16. `markit` doesn't have any <b>import feature</b> of its own. To import URLs in bulk, create a script with URLs and tags like the following (check TIP below):
<pre>#!/bin/bash
markit -aw https://wireless.wiki.kernel.org/ networking, device drivers
markit -aw https://courses.engr.illinois.edu/ece390/books/artofasm/ArtofAsm.html assembly
markit -aw http://www.tittbit.in/
markit -aw http://www.mikroe.com/chapters/view/65/ electronics
markit -aw "http://msdn.microsoft.com/en-us/library/bb470206(v=vs.85).aspx" file systems
markit -aw http://www.ibm.com/developerworks/linux/library/l-linuxboot/index.html boot process</pre>
Make the script executable and run to batch add bookmarks.
17. To <b>update selected URLs</b> (refresh) along with your tags, first get the unformatted selective output with URL and tags:
<pre>$ markit -P -x 2 | tee myurls</pre>
Remove the lines you don't need. Add `markit -wu ` in front of all the other lines (check TIP below). Should look like:
<pre>#!/bin/bash
markit -wu 50 https://wireless.wiki.kernel.org/ networking, device drivers
markit -wu 51 https://courses.engr.illinois.edu/ece390/books/artofasm/ArtofAsm.html assembly
markit -wu 52 http://www.tittbit.in/
markit -wu 53 http://www.mikroe.com/chapters/view/65/ electronics
markit -wu 54 "http://msdn.microsoft.com/en-us/library/bb470206(v=vs.85).aspx" file systems
markit -wu 55 http://www.ibm.com/developerworks/linux/library/l-linuxboot/index.html boot process</pre>
Run the script:
<pre>$ chmod +x myurls
$ ./myurls</pre>
  
<b>TIP:</b>  
To add the same text at the beginning of multiple lines using vim editor:  
  - Press `Ctrl-v` to select the first column of text in the lines you want to change (visual mode).
  - Press `Shift-i` and type the text you want to insert.
  - Hit `Esc`, wait 1 second and the inserted text will appear on every line.
  
Using sed:
<pre>$ sed -i 's/^/markit -wu /' filename</pre>

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
