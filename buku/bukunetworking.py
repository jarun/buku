#! /usr/bin/env python3
import cgi
import logging
import os
import re

import certifi
import urllib3
from bs4 import BeautifulSoup

from urllib3 import make_headers
from urllib3.exceptions import LocationParseError
from urllib3.util import parse_url

from .bukuconstants import USER_AGENT, SKIP_MIMES
from .bukuutil import is_nongeneric_url

LOGGER = logging.getLogger()
LOGDBG = LOGGER.debug
LOGERR = LOGGER.error


def gen_headers():
    """Generate headers for network connection."""

    headers = {
        'Accept-Encoding': 'gzip,deflate',
        'User-Agent': USER_AGENT,
        'Accept': '*/*',
        'Cookie': '',
        'DNT': '1'
                }

    proxy_address = os.environ.get('https_proxy')
    if proxy_address:
        try:
            url = parse_url(proxy_address)
        except Exception as e:
            LOGERR(e)
            return headers, proxy_address

        # Strip username and password (if present) and update headers
        if url.auth:
            proxy_address = proxy_address.replace(url.auth + '@', '')
            auth_headers = make_headers(basic_auth=url.auth)
            headers.update(auth_headers)

        LOGDBG('proxy: [%s]', proxy_address)

    return headers, proxy_address


MYHEADERS, MYPROXY = gen_headers()


def is_bad_url(url):
    """Check if URL is malformed.

    .. Note:: This API is not bulletproof but works in most cases.

    Parameters
    ----------
    url : str
        URL to scan.

    Returns
    -------
    bool
        True if URL is malformed, False otherwise.
    """

    # Get the netloc token
    try:
        netloc = parse_url(url).netloc
    except LocationParseError as e:
        LOGERR('%s, URL: %s', e, url)
        return True
    if not netloc:
        # Try of prepend '//' and get netloc
        netloc = parse_url('//' + url).netloc
        if not netloc:
            return True

    LOGDBG('netloc: %s', netloc)

    # netloc cannot start or end with a '.'
    if netloc.startswith('.') or netloc.endswith('.'):
        return True

    # netloc should have at least one '.'
    if netloc.rfind('.') < 0:
        return True

    return False


def is_ignored_mime(url):
    """Check if URL links to ignored MIME.

    .. Note:: Only a 'HEAD' request is made for these URLs.

    Parameters
    ----------
    url : str
        URL to scan.

    Returns
    -------
    bool
        True if URL links to ignored MIME, False otherwise.
    """

    for mime in SKIP_MIMES:
        if url.lower().endswith(mime):
            LOGDBG('matched MIME: %s', mime)
            return True

    return False


def is_unusual_tag(tagstr):
    """Identify unusual tags with word to comma ratio > 3.

    Parameters
    ----------
    tagstr : str
        tag string to check.

    Returns
    -------
    bool
        True if valid tag else False.
    """

    if not tagstr:
        return False

    nwords = len(tagstr.split())
    ncommas = tagstr.count(',') + 1

    if nwords / ncommas > 3:
        return True

    return False


def parse_decoded_page(page):
    """Fetch title, description and keywords from decoded HTML page.

    Parameters
    ----------
    page : str
        Decoded HTML page.

    Returns
    -------
    tuple
        (title, description, keywords).
    """

    title = None
    desc = None
    keys = None

    soup = BeautifulSoup(page, 'html5lib')

    try:
        title = soup.find('title').text.strip().replace('\n', ' ')
        if title:
            title = re.sub(r'\s{2,}', ' ', title)
    except Exception as e:
        LOGDBG(e)

    description = (soup.find('meta', attrs={'name':'description'}) or
                   soup.find('meta', attrs={'name':'Description'}) or
                   soup.find('meta', attrs={'property':'description'}) or
                   soup.find('meta', attrs={'property':'Description'}) or
                   soup.find('meta', attrs={'name':'og:description'}) or
                   soup.find('meta', attrs={'name':'og:Description'}) or
                   soup.find('meta', attrs={'property':'og:description'}) or
                   soup.find('meta', attrs={'property':'og:Description'}))
    try:
        if description:
            desc = description.get('content').strip()
            if desc:
                desc = re.sub(r'\s{2,}', ' ', desc)
    except Exception as e:
        LOGDBG(e)

    keywords = (soup.find('meta', attrs={'name':'keywords'}) or
                soup.find('meta', attrs={'name':'Keywords'}))
    try:
        if keywords:
            keys = keywords.get('content').strip().replace('\n', ' ')
            keys = re.sub(r'\s{2,}', ' ', keys)
            if is_unusual_tag(keys):
                if keys not in (title, desc):
                    LOGDBG('keywords to description: %s', keys)
                    if desc:
                        desc = desc + '\n## ' + keys
                    else:
                        desc = '* ' + keys

                keys = None
    except Exception as e:
        LOGDBG(e)

    LOGDBG('title: %s', title)
    LOGDBG('desc : %s', desc)
    LOGDBG('keys : %s', keys)

    return (title, desc, keys)


def get_data_from_page(resp):
    """Detect HTTP response encoding and invoke parser with decoded data.

    Parameters
    ----------
    resp : HTTP response
        Response from GET request.

    Returns
    -------
    tuple
        (title, description, keywords).
    """

    try:
        soup = BeautifulSoup(resp.data, 'html.parser')
    except Exception as e:
        LOGERR('get_data_from_page(): %s', e)

    try:
        charset = None

        if soup.meta and soup.meta.get('charset') is not None:
            charset = soup.meta.get('charset')
        elif 'content-type' in resp.headers:
            _, params = cgi.parse_header(resp.headers['content-type'])
            if params.get('charset') is not None:
                charset = params.get('charset')

        if not charset and soup:
            meta_tag = soup.find('meta', attrs={'http-equiv': 'Content-Type'})
            if meta_tag:
                _, params = cgi.parse_header(meta_tag.attrs['content'])
                charset = params.get('charset', charset)

        if charset:
            LOGDBG('charset: %s', charset)
            title, desc, keywords = parse_decoded_page(resp.data.decode(charset, errors='replace'))
        else:
            title, desc, keywords = parse_decoded_page(resp.data.decode(errors='replace'))

        return (title, desc, keywords)
    except Exception as e:
        LOGERR(e)
        return (None, None, None)


def get_PoolManager():
    """Creates a pool manager with proxy support, if applicable.

    Returns
    -------
    ProxyManager or PoolManager
        ProxyManager if https_proxy is defined, PoolManager otherwise.
    """

    if MYPROXY:
        return urllib3.ProxyManager(MYPROXY, num_pools=1, headers=MYHEADERS, timeout=15,
                                    cert_reqs='CERT_REQUIRED', ca_certs=certifi.where())

    return urllib3.PoolManager(
        num_pools=1,
        headers=MYHEADERS,
        timeout=15,
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where())


def network_handler(url, http_head=False):
    """Handle server connection and redirections.

    Parameters
    ----------
    url : str
        URL to fetch.
    http_head : bool
        If True, send only HTTP HEAD request. Default is False.

    Returns
    -------
    tuple
        (title, description, tags, recognized mime, bad url).
    """

    page_title = None
    page_desc = None
    page_keys = None
    exception = False

    if is_nongeneric_url(url) or is_bad_url(url):
        return (None, None, None, 0, 1)

    if is_ignored_mime(url) or http_head:
        method = 'HEAD'
    else:
        method = 'GET'

    try:
        manager = get_PoolManager()

        while True:
            resp = manager.request(method, url)

            if resp.status == 200:
                if method == 'GET':
                    page_title, page_desc, page_keys = get_data_from_page(resp)
            elif resp.status == 403 and url.endswith('/'):
                # HTTP response Forbidden
                # Handle URLs in the form of https://www.domain.com/
                # which fail when trying to fetch resource '/'
                # retry without trailing '/'

                LOGDBG('Received status 403: retrying...')
                # Remove trailing /
                url = url[:-1]
                resp.close()
                continue
            else:
                LOGERR('[%s] %s', resp.status, resp.reason)

            if resp:
                resp.close()

            break
    except Exception as e:
        LOGERR('network_handler(): %s', e)
        exception = True
    finally:
        if manager:
            manager.clear()
        if exception:
            return (None, None, None, 0, 0)
        if method == 'HEAD':
            return ('', '', '', 1, 0)
        if page_title is None:
            return ('', page_desc, page_keys, 0, 0)

        return (page_title, page_desc, page_keys, 0, 0)
