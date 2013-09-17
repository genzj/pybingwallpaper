#!/usr/bin/env python3
import re
import log
import webutil
from urllib.parse import urljoin

_logger = log.getChild('bingwallpaper')

def _property_need_loading(f):
    def wrapper(*args, **kwargs):
        args[0]._assert_load(f.__name__)
        return f(*args, **kwargs)
    return wrapper

class BingWallpaperPage:
    def __init__(self, url):
        self.update(url)

    def update(self, url):
        if hasattr(self, 'url') and self.url == url:
            return
        self.reset()
        self.url = url

    def reset(self):
        self.__loaded = False
        self.content = ''
        self.__img_link = None

    def _parse(self):
        img_pat = re.compile(r"url:'(.*?\d+x\d+\.jpg)'")

        imgs = img_pat.findall(self.content)

        if not imgs:
            _logger.error('no imgs')
            return False

        self.__img_link = urljoin(self.url, imgs[0])

        return True

    def load(self):
        self.reset()
        _logger.info('loading from %s', self.url)
        self.content = webutil.loadpage(self.url)
        if self.content:
            _logger.info('%d bytes loaded', len(self.content))
            self.__loaded = True
            self._parse()
        else:
            _logger.error('can\'t download photo page')

    def loaded(self):
        return self.__loaded

    @_property_need_loading
    def img_link(self):
        return self.__img_link

    def _assert_load(self, propname):
        if not self.loaded():
            raise Exception('use property "{}" before loading'.format(propname))

    def __str__(self):
        s_basic = '<url="{}", loaded={}'.format(self.url, self.loaded())
        if not self.loaded():
            return s_basic + '>'
        s_all   = s_basic + ', img_link="{}">'.format(self.img_link())
        return s_all

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.url))

if __name__ == '__main__':
    log.setDebugLevel(log.DEBUG)
    s = BingWallpaperPage('http://www.bing.com')
    _logger.debug(repr(s))
    _logger.debug(str(s))
    s.load()
    _logger.debug(str(s))
    if s.img_link():
        with open('w.jpg', 'wb') as of:
            of.write(webutil.loadurl(s.img_link()))
    else:
        _logger('bad luck, no wallpaper today :(')
