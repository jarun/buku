#! /usr/bin/env python3

from enum import Enum
import logging

from .bukuconstants import DELIM
from .bukuutil import delim_wrap, is_nongeneric_url, parse_tags

# Set up logging
LOGGER = logging.getLogger()
LOGDBG = LOGGER.debug
LOGERR = LOGGER.error

IGNORE_FF_BOOKMARK_FOLDERS = frozenset(["placesRoot", "bookmarksMenuFolder"])


class BukuImporter:
    @staticmethod
    def import_md(filepath, newtag):
        """Parse bookmark Markdown file.

        Parameters
        ----------
        filepath : str
            Path to Markdown file.
        newtag : str
            New tag for bookmarks in Markdown file.

        Returns
        -------
        tuple
            Parsed result.
        """
        with open(filepath, mode='r', encoding='utf-8') as infp:
            for line in infp:
                # Supported Markdown format: [title](url)
                # Find position of title end, url start delimiter combo
                index = line.find('](')
                if index != -1:
                    # Find title start delimiter
                    title_start_delim = line[:index].find('[')
                    # Reverse find the url end delimiter
                    url_end_delim = line[index + 2:].rfind(')')

                    if title_start_delim != -1 and url_end_delim > 0:
                        # Parse title
                        title = line[title_start_delim + 1:index]
                        # Parse url
                        url = line[index + 2:index + 2 + url_end_delim]
                        if is_nongeneric_url(url):
                            continue

                        yield (
                            url, title, delim_wrap(newtag)
                            if newtag else None, None, 0, True
                        )

    @staticmethod
    def import_org(filepath, newtag):
        """Parse bookmark org file.

        Parameters
        ----------
        filepath : str
            Path to org file.
        newtag : str
            New tag for bookmarks in org file.

        Returns
        -------
        tuple
            Parsed result.
        """
        with open(filepath, mode='r', encoding='utf-8') as infp:
            # Supported Markdown format: * [[url][title]]
            # Find position of url end, title start delimiter combo
            for line in infp:
                index = line.find('][')
                if index != -1:
                    # Find url start delimiter
                    url_start_delim = line[:index].find('[[')
                    # Reverse find title end delimiter
                    title_end_delim = line[index + 2:].rfind(']]')

                    if url_start_delim != -1 and title_end_delim > 0:
                        # Parse title
                        title = line[index + 2: index + 2 + title_end_delim]
                        # Parse url
                        url = line[url_start_delim + 2:index]
                        if is_nongeneric_url(url):
                            continue

                        yield (
                            url, title, delim_wrap(newtag)
                            if newtag else None, None, 0, True
                        )

    @staticmethod
    def import_firefox_json(json, add_bookmark_folder_as_tag=False, unique_tag=None):
        """Open Firefox JSON export file and import data.
        Ignore 'SmartBookmark'  and 'Separator'  entries.

        Needed/used fields out of the JSON schema of the bookmarks:

        title              : the name/title of the entry
        tags               : ',' separated tags for the bookmark entry
        typeCode           : 1 - uri, 2 - subfolder, 3 - separator
        annos/{name,value} : following annotation entries are used
            name : Places/SmartBookmark            : identifies smart folder, ignored
            name : bookmarkPropereties/description :  detailed bookmark entry description
        children           : for subfolders, recurse into the child entries

        Parameters
        ----------
        path : str
            Path to Firefox JSON bookmarks file.
        unique_tag : str
            Timestamp tag in YYYYMonDD format.
        add_bookmark_folder_as_tag : bool
            True if bookmark parent folder should be added as tags else False.
        """

        class TypeCode(Enum):
            """ Format
                typeCode
                    1 : uri        (type=text/x-moz-place)
                    2 : subfolder  (type=text/x-moz-container)
                    3 : separator  (type=text/x-moz-separator)
            """
            uri = 1
            folder = 2
            separator = 3

        def is_smart(entry):
            result = False
            try:
                d = [anno for anno in entry['annos'] if anno['name'] == "Places/SmartBookmark"]
                result = bool(len(d))
            except Exception:
                result = False

            return result

        def extract_desc(entry):
            try:
                d = [
                    anno for anno in entry['annos']
                    if anno['name'] == "bookmarkProperties/description"
                ]
                return d[0]['value']
            except Exception:
                LOGDBG("ff_json: No description found for entry: {} {}".format(entry['uri'], entry['title']))
                return ""

        def extract_tags(entry):
            tags = []
            try:
                tags = entry['tags'].split(',')
            except Exception:
                LOGDBG("ff_json: No tags found for entry: {} {}".format(entry['uri'], entry['title']))

            return tags

        def iterate_children(parent_folder, entry_list):
            for bm_entry in entry_list:
                entry_title = bm_entry['title'] if 'title' in bm_entry else "<no title>"

                try:
                    typeCode = bm_entry['typeCode']
                except Exception:
                    LOGDBG("ff_json: item without typeCode found, ignoring: {}".format(entry_title))
                    continue

                LOGDBG("ff_json: processing typeCode '{}', title '{}'".format(typeCode, entry_title))
                if TypeCode.uri.value == typeCode:
                    try:
                        if is_smart(bm_entry):
                            LOGDBG("ff_json: SmartBookmark found, ignoring: {}".format(entry_title))
                            continue

                        if is_nongeneric_url(bm_entry['uri']):
                            LOGDBG("ff_json: Non-Generic URL found, ignoring: {}".format(entry_title))
                            continue

                        desc = extract_desc(bm_entry)
                        bookmark_tags = extract_tags(bm_entry)

                        # if parent_folder is not "None"
                        if add_bookmark_folder_as_tag and parent_folder:
                            bookmark_tags.append(parent_folder)

                        if unique_tag:
                            bookmark_tags.append(unique_tag)

                        formatted_tags = [DELIM + tag for tag in bookmark_tags]
                        tags = parse_tags(formatted_tags)

                        LOGDBG("ff_json: Entry found: {}, {}, {}, {} " .format(bm_entry['uri'], entry_title, tags, desc))
                        yield (bm_entry['uri'], entry_title, tags, desc, 0, True, False)

                    except Exception as e:
                        LOGERR("ff_json: Error parsing entry '{}' Exception '{}'".format(entry_title, e))

                elif TypeCode.folder.value == typeCode:

                    # ignore special bookmark folders
                    if 'root' in bm_entry and bm_entry['root'] in IGNORE_FF_BOOKMARK_FOLDERS:
                        LOGDBG("ff_json: ignoring root folder: {}" .format(entry_title))
                        entry_title = None

                    if "children" in bm_entry:
                        yield from iterate_children(entry_title, bm_entry['children'])
                    else:
                        # if any of the properties does not exist, bail out silently
                        LOGDBG("ff_json: No 'children' found in bookmark folder - skipping: {}".format(entry_title))

                elif TypeCode.separator.value == typeCode:
                    # ignore separator
                    pass
                else:
                    LOGDBG("ff_json: Unknown typeCode found : {}".format(typeCode))

        if "children" in json:
            main_entry_list = json['children']
        else:
            LOGDBG("ff_json: No children in Root entry found")
            return []

        yield from iterate_children(None, main_entry_list)

    @staticmethod
    def import_html(html_soup, add_parent_folder_as_tag, newtag):
        """Parse bookmark HTML.

        Parameters
        ----------
        html_soup : BeautifulSoup object
            BeautifulSoup representation of bookmark HTML.
        add_parent_folder_as_tag : bool
            True if bookmark parent folders should be added as tags else False.
        newtag : str
            A new unique tag to add to imported bookmarks.

        Returns
        -------
        tuple
            Parsed result.
        """

        # compatibility
        soup = html_soup

        for tag in soup.findAll('a'):
            # Extract comment from <dd> tag
            try:
                if is_nongeneric_url(tag['href']):
                    continue
            except KeyError:
                continue

            desc = None
            comment_tag = tag.findNextSibling('dd')

            if comment_tag:
                desc = comment_tag.find(text=True, recursive=False)

            # add parent folder as tag
            if add_parent_folder_as_tag:
                # could be its folder or not
                possible_folder = tag.find_previous('h3')
                # get list of tags within that folder
                tag_list = tag.parent.parent.find_parent('dl')

                if ((possible_folder) and possible_folder.parent in list(tag_list.parents)):
                    # then it's the folder of this bookmark
                    if tag.has_attr('tags'):
                        tag['tags'] += (DELIM + possible_folder.text)
                    else:
                        tag['tags'] = possible_folder.text

            # add unique tag if opted
            if newtag:
                if tag.has_attr('tags'):
                    tag['tags'] += (DELIM + newtag)
                else:
                    tag['tags'] = newtag

            yield (
                tag['href'], tag.string,
                parse_tags([tag['tags']]) if tag.has_attr('tags') else None,
                desc if not desc else desc.strip(), 0, True, False
            )
