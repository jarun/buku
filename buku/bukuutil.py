#! /usr/bin/env python3
import json
import logging
import os
import re
import subprocess
import sys
import time

from .bukuconstants import DELIM

LOGGER = logging.getLogger()
LOGDBG = LOGGER.debug
LOGERR = LOGGER.error


def get_default_dbdir():
    """Determine the directory path where dbfile will be stored.

    If the platform is Windows, use %APPDATA%
    else if $XDG_DATA_HOME is defined, use it
    else if $HOME exists, use it
    else use the current directory.

    Returns
    -------
    str
        Path to database file.
    """

    data_home = os.environ.get('XDG_DATA_HOME')
    if data_home is None:
        if os.environ.get('HOME') is None:
            if sys.platform == 'win32':
                data_home = os.environ.get('APPDATA')
                if data_home is None:
                    return os.path.abspath('.')
            else:
                return os.path.abspath('.')
        else:
            data_home = os.path.join(os.environ.get('HOME'), '.local', 'share')

    return os.path.join(data_home, 'buku')


def is_nongeneric_url(url):
    """Returns True for URLs which are non-http and non-generic.

    Parameters
    ----------
    url : str
        URL to scan.

    Returns
    -------
    bool
        True if URL is a non-generic URL, False otherwise.
    """

    ignored_prefix = [
        'about:',
        'apt:',
        'chrome://',
        'file://',
        'place:',
    ]

    for prefix in ignored_prefix:
        if url.startswith(prefix):
            return True

    return False


def delim_wrap(token):
    """Returns token string wrapped in delimiters.

    Parameters
    ----------
    token : str
        String item to wrap with DELIM.

    Returns
    -------
    str
        Token string wrapped by DELIM.
    """

    if token is None or token.strip() == '':
        return DELIM

    if token[0] != DELIM:
        token = DELIM + token

    if token[-1] != DELIM:
        token = token + DELIM

    return token


def parse_tags(keywords=[]):
    """Format and get tag string from tokens.

    Parameters
    ----------
    keywords : list, optional
        List of tags to parse. Default is empty list.

    Returns
    -------
    str
        Comma-delimited string of tags.
    DELIM : str
        If no keywords, returns the delimiter.
    None
        If keywords is None.
    """

    if keywords is None:
        return None

    if not keywords or len(keywords) < 1 or not keywords[0]:
        return DELIM

    tags = DELIM

    # Cleanse and get the tags
    tagstr = ' '.join(keywords)
    marker = tagstr.find(DELIM)

    while marker >= 0:
        token = tagstr[0:marker]
        tagstr = tagstr[marker + 1:]
        marker = tagstr.find(DELIM)
        token = token.strip()
        if token == '':
            continue

        tags += token + DELIM

    tagstr = tagstr.strip()
    if tagstr != '':
        tags += tagstr + DELIM

    LOGDBG('keywords: %s', keywords)
    LOGDBG('parsed tags: [%s]', tags)

    if tags == DELIM:
        return tags

    # original tags in lower case
    orig_tags = tags.lower().strip(DELIM).split(DELIM)

    # Create list of unique tags and sort
    unique_tags = sorted(set(orig_tags))

    # Wrap with delimiter
    return delim_wrap(DELIM.join(unique_tags))

# ---------------------
# Editor mode functions
# ---------------------


def get_system_editor():
    """Returns default system editor is $EDITOR is set."""

    return os.environ.get('EDITOR', 'none')


def get_firefox_profile_name(path):
    """List folder and detect default Firefox profile name.

    Returns
    -------
    profile : str
        Firefox profile name.
    """
    from configparser import ConfigParser, NoOptionError

    profile_path = os.path.join(path, 'profiles.ini')
    if os.path.exists(profile_path):
        config = ConfigParser()
        config.read(profile_path)
        profiles_names = [section for section in config.sections() if section.startswith('Profile')]
        if not profiles_names:
            return None
        for name in profiles_names:
            try:
                # If profile is default
                if config.getboolean(name, 'default'):
                    profile_path = config.get(name, 'path')
                    return profile_path
            except NoOptionError:
                pass
            try:
                # alternative way to detect default profile
                if config.get(name, 'name').lower() == "default":
                    profile_path = config.get(name, 'path')
                    return profile_path
            except NoOptionError:
                pass

        # There is no default profile
        return None
    LOGDBG('get_firefox_profile_name(): {} does not exist'.format(path))
    return None


def prep_tag_search(tags):
    """Prepare list of tags to search and determine search operator.

    Parameters
    ----------
    tags : str
        String list of tags to search.

    Returns
    -------
    tuple
        (list of formatted tags to search,
         a string indicating query search operator (either OR or AND),
         a regex string of tags or None if ' - ' delimiter not in tags).
    """

    exclude_only = False

    # tags may begin with `- ` if only exclusion list is provided
    if tags.startswith('- '):
        tags = ' ' + tags
        exclude_only = True

    # tags may start with `+ ` etc., tricky test case
    if tags.startswith(('+ ', ', ')):
        tags = tags[2:]

    # tags may end with ` -` etc., tricky test case
    if tags.endswith((' -', ' +', ' ,')):
        tags = tags[:-2]

    # tag exclusion list can be separated by comma (,), so split it first
    excluded_tags = None
    if ' - ' in tags:
        tags, excluded_tags = tags.split(' - ', 1)

        excluded_taglist = [delim_wrap(re.escape(t.strip())) for t in excluded_tags.split(',')]
        # join with pipe to construct regex string
        excluded_tags = '|'.join(excluded_taglist)

    if exclude_only:
        search_operator = 'OR'
        tags = ['']
    else:
        # do not allow combination of search logics in tag inclusion list
        if ' + ' in tags and ',' in tags:
            return None, None, None

        search_operator = 'OR'
        tag_delim = ','
        if ' + ' in tags:
            search_operator = 'AND'
            tag_delim = ' + '

        tags = [delim_wrap(t.strip()) for t in tags.split(tag_delim)]

    return tags, search_operator, excluded_tags


def gen_auto_tag():
    """Generate a tag in Year-Month-Date format.

    Returns
    -------
    str
        New tag as YYYYMonDD.
    """

    import calendar as cal

    t = time.localtime()
    return '%d%s%02d' % (t.tm_year, cal.month_abbr[t.tm_mon], t.tm_mday)


def to_temp_file_content(url, title_in, tags_in, desc):
    """Generate temporary file content string.

    Parameters
    ----------
    url : str
        URL to open.
    title_in : str
        Title to add manually.
    tags_in : str
        Comma-separated tags to add manually.
    desc : str
        String description.

    Returns
    -------
    str
        Lines as newline separated string.

    Raises
    ------
    AttributeError
        when tags_in is None.
    """

    strings = [('# Lines beginning with "#" will be stripped.\n'
                '# Add URL in next line (single line).'), ]

    # URL
    if url is not None:
        strings += (url,)

    # TITLE
    strings += (('# Add TITLE in next line (single line). '
                 'Leave blank to web fetch, "-" for no title.'),)
    if title_in is None:
        title_in = ''
    elif title_in == '':
        title_in = '-'
    strings += (title_in,)

    # TAGS
    strings += ('# Add comma-separated TAGS in next line (single line).',)
    strings += (tags_in.strip(DELIM),) if not None else ''

    # DESC
    strings += ('# Add COMMENTS in next line(s). Leave blank to web fetch, "-" for no comments.',)
    if desc is None:
        strings += ('\n',)
    elif desc == '':
        strings += ('-',)
    else:
        strings += (desc,)
    return '\n'.join(strings)


def parse_temp_file_content(content):
    """Parse and return temporary file content.

    Parameters
    ----------
    content : str
        String of content.

    Returns
    -------
    tuple
        (url, title, tags, comments)

        url: URL to open
        title: string title to add manually
        tags: string of comma-separated tags to add manually
        comments: string description
    """

    content = content.split('\n')
    content = [c for c in content if not c or c[0] != '#']
    if not content or content[0].strip() == '':
        print('Edit aborted')
        return None

    url = content[0]
    title = None
    if len(content) > 1:
        title = content[1]

    if title == '':
        title = None
    elif title == '-':
        title = ''

    tags = DELIM
    if len(content) > 2:
        tags = parse_tags([content[2]])

    comments = []
    if len(content) > 3:
        comments = [c for c in content[3:]]
        # need to remove all empty line that are at the end
        # and not those in the middle of the text
        for i in range(len(comments) - 1, -1, -1):
            if comments[i].strip() != '':
                break

        if i == -1:
            comments = []
        else:
            comments = comments[0:i+1]

    comments = '\n'.join(comments)
    if comments == '':
        comments = None
    elif comments == '-':
        comments = ''

    return url, title, tags, comments


def edit_rec(editor, url, title_in, tags_in, desc):
    """Edit a bookmark record.

    Parameters
    ----------
    editor : str
        Editor to open.
    URL : str
        URL to open.
    title_in : str
        Title to add manually.
    tags_in : str
        Comma-separated tags to add manually.
    desc : str
        Bookmark description.

    Returns
    -------
    tuple
        Parsed results from parse_temp_file_content().
    """

    import tempfile

    temp_file_content = to_temp_file_content(url, title_in, tags_in, desc)

    fd, tmpfile = tempfile.mkstemp(prefix='buku-edit-')
    os.close(fd)

    try:
        with open(tmpfile, 'w+', encoding='utf-8') as fp:
            fp.write(temp_file_content)
            fp.flush()
            LOGDBG('Edited content written to %s', tmpfile)

        cmd = editor.split(' ')
        cmd += (tmpfile,)
        subprocess.call(cmd)

        with open(tmpfile, 'r', encoding='utf-8') as f:
            content = f.read()

        os.remove(tmpfile)
    except FileNotFoundError:
        if os.path.exists(tmpfile):
            os.remove(tmpfile)
            LOGERR('Cannot open editor')
        else:
            LOGERR('Cannot open tempfile')
        return None

    parsed_content = parse_temp_file_content(content)
    return parsed_content


def format_json(resultset, single_record=False, field_filter=0):
    """Return results in JSON format.

    Parameters
    ----------
    resultset : list
        Search results from DB query.
    single_record : bool, optional
        If True, indicates only one record. Default is False.

    Returns
    -------
    json
        Record(s) in JSON format.
    """

    if single_record:
        marks = {}
        for row in resultset:
            if field_filter == 1:
                marks['uri'] = row[1]
            elif field_filter == 2:
                marks['uri'] = row[1]
                marks['tags'] = row[3][1:-1]
            elif field_filter == 3:
                marks['title'] = row[2]
            elif field_filter == 4:
                marks['uri'] = row[1]
                marks['tags'] = row[3][1:-1]
                marks['title'] = row[2]
            else:
                marks['index'] = row[0]
                marks['uri'] = row[1]
                marks['title'] = row[2]
                marks['description'] = row[4]
                marks['tags'] = row[3][1:-1]
    else:
        marks = []
        for row in resultset:
            if field_filter == 1:
                record = {'uri': row[1]}
            elif field_filter == 2:
                record = {'uri': row[1], 'tags': row[3][1:-1]}
            elif field_filter == 3:
                record = {'title': row[2]}
            elif field_filter == 4:
                record = {'uri': row[1], 'title': row[2], 'tags': row[3][1:-1]}
            else:
                record = {
                    'index': row[0],
                    'uri': row[1],
                    'title': row[2],
                    'description': row[4],
                    'tags': row[3][1:-1]
                }

            marks.append(record)

    return json.dumps(marks, sort_keys=True, indent=4)


def is_int(string):
    """Check if a string is a digit.

    string : str
        Input string to check.

    Returns
    -------
    bool
        True on success, False on exception.
    """

    try:
        int(string)
        return True
    except Exception:
        return False


def regexp(expr, item):
    """Perform a regular expression search.

    Parameters
    ----------
    expr : regex
        Regular expression to search for.
    item : str
        Item on which to perform regex search.

    Returns
    -------
    bool
        True if result of search is not None, returns None otherwise.
    """

    if expr is None or item is None:
        LOGDBG('expr: [%s], item: [%s]', expr, item)
        return False

    return re.search(expr, item, re.IGNORECASE) is not None
