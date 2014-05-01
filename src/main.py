#!/usr/bin/env python3
from sys import argv, exit as sysexit, platform
import os
from os.path import expanduser, join as pathjoin, isfile, isdir, splitext
from os.path import basename, dirname, abspath
import log
import webutil
import bingwallpaper
import record
import setter
import sched
import config

NAME = 'pybingwallpaper'
REV  = '1.4.4'
LINK = 'https://github.com/genzj/pybingwallpaper'
HISTORY_FILE = pathjoin(expanduser('~'), 'bing-wallpaper-history.json')

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

    configdb = config.ConfigDatabase(prog=NAME, 
            description='Download the wallpaper offered by Bing.com '
            +'and set it current wallpaper background.')
    
    params.append(config.ConfigParameter('version',
            help='show version information',
            loader_srcs=['cli'],
            loader_opts={'cli':{
                'flags':('-v', '--version'),
                'action': 'version',
                'version':'%(prog)s-{} ({})'.format(REV, LINK),
                }}
            ))

    params.append(config.ConfigParameter('config_file',
            defaults = pathjoin(get_app_path(), 'settings.conf'),
            help=''''specify configuration file, use `settings.conf`
                in installation directory by default.''',
            loader_srcs=['cli', 'defload'],
            loader_opts={'cli':{
                'flags':('--config-file',),
                }}
            ))

    params.append(config.ConfigParameter('generate_config',
            defaults=False,
            help='''generate a configuration file containing arguments
            specified in command line and exit. to generate default config
            file, issue without other command arguments.
            path and name of configuration file can be specified with
            --config-file''',
            loader_srcs=['cli', 'defload'],
            loader_opts={'cli':{
                'flags':('--generate-config',),
                'action':'store_true'
                }}
            ))

    params.append(config.ConfigParameter('background',
            defaults=False,
            help='''work in background (daemon mode) and check
            wallpaper periodically (interval can be set by --interval).''',
            loader_opts={'cli':{
                'flags':('-b', '--background'),
                'action':'store_true',
                }, 'conffile':{
                'section':'Daemon',
                'converter':config.str_to_bool,
                }}
            ))

    params.append(config.ConfigParameter('foreground',
            defaults=False,
            help='''force working in foreground mode to cancel 
            the effect of `background` in config file.''',
            loader_srcs=['cli', 'defload'],
            loader_opts={'cli':{
                'flags':('--foreground',),
                'action':'store_true'
                }}
            ))

    params.append(config.ConfigParameter('country', defaults='auto',
            choices=('au', 'br', 'ca', 'cn', 'de', 'fr', 'jp', 'nz', 'us', 'uk', 'auto'), 
            help='''select country code sent to bing.com.
            bing.com in different countries may show different
            backgrounds. 
            au: Australia  br: Brazil  ca: Canada  cn: China  de:Germany
            fr: France  jp: Japan  nz: New Zealand  us: USA  uk: United Kingdom
            auto: select country according to your IP address (by Bing.com)
            Note: only China(cn), New Zealand(nz) and USA(us) have
            high resolution (1920x1200) wallpapers; the rest offer 1366x768 only.''',
            loader_opts={'cli':{
                'flags':('-c', '--country'),
                }, 'conffile':{
                'section':'Download',
                }}
            ))
    params.append(config.ConfigParameter('market', defaults='',
            help='''specify market from which the wallpaper should be downloaded.
            Market is a more generic way to specify language-country of bing.com.
            The list of markets may grow sometimes, and different language of the
            same country may have different image, so consider using it instead of
            country. Market code should be specified in format 'xy-ab' such as en-us.
            Note: specify this parameter will override any settings to --country.
            ''',
            loader_opts={'cli':{
                'flags':('--market',),
                }, 'conffile':{
                'section':'Download',
                }}
            ))
    params.append(config.ConfigParameter('debug', defaults=0,
            help='''enable debug outputs. 
            The more --debug the more detailed the log will be''',
            loader_opts={'cli':{
                'flags':('-d', '--debug'),
                'action':'count',
                }, 'conffile': {
                'converter':int,
                'section':'Debug',
                }}
            ))
    def convert_interval(interval):
        i = int(interval)
        return i if i >=1 else 1

    params.append(config.ConfigParameter('interval',
            type=convert_interval, defaults=2,
            help='''interval between each two wallpaper checkings 
                    in unit of hours. applicable only in `background` mode.
                    at lease 1 hour; 2 hours by default.''',
            loader_opts={'cli':{
                'flags':('-i', '--interval'),
                }, 'conffile':{
                'section':'Daemon',
                }}
            ))
    params.append(config.ConfigParameter('keep_file_name', defaults=False,
            help='''keep the original filename. By default
            downloaded file will be renamed as 'wallpaper.jpg'.
            Keep file name will retain all downloaded photos
            ''',
            loader_opts={'cli':{
                'flags':('-k', '--keep-file-name'),
                'action':'store_true',
                }, 'conffile':{
                'section':'Download',
                'converter':config.str_to_bool,
                }}
            ))

    params.append(config.ConfigParameter('size_mode', defaults='prefer',
            choices=('prefer', 'collect', 'highest', 'insist', 'manual', 'never'),
            help='''set selecting strategy when wallpapers in different 
                    size are available (normally 1920x1200 and 1366x768).
                    `prefer` (default) uses high resolution if it's 
                    available, otherwise downloads normal resolution;
                    `insist` always use high resolution and ignore 
                    other pictures (Note: some countries have only
                    normal size wallpapers, if `insist` is adopted
                    with those sites, no wallpaper can be downloaded,
                    see `--country` for more);
                    `highest` use the highest available resolution, that
                    is, 1920x1200 for HD sites, 1920x1080 for others;
                    `never` always use normal resolution;
                    `manual` use resolution specified in `--image-size`
                    `collect` acts exactly as highest in most of cases, 
                    however it will also download the picture with Chinese
                    bing logo if the picture is ROW and in the size of 1920x1200
                    (try --market=en-ww). In collect mode, only the first
                    picture (usually the one with English bing logo) 
                    will be set as wallpaper.''',
            loader_opts={'cli':{
                'flags':('-m', '--size-mode'),
                }, 'conffile':{
                'section':'Download',
                }}
            ))
    params.append(config.ConfigParameter('image_size', defaults='',
            help='''specify resolution of image to download. check
                    `--size-mode` for more''',
            loader_opts={'cli':{
                'flags':('--image-size',),
                }, 'conffile':{
                'section':'Download',
                }}
            ))
    params.append(config.ConfigParameter('offset', type=int, defaults='0',
            help='''start downloading from the photo of 'N' days ago.
                    specify 0 to download photo of today.''',
            loader_opts={'cli':{
                'flags':('-o', '--offset'),
                }, 'conffile':{
                'section':'Download',
                }}
            ))
    params.append(config.ConfigParameter('proxy_server', defaults='',
            help='''proxy server url, ex: http://10.1.1.1''',
            loader_opts={'cli':{
                'flags':('--proxy-server',),
                }, 'conffile':{
                'section':'Proxy',
                }}
            ))
    params.append(config.ConfigParameter('proxy_port', defaults='80',
            help='''port of proxy server, default: 80''',
            loader_opts={'cli':{
                'flags':('--proxy-port',),
                }, 'conffile':{
                'section':'Proxy',
                }}
            ))
    params.append(config.ConfigParameter('proxy_username', defaults='',
            help='''optional username for proxy server authentication''',
            loader_opts={'cli':{
                'flags':('--proxy-username',),
                }, 'conffile':{
                'section':'Proxy',
                }}
            ))
    params.append(config.ConfigParameter('proxy_password', defaults='',
            help='''optional password for proxy server authentication''',
            loader_opts={'cli':{
                'flags':('--proxy-password',),
                }, 'conffile':{
                'section':'Proxy',
                }}
            ))
    params.append(config.ConfigParameter('redownload', defaults=False,
            help='''do not check history records. Download
                    must be done. downloaded picture will still
                    be recorded in history file.
            ''',
            loader_opts={'cli':{
                'action':'store_true',
                }, 'conffile':{
                'section':'Download',
                'converter':config.str_to_bool
                }}
            ))
    params.append(config.ConfigParameter('setter', choices=setters,
            defaults=setters[1],
            help='''specify interface to be called for
                    setting wallpaper. 'no'
                    indicates downloading-only; 'gnome2/3'
                    are only for Linux with gnome; 'win' is
                    for Windows only. Customized setter can
                    be added as dev doc described. Default: {}
            '''.format(setters[1]),
            loader_opts={'cli':{
                'flags':('-s', '--setter'),
                }, 'conffile':{
                'section':'Setter',
                }}
            ))

    params.append(config.ConfigParameter('setter_args', defaults=[],
            help='''arguments for external setters''',
            loader_opts={'cli':{
                'flags':('--setter-args',),
                'action':'append',
                }, 'conffile':{
                'formatter':lambda args: ','.join(args),
                'section':'Setter',
                }}
            ))

    params.append(config.ConfigParameter('output_folder',
            defaults=pathjoin(expanduser('~'), 'MyBingWallpapers'),
            help='''specify the folder to store photos.
                    Use '~/MyBingWallpapers' folder in Linux, 
                    'C:/Documents and Settings/<your-username>/MyBingWallpapers 
                    in Windows XP or 'C:/Users/<your-username>/MyBingWallpapers' 
                    in Windows 7 by default
                ''',
            loader_opts={'cli':{
                'flags':('-t', '--output-folder'),
                }, 'conffile':{
                'section':'Download',
                }}
            ))

    params.append(config.ConfigParameter('database_file',
            defaults='',
            help='''specify the sqlite3 database used to store meta info of photos.
                    leave it blank to disable database storage.
                ''',
            loader_opts={'cli':{
                'flags':('--database-file',),
                }, 'conffile':{
                'section':'Database',
                }}
            ))

    params.append(config.ConfigParameter('database_no_image',
            defaults=False,
            help='''images will be embedded into database by default. Exclude
                    images from database can reduce the size of database file.
                ''',
            loader_opts={'cli':{
                'flags':('--database-no-image',),
                'action':'store_false',
                }, 'conffile':{
                'section':'Database',
                'converter':config.str_to_bool
                }}
            ))
    for p in params:
        configdb.add_param(p)
    return configdb

def prepare_output_dir(d):
    os.makedirs(d, exist_ok=True)
    if isdir(d):
        return True
    else:
        _logger.critical('can not create output folder %s', d)

def download_wallpaper(run_config):
    records = list()
    idx = run_config.offset
    country_code = None if run_config.country == 'auto' else run_config.country
    market_code = None if not run_config.market else run_config.market
    try:
        s = bingwallpaper.BingWallpaperPage(idx, 
                country_code = country_code,
                market_code = market_code,
                high_resolution = bingwallpaper.HighResolutionSetting.getByName(
                    run_config.size_mode
                    ),
                resolution = run_config.image_size
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
    for wplinks, info in s.image_links():
        _logger.info('%s photo list: %s', info, wplinks)
        mainlink = wplinks[0]
        outfile = get_output_filename(run_config, mainlink)
        rec = record.default_manager.get_by_url(mainlink)
        _logger.debug('%s', rec)

        if outfile == rec['local_file']:
            if not run_config.redownload:
                _logger.info('file has been downloaded before, exit')
                return None
            else:
                _logger.info('file has been downloaded before, redownload it')

        _logger.info('download photo of "%s"', info)
        raw = save_a_picture(mainlink, info, outfile)
        if not raw: continue
        r = record.DownloadRecord(mainlink, outfile, info,
                                    raw=None if run_config.database_no_image else raw)
        records.append(r)
        collect_accompanying_pictures(wplinks[1:], info, run_config.output_folder, records)
        return records
        
    _logger.info('bad luck, no wallpaper today:(')
    return None

def collect_accompanying_pictures(wplinks, info, output_folder, records):
    for link in wplinks:
        filename = pathjoin(output_folder, basename(link))
        _logger.info('download accompanying photo of "%s" from %s to %s', 
                        info, link, output_folder)
        raw = save_a_picture(link, info, filename)
        if raw:
            r = record.DownloadRecord(link, filename, info,
                                        raw=None if run_config.database_no_image else raw,
                                        is_accompany=True)
            records.append(r)

def save_a_picture(pic_url, info, outfile):
    picture_content = webutil.loadurl(pic_url)
    if picture_content:
        with open(outfile, 'wb') as of:
            of.write(picture_content)
            _logger.info('file saved %s', outfile)
    return picture_content

def get_output_filename(run_config, link):
    filename = basename(link)
    if not run_config.keep_file_name:
        filename = 'wallpaper{}'.format(splitext(filename)[1])
    return pathjoin(run_config.output_folder, filename)

def load_history():
    try:
        f = open(HISTORY_FILE, 'r')
    except FileNotFoundError:
        _logger.info('{} not found, ignore download history'.format(HISTORY_FILE))        
    except Exception:
        _logger.warning('error occurs when recover downloading history', exc_info=1)
    else:
        record.default_manager.load(f)
        f.close()

def save_history(records, keepold=False):
    last_record = records[0]
    if not keepold:
        record.default_manager.clear()
    record.default_manager.add(last_record)
    try:
        f = open(HISTORY_FILE, 'w')
        f.truncate(0)
    except Exception:
        _logger.warning('error occurs when store downloading history',
                        exc_info=1)
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
        _logger.error('error occurs when store records into database %s', run_config.database_file,
                        exc_info=1)

def set_debug_details(level):
    if not level:
        l = log.INFO
    elif level == 1:
        l = log.DEBUG
    elif level >= 2:
        l = log.PAGEDUMP
    log.setDebugLevel(l)

def main(daemon=None):
    if daemon: _logger.info('daemon %s triggers an update', str(daemon))
    # reload config again in case the config file has been modified after
    #last shooting
    configdb = prepare_config_db()
    run_config = load_config(configdb)
    setter.load_ext_setters(dirname(abspath(argv[0])))

    prepare_output_dir(run_config.output_folder)

    load_history()
    install_proxy(run_config)
    try:
        filerecords = download_wallpaper(run_config)
    except CannotLoadImagePage:
        if not run_config.foreground and run_config.background and daemon:
            _logger.info("network error happened, daemon will retry in 60 seconds")
            timeout = 60
        else:
            _logger.info("network error happened. please retry after Internet connection restore.")
        filerecords = None
    else:
        timeout = run_config.interval*3600

    if filerecords:
        save_history(filerecords)
    if not filerecords or run_config.setter == 'no':
        _logger.info('nothing to set')
    else:
        s = setter.get(run_config.setter)()
        # use the first image as wallpaper, accompanying images are just
        # to fulfill your collection
        wallpaper_record = filerecords[0]
        _logger.info('setting wallpaper %s', wallpaper_record['local_file'])
        s.set(wallpaper_record['local_file'], run_config.setter_args)
        _logger.info('all done. enjoy your new wallpaper')

    if not run_config.foreground and run_config.background and daemon:
        schedule_next_poll(timeout, daemon)
    elif run_config.foreground:
        _logger.info('force foreground mode from command line')

def schedule_next_poll(timeout, daemon):
    if not daemon:
        _logger.error('no scheduler')
    else:
        _logger.debug('schedule next running in %d seconds', run_config.interval*3600)
        daemon.enter(timeout, 1, main, (daemon, ))

def start_daemon():
    daemon = sched.scheduler()
    
    main(daemon)
    _logger.info('daemon %s is running', str(daemon))
    daemon.run()
    _logger.info('daemon %s exited', str(daemon))

def load_config(configdb, args = None):
    args = argv[1:] if args is None else args
    set_debug_details(args.count('--debug')+args.count('-d'))

    default_config = config.DefaultValueLoader().load(configdb)
    _logger.debug('default config:\n\t%s', config.pretty(default_config, '\n\t'))

    # parse cli options at first because we need the config file path in it
    cli_config = config.CommandLineArgumentsLoader().load(configdb, argv[1:])
    _logger.debug('cli arg parsed:\n\t%s', config.pretty(cli_config, '\n\t'))
    run_config = config.merge_config(default_config, cli_config)

    if run_config.generate_config:
        generate_config_file(configdb, run_config)

    config_file = run_config.config_file
    if not isfile(config_file):
        _logger.warning("can't find config file %s, use default settings and cli settings",
                config_file)
    else:
        try:
            conf_config = config.from_file(configdb, run_config.config_file)
        except config.ConfigFileLoader.ConfigValueError as err:
            _logger.error(err)
            sysexit(1)

        _logger.debug('config file parsed:\n\t%s', config.pretty(conf_config, '\n\t'))
        run_config = config.merge_config(run_config, conf_config)

    # override saved settings again with cli options again, because we want
    # command line options to take higher priority
    run_config = config.merge_config(run_config, cli_config)
    if run_config.setter_args:
        run_config.setter_args = ','.join(run_config.setter_args).split(',')
    else:
        run_config.setter_args = list()
    _logger.info('running config is:\n\t%s', config.pretty(run_config, '\n\t'))
    return run_config

def save_config(configdb, run_config, filename=None):
    filename = run_config.config_file if not filename else filename
    config.to_file(configdb, run_config, filename)

def generate_config_file(configdb, config_content):
    filename = config_content.config_file
    _logger.info('save following config to file %s:\n\t%s', 
            filename, 
            config.pretty(config_content, '\n\t'))
    save_config(configdb, config_content, filename)
    sysexit(0)

def install_proxy(config):
    from itertools import product
    if not config.proxy_server:
        _logger.debug('no proxy server specified')
        return
    else:
        if len(config.proxy_password) <= 4:
            hidden_password = '*'*len(config.proxy_password)
        else:
            hidden_password = '%s%s%s'%(config.proxy_password[0], 
                                        '*'*(len(config.proxy_password)-2), 
                                        config.proxy_password[-1])
        _logger.info('user specified proxy: "%s:%s"', config.proxy_server, config.proxy_port)
        _logger.debug('proxy username: "%s" password: "%s"', config.proxy_username, hidden_password)
    PROXY_SITES_PROTOCOL = ('http', 'https')
    PROXY_SITES = ('bing.com', 'www.bing.com', 'cn.bing.com', 'nz.bing.com')

    proxy_sites = [p+'://'+s for p, s in product(('http', 'https'), PROXY_SITES)]
    webutil.setup_proxy(PROXY_SITES_PROTOCOL, config.proxy_server, config.proxy_port, 
                            proxy_sites, config.proxy_username, config.proxy_password)

def get_app_path(appfile=None):
    appfile = appfile if appfile else argv[0]
    apppath = dirname(appfile)
    apppath = '.' if not apppath else apppath
    oldpath = abspath(os.curdir)
    os.chdir(apppath)
    apppath = abspath(os.curdir)
    os.chdir(oldpath)
    return os.path.normcase(apppath)


if __name__ == '__main__':
    configdb = prepare_config_db()
    run_config = load_config(configdb)
    set_debug_details(run_config.debug)
    if not run_config.foreground and run_config.background:
        start_daemon()
    else:
        main(None)
    sysexit(0)
