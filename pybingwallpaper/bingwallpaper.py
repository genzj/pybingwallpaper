#!/usr/bin/env python3
import json
import re

from datetime import datetime

from . import log
from . import webutil

_logger = log.getChild('bingwallpaper')


def _property_need_loading(f):
    def wrapper(*args, **kwargs):
        args[0]._assert_load(f.__name__)
        return f(*args, **kwargs)

    return wrapper


class HighResolutionSetting:
    settings = dict()

    def get_pic_url(self, rooturl, imgurlbase, fallbackurl, has_wp, resolution):
        raise NotImplementedError()

    @staticmethod
    def get_by_name(name):
        if name not in HighResolutionSetting.settings:
            raise ValueError('{} is not a legal resolution setting'.format(name))
        return HighResolutionSetting.settings[name]


class UHDResolution(HighResolutionSetting):
    def get_pic_url(self, rooturl, imgurlbase, fallbackurl, has_wp, resolution):
        wplink = webutil.urljoin(rooturl, '_'.join([imgurlbase, 'UHD.jpg']))
        _logger.debug('in UHD mode, get url %s', wplink)
        return wplink,


class PreferHighResolution(HighResolutionSetting):
    def get_pic_url(self, rooturl, imgurlbase, fallbackurl, has_wp, resolution):
        resolutions = ['UHD', '1920x1200', '1920x1080', ]
        candidates = [
            webutil.urljoin(rooturl, '_'.join([imgurlbase, suffix + '.jpg']))
            for suffix in resolutions
        ]
        for url in candidates:
            _logger.debug('in prefer mode, detect existence of pic %s', url)
            if webutil.test_header(url):
                _logger.debug('in prefer mode, decided url: %s', url)
                return url,
        return webutil.urljoin(rooturl, fallbackurl),


class InsistHighResolution(HighResolutionSetting):
    def get_pic_url(self, rooturl, imgurlbase, fallbackurl, has_wp, resolution):
        if has_wp:
            wplink = webutil.urljoin(rooturl, '_'.join([imgurlbase, '1920x1200.jpg']))
            _logger.debug('in insist mode, get high resolution url %s', wplink)
        else:
            wplink = None
            _logger.debug('in insist mode, drop normal resolution pic')
        return wplink,


class NeverHighResolution(HighResolutionSetting):
    def get_pic_url(self, rooturl, imgurlbase, fallbackurl, has_wp, resolution):
        wplink = webutil.urljoin(rooturl, fallbackurl)
        _logger.debug('never use high resolution, use %s', wplink)
        return wplink,


class HighestResolution(HighResolutionSetting):
    def get_pic_url(self, rooturl, imgurlbase, fallbackurl, has_wp, resolution):
        if has_wp:
            wplink = webutil.urljoin(rooturl, '_'.join([imgurlbase, '1920x1200.jpg']))
            _logger.debug('support wallpaper, get high resolution url %s', wplink)
        else:
            wplink = webutil.urljoin(rooturl, '_'.join([imgurlbase, '1920x1080.jpg']))
            _logger.debug('not support wallpaper, use second highest resolution %s', wplink)
        return wplink,


class ManualHighResolution(HighResolutionSetting):
    def get_pic_url(self, rooturl, imgurlbase, fallbackurl, has_wp, resolution):
        if not re.match(r'\d+x\d+', resolution):
            _logger.error('invalid resolution "%s" for manual mode', resolution)
            raise ValueError('invalid resolution "%s"' % (resolution,))
        wplink = webutil.urljoin(rooturl, ''.join([imgurlbase, '_', resolution, '.jpg']))
        _logger.debug('manually specify resolution, use %s', wplink)
        return wplink,


HighResolutionSetting.settings['uhd'] = UHDResolution
HighResolutionSetting.settings['prefer'] = PreferHighResolution
HighResolutionSetting.settings['insist'] = InsistHighResolution
HighResolutionSetting.settings['never'] = NeverHighResolution
HighResolutionSetting.settings['highest'] = PreferHighResolution
HighResolutionSetting.settings['manual'] = ManualHighResolution


class AssetCollector:
    __registered_collectors = dict()

    @classmethod
    def register(cls, name, collector):
        if name in cls.__registered_collectors:
            raise Exception(
                'collector {!s} has been registered by {!r}'.format(
                    name, cls.__registered_collectors[name]
                )
            )
        cls.__registered_collectors[name] = collector

    @classmethod
    def get(cls, name, *init_args, **init_kwargs):
        if name not in cls.__registered_collectors:
            _logger.warning('collector %s is not supported', name)
            # return a blank collect
            return AssetCollector()
        return cls.__registered_collectors[name](*init_args, **init_kwargs)

    def collect(self, rooturl, curimage):
        return None


class AccompanyImageCollector(AssetCollector):
    def collect(self, rooturl, curimage):
        img_url_base = curimage['urlbase']
        has_wp = curimage.get('wp', False)
        if has_wp and '_ZH_' not in img_url_base:
            _logger.debug('%s may have a Chinese brother', img_url_base)
            zh_link = [webutil.urljoin(rooturl, '_'.join([img_url_base, 'ZH_1920x1200.jpg'])), ]
        else:
            _logger.debug('no chinese logo for %s', img_url_base)
            zh_link = None
        return zh_link


class VideoCollector(AssetCollector):
    def collect(self, rooturl, curimage):
        vlink = list()
        if 'vid' not in curimage:
            return None
        for video_format, _, video_url in curimage['vid']['sources']:
            if video_format.endswith('hd'):
                continue
            elif video_url.startswith('//'):
                video_url = 'http:' + video_url
            vlink.append(video_url)
        return vlink


class HdVideoCollector(AssetCollector):
    def collect(self, rooturl, curimage):
        vlink = list()
        if 'vid' not in curimage:
            return None
        for video_format, _, video_url in curimage['vid']['sources']:
            if not video_format.endswith('hd'):
                continue
            elif video_url.startswith('//'):
                video_url = 'http:' + video_url
            vlink.append(video_url)
        return vlink


AssetCollector.register('accompany', AccompanyImageCollector)
AssetCollector.register('video', VideoCollector)
AssetCollector.register('hdvideo', HdVideoCollector)


class BingWallpaperPage:
    BASE_URL = 'http://www.bing.com'
    IMAGE_API = '/HPImageArchive.aspx?format=js&mbl=1&idx={idx}&n={n}&video=1'

    def __init__(self, idx, n=1, base=BASE_URL, api=IMAGE_API, country_code=None,
                 market_code=None, high_resolution=PreferHighResolution, resolution='1920x1200',
                 collect=None):
        self.idx = idx
        self.n = n
        self.base = base
        self.api = api
        self.reset()
        self.url = webutil.urljoin(self.base, self.api.format(idx=idx, n=n))
        self.country_code = country_code
        self.market_code = market_code
        self.high_resolution = high_resolution
        self.resolution = resolution
        self.collect = collect or []
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

    def _parse(self, raw_file):
        try:
            self.content = json.loads(raw_file)
        except Exception as ex:
            _logger.exception(ex)
            return False

        # including blank response or 'null' in json
        if not self.content:
            return False

        _logger.debug(self.content)

        self.__images = self.content['images']
        if 'market' in self.content and 'mkt' in self.content['market']:
            self.act_market = self.content['market']['mkt']
        self._update_img_link()

        _logger.warning('links to be downloaded: %s', self.wplinks)

        return True

    def _get_metadata(self, i):
        metadata = dict()
        meta_field = [
            'copyright', 'copyrightlink', 'hsh'
        ]
        for f in meta_field:
            metadata[f] = i.get(f, None)
        metadata['market'] = self.act_market
        metadata['startdate'] = datetime.strptime(i['startdate'], '%Y%m%d').date()
        metadata['enddate'] = datetime.strptime(i['enddate'], '%Y%m%d').date()
        metadata['fullstartdate'] = datetime.strptime(i['fullstartdate'], '%Y%m%d%H%M')

        return metadata

    def _update_img_link(self):
        del self.wplinks[:]
        for i in self.__images:
            metadata = self._get_metadata(i)
            has_wp = i.get('wp', False)
            _logger.debug(
                'handling %s, rooturl=%s, img_url_base=%s, has_wp=%s, resolution=%s, act_market=%s',
                i['url'], self.base, i['urlbase'], has_wp, self.resolution, self.act_market
            )
            wplink = self.high_resolution().get_pic_url(self.base, i['urlbase'], i['url'], has_wp, self.resolution)
            collections = list()
            for collector_name in self.collect:
                asset = AssetCollector.get(collector_name).collect(self.base, i)
                if asset:
                    collections += asset
            if wplink:
                self.wplinks.append((wplink + tuple(collections), metadata))

    def load(self):
        self.reset()
        _logger.info('loading from %s', self.url)
        raw_file = webutil.loadpage(self.url)

        if raw_file:
            _logger.info('%d bytes loaded', len(raw_file))
            self.__loaded = self._parse(raw_file)
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

    def _assert_load(self, attr):
        if not self.loaded():
            raise Exception('use property "{}" before loading'.format(attr))

    def __str__(self):
        s_basic = '<url="{}", loaded={}'.format(self.url, self.loaded())
        if not self.loaded():
            return s_basic + '>'
        s_all = s_basic + ', images="{}">'.format(self.images())
        return s_all

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, repr(self.url))

    @staticmethod
    def validate_market(market_code):
        #
        if not re.match(r'\w\w-\w\w', market_code):
            raise ValueError('%s is not a valid market code.' % (market_code,))
        return True
