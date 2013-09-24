#!/usr/bin/env python3
import re
import log
import webutil
import json

_logger = log.getChild('bingwallpaper')

def _property_need_loading(f):
    def wrapper(*args, **kwargs):
        args[0]._assert_load(f.__name__)
        return f(*args, **kwargs)
    return wrapper

class BingWallpaperPage:
    BASE_URL='http://www.bing.com'
    IMAGE_API='/HPImageArchive.aspx?format=js&idx={idx}&n={n}'
    def __init__(self, idx, n=1, base=BASE_URL, api=IMAGE_API, filter_wp=True, country_code=None):
        self.update(idx, n, base, api, filter_wp, country_code)

    def update(self, idx, n=1, base=BASE_URL, api=IMAGE_API, filter_wp=True, country_code=None):
        self.base = base
        self.api = api
        self.filter_wp = filter_wp
        self.reset()
        self.url = webutil.urljoin(self.base, self.api.format(idx=idx, n=n))
        self.country_code = country_code
        if country_code:
            self.url = '&'.join([self.url, 'cc={}'.format(country_code)])

    def reset(self):
        self.__loaded = False
        self.content = ''
        self.__img_link = None
        self.discovered = 0
        self.filtered = 0

    def _is_wp(self, image, filtermode='auto'):
        if filtermode not in ('auto', 'strict'):
            raise ValueError('Unknown filtermode {}'.format(str(filtermode)))
        self.discovered += 1
        url = image['url']
        if image['wp']: 
            _logger.debug('wp flag of %s is True, keep it', url)
            return True
        elif filtermode == 'auto':
            # also guess from its resolution
            resolution = re.search(r'(\d+)x(\d+)', url)
            if resolution and int(resolution.groups()[0]) > 1024:
                _logger.debug('guess %s is in %s, could be a wallpaper', url, resolution.groups())
                return True
        else:
            _logger.info('%s is not for wallpaper, try force option if you want to keep it', 
                        url)
            self.filtered += 1
            return False

    def _parse(self, rawfile):
        try:
            self.content = json.loads(rawfile)
        except Exception as ex:
            _logger.exception(ex)
            return False

        # including blank response or 'null' in json
        if not self.content: return False
        
        _logger.debug(self.content)

        if self.filter_wp:
            self.__images = list(filter(self._is_wp, self.content['images']))
        else:
            self.__images = self.content['images']
        self._update_img_link()

        return True

    def _update_img_link(self):
        for i in self.__images:
            i['url'] = webutil.urljoin(self.base, i['url'])

    def load(self):
        self.reset()
        _logger.info('loading from %s', self.url)
        rawfile = webutil.loadpage(self.url)
        
        if rawfile:
            _logger.info('%d bytes loaded', len(rawfile))
            self.__loaded = self._parse(rawfile)
        else:
            _logger.error('can\'t download photo page')

    def loaded(self):
        return self.__loaded

    @_property_need_loading
    def images(self):
        return self.__images
    
    @_property_need_loading
    def image_links(self):
        return [i['url'] for i in self.images()]

    def _assert_load(self, propname):
        if not self.loaded():
            raise Exception('use property "{}" before loading'.format(propname))

    def __str__(self):
        s_basic = '<url="{}", loaded={}'.format(self.url, self.loaded())
        if not self.loaded():
            return s_basic + '>'
        s_all   = s_basic + ', images="{}">'.format(self.images())
        return s_all

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.url))

if __name__ == '__main__':
    log.setDebugLevel(log.DEBUG)
    s = BingWallpaperPage(0, 4)
    _logger.debug(repr(s))
    _logger.debug(str(s))
    s.load()
    _logger.debug(str(s))
    for i in s.images():
        l = i['url']
        with open(i['urlbase'].rpartition('/')[2]+'.jpg', 'wb') as of:
            of.write(webutil.loadurl(l))
