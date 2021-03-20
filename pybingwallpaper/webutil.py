#!/usr/bin/env python
import gzip
import ssl
from io import BytesIO

from . import log
from .ntlmauth import HTTPNtlmAuthHandler
from .py23 import get_moved_attr, import_moved

_logger = log.getChild('webutil')

Request = get_moved_attr('urllib2', 'urllib.request', 'Request')
urlopen = get_moved_attr('urllib2', 'urllib.request', 'urlopen')
URLError = get_moved_attr('urllib2', 'urllib.error', 'URLError')
urlparse = get_moved_attr('urlparse', 'urllib.parse', 'urlparse')
parse_qs = get_moved_attr('urlparse', 'urllib.parse', 'parse_qs')
urlencode = get_moved_attr('urllib', 'urllib.parse', 'urlencode')
urljoin = get_moved_attr('urlparse', 'urllib.parse', 'urljoin')
url_request = import_moved('urllib2', 'urllib.request')


def setup_proxy(proxy_protocols, proxy_url, proxy_port, sites, username="", password=""):
    proxy_dict = {p: '%s:%s' % (proxy_url, proxy_port) for p in proxy_protocols}
    ph = url_request.ProxyHandler(proxy_dict)
    passman = url_request.HTTPPasswordMgrWithDefaultRealm()

    _logger.info('add proxy site %s', sites)
    passman.add_password(None, sites, username, password)
    pnah = HTTPNtlmAuthHandler.ProxyNtlmAuthHandler(passman)
    pbah = url_request.ProxyBasicAuthHandler(passman)
    pdah = url_request.ProxyDigestAuthHandler(passman)

    cp = url_request.HTTPCookieProcessor()
    context = ssl.create_default_context()
    opener = url_request.build_opener(cp,
                                      url_request.HTTPSHandler(debuglevel=1, context=context),
                                      url_request.HTTPHandler(debuglevel=99),
                                      ph, pnah, pbah, pdah,
                                      url_request.HTTPErrorProcessor())
    url_request.install_opener(opener)


def _ungzip(html):
    if html[:6] == b'\x1f\x8b\x08\x00\x00\x00':
        html = gzip.GzipFile(fileobj=BytesIO(html)).read()
    return html


def loadurl(url, headers=None, optional=False):
    headers = headers or dict()
    if not url:
        return None
    _logger.debug('getting url %s, headers %s', url, headers)
    if 'User-Agent' not in headers:
        headers[
            'User-Agent'
        ] = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1521.3 Safari/537.36'
    try:
        req = Request(url=url, headers=headers)
        con = urlopen(req)
    except Exception as err:
        if not optional:
            _logger.error('error %s occurs during load %s with header %s', err, url, headers)
        _logger.debug('', exc_info=1)
        return None
    if con:
        _logger.debug("Hit %s code: %s", str(con), con.getcode())
        data = con.read()
        data = _ungzip(data)
        _logger.log(log.PAGEDUMP, repr(data))
        return data
    else:
        _logger.error("No data returned.")
    return None


def loadpage(url, codec=('utf8', 'strict'), headers=None, optional=False):
    headers = headers or dict()
    data = loadurl(url, headers=headers, optional=optional)
    return data.decode(*codec) if data else None


def postto(url, datadict, headers=None, decodec='gbk'):
    headers = headers or dict()
    params = urlencode(datadict)
    _logger.info('Post %s to %s, headers %s', params, url, headers)
    try:
        req = Request(url=url, data=params)
        for k, v in list(headers.items()):
            req.add_header(k, v)
        con = urlopen(req)
        if con:
            _logger.debug("Hit %s %d", str(con), con.getcode())
            data = con.read(-1)
            return data.decode(decodec)
        else:
            _logger.error("No data returned.")
            return None

    except Exception as err:
        _logger.error('error %s occurs during post %s to %s', err, params, url)
        _logger.debug('', exc_info=1)


def test_header(url, extra_headers=None):
    headers = {
        'method': 'HEAD',
    }
    if extra_headers:
        headers.update(extra_headers)
    resp = loadurl(url, headers, True)
    return resp is not None
