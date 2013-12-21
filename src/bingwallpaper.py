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

class HighResolutionSetting:
    settings = dict()
    def getPicUrl(self, rooturl, imgurlbase, fallbackurl, has_wp, *args, **kwargs):
        raise NotImplementedError()

    @staticmethod
    def getByName(name):
        if name not in HighResolutionSetting.settings:
            raise ValueError('{} is not a legal resolution setting'.format(name))
        return HighResolutionSetting.settings[name]

class PreferHighResolution(HighResolutionSetting):
    def getPicUrl(self, rooturl, imgurlbase, fallbackurl, has_wp, *args, **kwargs):
        if has_wp:
            wplink = webutil.urljoin(rooturl, '_'.join([imgurlbase,'1920x1200.jpg'])) 
            _logger.debug('in prefer mode, get high resolution url %s', wplink)
        else:
            wplink = webutil.urljoin(rooturl, fallbackurl)
            _logger.debug('in prefer mode, get normal resolution url %s', wplink)
        return wplink

class InsistHighResolution(HighResolutionSetting):
    def getPicUrl(self, rooturl, imgurlbase, fallbackurl, has_wp, *args, **kwargs):
        if has_wp:
            wplink = webutil.urljoin(rooturl, '_'.join([imgurlbase,'1920x1200.jpg'])) 
            _logger.debug('in insist mode, get high resolution url %s', wplink)
        else:
            wplink = None
            _logger.debug('in insist mode, drop normal resolution pic')
        return wplink

class NeverHighResolution(HighResolutionSetting):
    def getPicUrl(self, rooturl, imgurlbase, fallbackurl, has_wp, *args, **kwargs):
        wplink = webutil.urljoin(rooturl, fallbackurl)
        _logger.debug('never use high resolution, use %s', wplink)
        return wplink

class HighestResolution(HighResolutionSetting):
    def getPicUrl(self, rooturl, imgurlbase, fallbackurl, has_wp, *args, **kwargs):
        if has_wp:
            wplink = webutil.urljoin(rooturl, '_'.join([imgurlbase,'1920x1200.jpg'])) 
            _logger.debug('support wallpaper, get high resolution url %s', wplink)
        else:
            wplink = webutil.urljoin(rooturl, '_'.join([imgurlbase,'1920x1080.jpg'])) 
            _logger.debug('not support wallpaper, use second highest resolution %s', wplink)
        return wplink

class ManualHighResolution(HighResolutionSetting):
    def getPicUrl(self, rooturl, imgurlbase, fallbackurl, has_wp, resolution):
        if not re.match(r'\d+x\d+', resolution):
            _logger.error('invalid resolution "%s" for manual mode', resolution)
            raise ValueError('invalid resolution "%s"'%(resolution, ))
        wplink = webutil.urljoin(rooturl, ''.join([imgurlbase, '_', resolution, '.jpg'])) 
        _logger.debug('manually specify resolution, use %s', wplink)
        return wplink

HighResolutionSetting.settings['prefer'] = PreferHighResolution
HighResolutionSetting.settings['insist'] = InsistHighResolution
HighResolutionSetting.settings['never'] = NeverHighResolution
HighResolutionSetting.settings['highest'] = HighestResolution
HighResolutionSetting.settings['manual'] = ManualHighResolution

class BingWallpaperPage:
    BASE_URL='http://www.bing.com'
    IMAGE_API='/HPImageArchive.aspx?format=js&idx={idx}&n={n}'
    def __init__(self, idx, n=10, base=BASE_URL, api=IMAGE_API, country_code=None, 
                market_code=None, high_resolution = PreferHighResolution, resolution='1920x1200'):
        self.base = base
        self.api = api
        self.reset()
        self.url = webutil.urljoin(self.base, self.api.format(idx=idx, n=n))
        self.country_code = country_code
        self.market_code = market_code
        self.high_resolution = high_resolution
        self.resolution = resolution
        if market_code:
            BingWallpaperPage.validate_market(market_code)
            self.url = '&'.join([self.url, 'mkt={}'.format(market_code)])
        elif country_code:
            self.url = '&'.join([self.url, 'cc={}'.format(country_code)])

    def reset(self):
        self.__loaded = False
        self.content = ''
        self.__img_link = None
        self.discovered = 0
        self.filtered = 0
        self.wplinks = []

    def _parse(self, rawfile):
        try:
            self.content = json.loads(rawfile)
        except Exception as ex:
            _logger.exception(ex)
            return False

        # including blank response or 'null' in json
        if not self.content: return False
        
        _logger.debug(self.content)

        self.__images = self.content['images']
        self._update_img_link()

        return True

    def _update_img_link(self):
        self.wplinks.clear()
        for i in self.__images:
            has_wp = i.get('wp', False)
            _logger.debug('handling %s, rooturl=%s, imgurlbase=%s, has_wp=%s, resolution=%s', 
                        i['url'], self.base, i['urlbase'], has_wp, self.resolution)
            wplink = self.high_resolution().getPicUrl(self.base, i['urlbase'], i['url'], has_wp, self.resolution)
            if wplink: self.wplinks.append((wplink, i['copyright']))

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
        return self.wplinks

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
    
    @staticmethod
    def validate_market(market_code):
        #
        if not re.match(r'\w\w-\w\w', market_code):
            raise ValueError('%s is not a valid market code.'%(market_code,))
        return True

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
