#!/usr/bin/env python3
import errno
import os
import sched
from datetime import datetime
from os.path import basename, dirname, abspath
from os.path import expanduser, join as path_join, isfile, isdir, splitext
from sys import argv, exit as sys_exit, platform

from . import bingwallpaper
from . import config
from . import log
from . import record
from . import setter
from . import webutil
from .rev import REV
from .webutil import urlparse, parse_qs

NAME = 'pybingwallpaper'
LINK = 'https://github.com/genzj/pybingwallpaper'

if platform == 'win32':
    HISTORY_FILE = path_join(
        os.getenv('APPDATA', expanduser('~')),
        'Genzj',
        'PyBingWallpaper',
        'bing-wallpaper-history.json'
    )
else:
    HISTORY_FILE = path_join(expanduser('~'), '.bing-wallpaper-history.json')

_logger = log.getChild('main')


class CannotLoadImagePage(Exception):
    pass


def load_setters():
    if platform == 'win32':
        return ['no', 'win']
    else:
        return ['no', 'gnome3', 'gnome2']


def prepare_config_db():
    params = []

    setters = load_setters()

    configdb = config.ConfigDatabase(
        prog=NAME,
        description='Download the wallpaper offered by Bing.com '
                    + 'and set it current wallpaper background.'
    )

    params.append(config.ConfigParameter(
        'version',
        help='show version information',
        loader_srcs=['cli'],
        loader_opts={'cli': {
            'flags': ('-v', '--version'),
            'action': 'version',
            'version': '%(prog)s-{} ({})'.format(REV, LINK),
        }}
    ))

    params.append(config.ConfigParameter(
        'config_file',
        defaults=path_join(get_app_path(), 'settings.conf'),
        help=''''specify configuration file, use `settings.conf`
                in installation directory by default.''',
        loader_srcs=['cli', 'defload'],
        loader_opts={'cli': {
            'flags': ('--config-file',),
        }}
    ))

    params.append(config.ConfigParameter(
        'generate_config',
        defaults=False,
        help='''generate a configuration file containing arguments
            specified in command line and exit. to generate default config
            file, issue without other command arguments.
            path and name of configuration file can be specified with
            --config-file''',
        loader_srcs=['cli', 'defload'],
        loader_opts={'cli': {
            'flags': ('--generate-config',),
            'action': 'store_true'
        }}
    ))

    params.append(config.ConfigParameter(
        'background',
        defaults=False,
        help='''work in background (daemon mode) and check
            wallpaper periodically (interval can be set by --interval).''',
        loader_opts={'cli': {
            'flags': ('-b', '--background'),
            'action': 'store_true',
        }, 'conffile': {
            'section': 'Daemon',
            'converter': config.str_to_bool,
        }}
    ))

    params.append(config.ConfigParameter(
        'foreground',
        defaults=False,
        help='''force working in foreground mode to cancel
            the effect of `background` in config file.''',
        loader_srcs=['cli', 'defload'],
        loader_opts={'cli': {
            'flags': ('--foreground',),
            'action': 'store_true'
        }}
    ))

    params.append(config.ConfigParameter(
        'country', defaults='auto',
        choices=('au', 'br', 'ca', 'cn', 'de', 'fr', 'jp', 'nz', 'us', 'uk', 'auto'),
        help='''
            (Obsolete, use --market instead)
            select country code used to access bing.com API.
            au: Australia  br: Brazil  ca: Canada  cn: China  de:Germany
            fr: France  jp: Japan  nz: New Zealand  us: USA  uk: United Kingdom
            auto: select country according to your IP address (by Bing.com)
            Note: only China(cn), New Zealand(nz) and USA(us) have
            high resolution (1920x1200) wallpapers; the rest offer 1366x768 only.''',
        loader_opts={'cli': {
            'flags': ('-c', '--country'),
        }, 'conffile': {
            'section': 'Download',
        }}
    ))
    params.append(config.ConfigParameter(
        'market', defaults='',
        help='''specify region from which the wallpaper should be downloaded.
            Market code should be specified in format 'xy-ab' such as en-us.
            Use '--list-markets' to view all available markets.
            Note: specify this parameter will override any settings to --country.
            ''',
        loader_opts={'cli': {
            'flags': ('--market',),
        }, 'conffile': {
            'section': 'Download',
        }}
    ))
    params.append(config.ConfigParameter(
        'list_markets',
        defaults=False,
        help='''list all available values for the --market option and exit''',
        loader_srcs=['cli', 'defload'],
        loader_opts={'cli': {
            'flags': ('--list-markets',),
            'action': 'store_true'
        }}
    ))
    params.append(config.ConfigParameter(
        'debug', defaults=0,
        help='''enable debug outputs.
            The more --debug the more detailed the log will be''',
        loader_opts={'cli': {
            'flags': ('-d', '--debug'),
            'action': 'count',
        }, 'conffile': {
            'converter': int,
            'section': 'Debug',
        }}
    ))

    def convert_interval(interval):
        i = int(interval)
        return i if i >= 1 else 1

    params.append(config.ConfigParameter(
        'interval',
        type=convert_interval, defaults=2,
        help='''interval between each two wallpaper checkings
                    in unit of hours. applicable only in `background` mode.
                    at lease 1 hour; 2 hours by default.''',
        loader_opts={'cli': {
            'flags': ('-i', '--interval'),
        }, 'conffile': {
            'section': 'Daemon',
        }}
    ))
    params.append(config.ConfigParameter(
        'keep_file_name', defaults=False,
        help='''keep the original filename. By default
            downloaded file will be renamed as 'wallpaper.jpg'.
            Keep file name will retain all downloaded photos
            ''',
        loader_opts={'cli': {
            'flags': ('-k', '--keep-file-name'),
            'action': 'store_true',
        }, 'conffile': {
            'section': 'Download',
            'converter': config.str_to_bool,
        }}
    ))

    params.append(config.ConfigParameter(
        'size_mode', defaults='prefer',
        choices=('prefer', 'collect', 'highest', 'insist', 'manual', 'never', 'uhd'),
        help='''set selecting strategy when wallpapers in different
                    size are available (4K, 1920x1200, 1920x1080 and 1366x768).
                    `prefer` (default) detect and download the highest
                    available resolution;
                    `insist` always use 1920x1200 resolution and ignore
                    other pictures (Note: some countries have only
                    normal size wallpapers, if `insist` is adopted
                    with those sites, no wallpaper can be downloaded,
                    see `--country` for more);
                    `highest` is an alias of `prefer`
                    `never` always use normal resolution (1366x768);
                    `manual` use resolution specified in `--image-size`
                    `collect` is obsolete and only kept for backward
                    compatibility, equals `prefer` mode together with
                    --collect=accompany option.
                    `uhd` insists using 4K resolution, or abort wallpaper
                    downloading if it's not available.
                    ''',
        loader_opts={'cli': {
            'flags': ('-m', '--size-mode'),
        }, 'conffile': {
            'section': 'Download',
        }}
    ))

    params.append(config.ConfigParameter(
        'collect', defaults=[],
        help='''items to be collected besides main wallpaper, can be assigned
            more than once in CLI or as comma separated list from config file.
            currently `accompany`, `video` and `hdvideo` are supported.
            `accompany` - some markets (i.e. en-ww) offers two wallpapers
            every day with same image but different Bing logo (English and
            Chinese respectively). enables this will download both original
            wallpaper and its accompanyings.
            `video` - bing sometimes (not everyday) release interesting
            animated mp4 background, use this to collect them.
            `hdvideo` - HD version of video.''',
        loader_opts={'cli': {
            'flags': ('--collect',),
            'action': 'append',
        }, 'conffile': {
            'formatter': lambda args: ','.join(args),
            'converter': lambda arg: [_p.strip() for _p in arg.split(',') if
                                      _p.strip()],
            'section': 'Download',
        }}
    ))

    params.append(config.ConfigParameter(
        'image_size', defaults='',
        help='''specify resolution of image to download. check
                    `--size-mode` for more''',
        loader_opts={'cli': {
            'flags': ('--image-size',),
        }, 'conffile': {
            'section': 'Download',
        }}
    ))
    params.append(config.ConfigParameter(
        'offset', type=int, defaults='0',
        help='''start downloading from the photo of 'N' days ago.
                    specify 0 to download photo of today.''',
        loader_opts={'cli': {
            'flags': ('-o', '--offset'),
        }, 'conffile': {
            'section': 'Download',
        }}
    ))
    params.append(config.ConfigParameter(
        'proxy_server', defaults='',
        help='''proxy server value, ex: http://10.1.1.1''',
        loader_opts={'cli': {
            'flags': ('--proxy-server',),
        }, 'conffile': {
            'section': 'Proxy',
        }}
    ))
    params.append(config.ConfigParameter(
        'proxy_port', defaults='80',
        help='''port of proxy server, default: 80''',
        loader_opts={'cli': {
            'flags': ('--proxy-port',),
        }, 'conffile': {
            'section': 'Proxy',
        }}
    ))
    params.append(config.ConfigParameter(
        'proxy_username', defaults='',
        help='''optional username for proxy server authentication''',
        loader_opts={'cli': {
            'flags': ('--proxy-username',),
        }, 'conffile': {
            'section': 'Proxy',
        }}
    ))
    params.append(config.ConfigParameter(
        'proxy_password', defaults='',
        help='''optional password for proxy server authentication''',
        loader_opts={'cli': {
            'flags': ('--proxy-password',),
        }, 'conffile': {
            'section': 'Proxy',
        }}
    ))
    params.append(config.ConfigParameter(
        'redownload', defaults=False,
        help='''do not check history records. Download
                    must be done. downloaded picture will still
                    be recorded in history file.
            ''',
        loader_opts={'cli': {
            'action': 'store_true',
        }, 'conffile': {
            'section': 'Download',
            'converter': config.str_to_bool
        }}
    ))
    params.append(config.ConfigParameter(
        'setter', choices=setters,
        defaults=setters[1],
        help='''specify interface to be called for
                    setting wallpaper. 'no'
                    indicates downloading-only; 'gnome2/3'
                    are only for Linux with gnome; 'win' is
                    for Windows only. Customized setter can
                    be added as dev doc described. Default: {}
            '''.format(setters[1]),
        loader_opts={'cli': {
            'flags': ('-s', '--setter'),
        }, 'conffile': {
            'section': 'Setter',
        }}
    ))

    params.append(config.ConfigParameter(
        'setter_args', defaults=[],
        help='''arguments for external setters''',
        loader_opts={'cli': {
            'flags': ('--setter-args',),
            'action': 'append',
        }, 'conffile': {
            'formatter': lambda args: ','.join(args),
            'section': 'Setter',
        }}
    ))

    params.append(config.ConfigParameter(
        'output_folder',
        defaults=path_join(expanduser('~'), 'MyBingWallpapers'),
        help='''specify the folder to store photos.
                    Use '~/MyBingWallpapers' folder in Linux,
                    'C:/Documents and Settings/<your-username>/MyBingWallpapers
                    in Windows XP or 'C:/Users/<your-username>/MyBingWallpapers'
                    in Windows 7 by default
                ''',
        loader_opts={'cli': {
            'flags': ('-t', '--output-folder'),
        }, 'conffile': {
            'section': 'Download',
        }}
    ))

    params.append(config.ConfigParameter(
        'database_file',
        defaults='',
        help='''specify the sqlite3 database used to store meta info of photos.
                    leave it blank to disable database storage.
                ''',
        loader_opts={'cli': {
            'flags': ('--database-file',),
        }, 'conffile': {
            'section': 'Database',
        }}
    ))

    params.append(config.ConfigParameter(
        'database_no_image',
        defaults=False,
        help='''images will be embedded into database by default. Exclude
                    images from database can reduce the size of database file.
                ''',
        loader_opts={'cli': {
            'flags': ('--database-no-image',),
            'action': 'store_false',
        }, 'conffile': {
            'section': 'Database',
            'converter': config.str_to_bool
        }}
    ))

    params.append(config.ConfigParameter(
        'server', defaults='global',
        choices=('global', 'china', 'custom'),
        help='''select bing server used for meta data
            and wallpaper pictures. it seems bing.com uses different
            servers and domain names in china.
            global: use bing.com of course.
            china:  use s.cn.bing.net. (note: use this may freeze market
                    or country to China zh-CN)
            custom: use the server specified in option "customserver"
            ''',
        loader_opts={'cli': {
            'flags': ('--server',),
        }, 'conffile': {
            'section': 'Download',
        }}
    ))

    def url(s):
        from .webutil import urlparse
        value = ('http://' + s) \
            if s and not urlparse(s).scheme \
            else s
        return value + '/' if value and not value.endswith('/') else value

    params.append(config.ConfigParameter('customserver', defaults='',
                                         type=url,
                                         help='''specify server used for meta data and wallpaper photo.
            you need to set --server to 'custom' to enable the custom server
            address.''',
                                         loader_opts={'cli': {
                                             'flags': ('--custom-server',),
                                         }, 'conffile': {
                                             'section': 'Download',
                                         }}
                                         ))

    for p in params:
        configdb.add_param(p)
    return configdb


def makedirs(d):
    try:
        os.makedirs(d)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def prepare_output_dir(d):
    makedirs(d)
    if isdir(d):
        return True
    else:
        _logger.critical('can not create output folder %s', d)
    if os.access(d, os.W_OK | os.R_OK):
        return True
    else:
        _logger.critical('can not access output folder %s', d)


def download_wallpaper(run_config):
    records = list()
    idx = run_config.offset
    country_code = None if run_config.country == 'auto' else run_config.country
    market_code = None if not run_config.market else run_config.market
    if run_config.server == 'global':
        base_url = 'http://www.bing.com'
    elif run_config.server == 'china':
        base_url = 'http://s.cn.bing.net'
    else:
        base_url = run_config.customserver

    try:
        s = bingwallpaper.BingWallpaperPage(
            idx,
            base=base_url,
            country_code=country_code,
            market_code=market_code,
            high_resolution=bingwallpaper.HighResolutionSetting.get_by_name(
                run_config.size_mode
            ),
            resolution=run_config.image_size,
            collect=set(run_config.collect)
        )
        _logger.debug(repr(s))
        s.load()
        _logger.log(log.PAGEDUMP, str(s))
    except Exception:
        _logger.fatal('error happened during loading from bing.com.', exc_info=1)
        return None

    if not s.loaded():
        _logger.error('can not load url %s. aborting...', s.url)
        raise CannotLoadImagePage(s)
    for wplinks, metadata in s.image_links():
        _logger.debug('%s photo list: %s', metadata, wplinks)
        mainlink = wplinks[0]
        copyright_ = metadata['copyright']
        outfile = get_output_filename(run_config, mainlink)
        rec = record.default_manager.get_by_url(mainlink)
        _logger.debug('related download records: %s', rec)

        if outfile == rec['local_file']:
            if not run_config.redownload:
                _logger.info('file has been downloaded before, exit')
                return None
            else:
                _logger.info('file has been downloaded before, redownload it')

        _logger.info('download photo of "%s"', copyright_)
        raw = save_a_picture(mainlink, copyright_, outfile)
        if not raw:
            continue
        r = record.DownloadRecord(
            mainlink, outfile, copyright_,
            raw=None if run_config.database_no_image else raw,
            market=metadata['market'],
            start_time=metadata['fullstartdate'],
            end_time=metadata['enddate'],
        )
        records.append(r)
        collect_assets(wplinks[1:], metadata, run_config, records)
        return records

    _logger.info('bad luck, no wallpaper today:(')
    return None


def collect_assets(wplinks, metadata, run_config, records):
    output_folder = run_config.output_folder
    copyright_ = metadata['copyright']
    market = metadata['market']
    for link in wplinks:
        _logger.debug(
            'downloading assets of "%s" from %s to %s',
            copyright_, link, output_folder
        )
        filename = get_output_filename(run_config, link)
        raw = save_a_picture(link, copyright_, filename, optional=True)
        if not raw:
            continue
        elif filename.endswith('jpg'):
            r = record.DownloadRecord(
                link, filename, copyright_,
                raw=None if run_config.database_no_image else raw,
                is_accompany=True, market=market
            )
            records.append(r)
        _logger.info('assets "%s" of "%s" has been downloaded to %s',
                     link, copyright_, output_folder)


def save_a_picture(pic_url, _, outfile, optional=False):
    picture_content = webutil.loadurl(pic_url, optional=optional)
    if picture_content:
        with open(outfile, 'wb') as of:
            of.write(picture_content)
            _logger.info('file saved %s', outfile)
    return picture_content


def get_output_filename(run_config, link):
    link = urlparse(link)
    filename = basename(link.path)
    if filename == 'th':
        # 2019-03 new url style encoding filename in url parameters
        filename = parse_qs(link.query).get(
            'id',
            [datetime.now().strftime('bingwallpaper_%Y-%m-%d_%H%M%S.jpg'), ]
        )[0]
    if not run_config.keep_file_name:
        filename = 'wallpaper{}'.format(splitext(filename)[1])
    return path_join(run_config.output_folder, filename)


def load_history():
    try:
        f = open(HISTORY_FILE, 'r')
    except IOError as ex:
        if ex.errno == errno.ENOENT:
            _logger.info('{} not found, ignore download history'.format(HISTORY_FILE))
        else:
            _logger.warning('error occurs when recover downloading history', exc_info=1)
    except Exception:
        _logger.warning('error occurs when recover downloading history', exc_info=1)
    else:
        record.default_manager.load(f)
        f.close()


def save_history(records, run_config, keepold=False):
    last_record = records[0]
    if not keepold:
        record.default_manager.clear()
    record.default_manager.add(last_record)
    try:
        f = open(HISTORY_FILE, 'w')
        f.truncate(0)
    except Exception:
        _logger.warning(
            'error occurs when store downloading history',
            exc_info=1
        )
    else:
        record.default_manager.save(f)
        f.close()

    if not run_config.database_file:
        return

    rm = record.SqlDatabaseRecordManager('database %s' % (run_config.database_file,))
    for r in records:
        rm.add(r)

    try:
        rm.save(run_config.database_file)
    except Exception:
        _logger.error(
            'error occurs when store records into database %s',
            run_config.database_file,
            exc_info=1
        )


def set_debug_details(level_number):
    if not level_number:
        level = log.INFO
    elif level_number == 1:
        level = log.DEBUG
    elif level_number >= 2:
        level = log.PAGEDUMP
    else:
        level = log.INFO
    log.setDebugLevel(level)


def start(daemon=None):
    if daemon:
        _logger.info('daemon %s triggers an update', str(daemon))

    # reload config again in case the config file has been modified after
    # last shooting
    config_db = prepare_config_db()
    run_config = load_config(config_db)
    setter.load_ext_setters(dirname(abspath(argv[0])))

    prepare_output_dir(run_config.output_folder)
    prepare_output_dir(dirname(HISTORY_FILE))

    load_history()
    install_proxy(run_config)
    try:
        file_records = download_wallpaper(run_config)
    except CannotLoadImagePage:
        if not run_config.foreground and run_config.background and daemon:
            _logger.info("network error happened, daemon will retry in 60 seconds")
            timeout = 60
        else:
            _logger.info("network error happened. please retry after Internet connection restore.")
            timeout = None
        file_records = None
    else:
        timeout = run_config.interval * 3600

    if file_records:
        save_history(file_records, run_config)
    if not file_records or run_config.setter == 'no':
        _logger.info('nothing to set')
    else:
        s = setter.get(run_config.setter)()
        # use the first image as wallpaper, accompanying images are just
        # to fulfill your collection
        wallpaper_record = file_records[0]
        _logger.info('setting wallpaper %s', wallpaper_record['local_file'])
        s.set(wallpaper_record['local_file'], run_config.setter_args)
        _logger.info('all done. enjoy your new wallpaper')

    if not run_config.foreground and run_config.background and daemon:
        schedule_next_poll(timeout, daemon, run_config.interval)
    elif run_config.foreground:
        _logger.info('force foreground mode from command line')


def schedule_next_poll(timeout, daemon, interval):
    if not daemon:
        _logger.error('no scheduler')
    else:
        _logger.debug('schedule next running in %d seconds', interval * 3600)
        daemon.enter(timeout, 1, start, (daemon,))


def start_daemon():
    daemon = sched.scheduler()

    start(daemon)
    _logger.info('daemon %s is running', str(daemon))
    daemon.run()
    _logger.info('daemon %s exited', str(daemon))


def load_config(config_db, args=None):
    args = argv[1:] if args is None else args
    set_debug_details(args.count('--debug') + args.count('-d'))

    default_config = config.DefaultValueLoader().load(config_db)
    _logger.debug('default config:\n\t%s', config.pretty(default_config, '\n\t'))

    # parse cli options at first because we need the config file path in it
    cli_config = config.CommandLineArgumentsLoader().load(config_db, argv[1:])
    _logger.debug('cli arg parsed:\n\t%s', config.pretty(cli_config, '\n\t'))
    run_config = config.merge_config(default_config, cli_config)

    if run_config.list_markets:
        list_markets()

    if run_config.generate_config:
        generate_config_file(config_db, run_config)

    config_file = run_config.config_file
    if not isfile(config_file):
        _logger.warning("can't find config file %s, use default settings and cli settings",
                        config_file)
    else:
        try:
            conf_config = config.from_file(config_db, run_config.config_file)
        except config.ConfigFileLoader.ConfigValueError as err:
            _logger.error(err)
            sys_exit(1)

        # noinspection PyUnboundLocalVariable
        _logger.debug('config file parsed:\n\t%s', config.pretty(conf_config, '\n\t'))
        run_config = config.merge_config(run_config, conf_config)

    # override saved settings again with cli options again, because we want
    # command line options to take higher priority
    run_config = config.merge_config(run_config, cli_config)
    if run_config.setter_args:
        run_config.setter_args = ','.join(run_config.setter_args).split(',')
    else:
        run_config.setter_args = list()

    # backward compatibility modifications
    if run_config.size_mode == 'collect':
        _logger.warning(
            'size_mode=collect is obsolete, considering use collect=accompany instead'
        )
        run_config.size_mode = 'highest'
        if 'accompany' not in run_config.collect:
            run_config.collect.append('accompany')

    _logger.info('running config is:\n\t%s', config.pretty(run_config, '\n\t'))
    return run_config


def save_config(configdb, run_config, filename=None):
    filename = run_config.config_file if not filename else filename
    config.to_file(configdb, run_config, filename)


def generate_config_file(configdb, config_content):
    filename = config_content.config_file
    _logger.info(
        'save following config to file %s:\n\t%s',
        filename,
        config.pretty(config_content, '\n\t')
    )
    save_config(configdb, config_content, filename)
    sys_exit(0)


def install_proxy(config):
    from itertools import product
    if not config.proxy_server:
        _logger.debug('no proxy server specified')
        return
    else:
        if len(config.proxy_password) <= 4:
            hidden_password = '*' * len(config.proxy_password)
        else:
            hidden_password = '%s%s%s' % (
                config.proxy_password[0],
                '*' * (len(config.proxy_password) - 2),
                config.proxy_password[-1]
            )
        _logger.info('user specified proxy: "%s:%s"', config.proxy_server, config.proxy_port)
        _logger.debug('proxy username: "%s" password: "%s"', config.proxy_username, hidden_password)
    proxy_sites_protocol = ('http', 'https')
    proxy_sites = ('bing.com', 'www.bing.com', 'cn.bing.com', 'nz.bing.com', 's.cn.bing.net')

    proxy_sites = [p + '://' + s for p, s in product(('http', 'https'), proxy_sites)]
    if config.customserver and config.customserver not in proxy_sites:
        proxy_sites += (config.customserver,)
    webutil.setup_proxy(
        proxy_sites_protocol, config.proxy_server, config.proxy_port,
        proxy_sites, config.proxy_username, config.proxy_password
    )


def get_app_path(app_file=None):
    app_file = app_file if app_file else argv[0]
    app_path = dirname(app_file)
    app_path = '.' if not app_path else app_path
    old_path = abspath(os.curdir)
    os.chdir(app_path)
    app_path = abspath(os.curdir)
    os.chdir(old_path)
    return os.path.normcase(app_path)


def list_markets():
    # extracted from Bing Account settings page
    markets = (
        ("es-AR", "Argentina",),
        ("en-AU", "Australia",),
        ("de-AT", "Austria",),
        ("nl-BE", "Belgium - Dutch",),
        ("fr-BE", "Belgium - French",),
        ("pt-BR", "Brazil",),
        ("en-CA", "Canada - English",),
        ("fr-CA", "Canada - French",),
        ("es-CL", "Chile",),
        ("zh-CN", "China",),
        ("da-DK", "Denmark",),
        ("ar-EG", "Egypt",),
        ("fi-FI", "Finland",),
        ("fr-FR", "France",),
        ("de-DE", "Germany",),
        ("zh-HK", "Hong Kong SAR",),
        ("en-IN", "India",),
        ("en-ID", "Indonesia",),
        ("en-IE", "Ireland",),
        ("it-IT", "Italy",),
        ("ja-JP", "Japan",),
        ("ko-KR", "Korea",),
        ("en-MY", "Malaysia",),
        ("es-MX", "Mexico",),
        ("nl-NL", "Netherlands",),
        ("en-NZ", "New Zealand",),
        ("nb-NO", "Norway",),
        ("en-PH", "Philippines",),
        ("pl-PL", "Poland",),
        ("pt-PT", "Portugal",),
        ("ru-RU", "Russia",),
        ("ar-SA", "Saudi Arabia",),
        ("en-SG", "Singapore",),
        ("en-ZA", "South Africa",),
        ("es-ES", "Spain",),
        ("sv-SE", "Sweden",),
        ("fr-CH", "Switzerland - French",),
        ("de-CH", "Switzerland - German",),
        ("zh-TW", "Taiwan",),
        ("tr-TR", "Turkey",),
        ("ar-AE", "United Arab Emirates",),
        ("en-GB", "United Kingdom",),
        ("en-US", "United States - English",),
        ("es-US", "United States - Spanish",),
    )
    print('Available markets:')
    for k, v in markets:
        print(k, '    ', v)
    sys_exit(0)


def main():
    config_db = prepare_config_db()
    run_config = load_config(config_db)
    set_debug_details(run_config.debug)
    if not run_config.foreground and run_config.background:
        start_daemon()
    else:
        start(None)
    return 0


if __name__ == '__main__':
    sys_exit(main())
