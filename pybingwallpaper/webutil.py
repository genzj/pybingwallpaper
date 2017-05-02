#!/usr/bin/env python
from . import log
from .py23 import PY3, get_moved_attr
import gzip
from io import BytesIO

_logger = log.getChild('webutil')

Request = get_moved_attr('urllib2', 'urllib.request', 'Request')
urlopen = get_moved_attr('urllib2', 'urllib.request', 'urlopen')
URLError = get_moved_attr('urllib2', 'urllib.error', 'URLError')
urlparse = get_moved_attr('urlparse', 'urllib.parse', 'urlparse')
urlencode = get_moved_attr('urllib', 'urllib.parse', 'urlencode')
urljoin = get_moved_attr('urlparse', 'urllib.parse', 'urljoin')


if PY3:
    from .ntlmauth import HTTPNtlmAuthHandler
    from importlib import import_module
    _logger.debug('importing libs for python 3.x')
    _urlrequest = import_module('urllib.request')

    def setup_proxy(proxy_protocols, proxy_url, proxy_port, sites, username="", password=""):
        proxy_dict = {p:'%s:%s'%(proxy_url, proxy_port) for p in proxy_protocols}
        ph=_urlrequest.ProxyHandler(proxy_dict)
        passman = _urlrequest.HTTPPasswordMgrWithDefaultRealm()

        _logger.info('add proxy site %s', sites)
        passman.add_password(None, sites, username, password)
        pnah= HTTPNtlmAuthHandler.ProxyNtlmAuthHandler(passman)
        pbah= _urlrequest.ProxyBasicAuthHandler(passman)
        pdah= _urlrequest.ProxyDigestAuthHandler(passman)

        cp=_urlrequest.HTTPCookieProcessor()
        opener=_urlrequest.build_opener(cp,
                                        _urlrequest.HTTPSHandler(debuglevel=1),
                                        _urlrequest.HTTPHandler(debuglevel=99),
                                        ph, pnah, pbah, pdah,
                                        _urlrequest.HTTPErrorProcessor())
        _urlrequest.install_opener(opener)


def _ungzip(html):
    if html[:6] == b'\x1f\x8b\x08\x00\x00\x00':
        html = gzip.GzipFile(fileobj = BytesIO(html)).read()
    return html

def loadurl(url, headers={}, optional=False):
    if not url: return None
    _logger.debug('getting url %s, headers %s', url, headers)
    if 'User-Agent' not in headers:
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1521.3 Safari/537.36'
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

def loadpage(url, decodec=('utf8', 'strict'), headers={}, optional=False):
    data = loadurl(url, headers=headers, optional=optional)
    return data.decode(*decodec) if data else None

def postto(url, datadict, headers={}, decodec='gbk'):
    params = urlencode(datadict)
    _logger.info('Post %s to %s, headers %s', params, url, headers)
    try:
        req = Request(url=url, data=params)
        for k,v in list(headers.items()):
            req.add_header(k,v)
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

if __name__ == '__main__':
    _logger.setLevel(log.PAGEDUMP)
    _logger.info('try loading a paage')
    c = loadpage('http://ifconfig.me/all', headers={'User-Agent':'curl'})
    _logger.info('page content: \n%s', c)
