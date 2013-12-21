#!/usr/bin/env python3
from sys import argv, exit as sysexit, platform
import os
from os.path import expanduser, join as pathjoin, isdir, splitext
from os.path import basename, dirname, abspath
import log
import webutil
import bingwallpaper
import record
import setter
import sched
import config

NAME = 'pybingwallpaper'
REV  = '1.4.0'
LINK = 'https://github.com/genzj/pybingwallpaper'
HISTORY_FILE = pathjoin(expanduser('~'), 'bing-wallpaper-history.json')

_logger = log.getChild('main')

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

    #TODO need to generate configuration path according to program path
    params.append(config.ConfigParameter('config_file',
            defaults = 'settings.conf',
            help='specify configuration file',
            loader_srcs=['cli', 'defload'],
            loader_opts={'cli':{
                'flags':('--config-file',),
                }}
            ))

    params.append(config.ConfigParameter('generate_config',
            defaults=False,
            help='''generate a configuration file with default configuration
            and exit. path and name of configuration file can be specified with
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
    params.append(config.ConfigParameter('country', defaults='auto',
            choices=('au', 'br', 'ca', 'cn', 'de', 'fr', 'jp', 'nz', 'us', 'uk', 'auto'), 
            help='''select country code sent to bing.com.
            bing.com in different countries may show different
            backgrounds. 
            au: Australia  br: Brazil  ca: Canada  cn: China  de:Germany
            fr: France  jp: Japan  nz: Netherland  us: USA  uk: United Kingdom
            auto: select country according to your IP address (by Bing.com)
            Note: only China(cn), Netherland(nz) and USA(us) have
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
            choices=('prefer', 'highest', 'insist', 'manual', 'never'),
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
                    `manual` use resolution specified in `--image-size`''',
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
        _logger.fatal('can not load url %s. aborting...', s.url)
        return None
    for wplink, info in s.image_links():
        if wplink:
            outfile = get_output_filename(run_config, wplink)
            rec = record.default_manager.get(wplink, None)

            if rec and outfile == rec['local_file']:
                if not run_config.redownload:
                    _logger.info('file has been downloaded before, exit')
                    return None
                else:
                    _logger.info('file has been downloaded before, redownload it')

            _logger.info('download photo of "%s"', info)
            picture_content = webutil.loadurl(wplink)
            if picture_content:
                with open(outfile, 'wb') as of:
                    of.write(picture_content)
                    _logger.info('file saved %s', outfile)
                r = record.DownloadRecord(wplink, outfile)
                return r
        _logger.debug('no wallpaper, try next')
        
    if s.filtered > 0:
        _logger.info('%d picture(s) filtered, try again with -f option if you want them',
                     s.filtered)
    _logger.info('bad luck, no wallpaper today:(')
    return None

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

def save_history(r, keepold=False):
    if not keepold:
        record.default_manager.clear()
    record.default_manager.add(r)
    try:
        f = open(HISTORY_FILE, 'w')
        f.truncate(0)
    except Exception:
        _logger.warning('error occurs when store downloading history',
                        exc_info=1)
    else:
        record.default_manager.save(f)
        f.close()

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
    filerecord = download_wallpaper(run_config)

    if filerecord:
        save_history(filerecord)
    if not filerecord or run_config.setter == 'no':
        _logger.info('nothing to set')
    else:
        s = setter.get(run_config.setter)()
        _logger.info('setting wallpaper %s', filerecord['local_file'])
        s.set(filerecord['local_file'], run_config.setter_args)
        _logger.info('all done. enjoy your new wallpaper')

    if daemon: schedule_next_poll(run_config, daemon)

def schedule_next_poll(run_config, daemon):
    if run_config.background and daemon:
        _logger.debug('schedule next running in %d seconds', run_config.interval*3600)
        daemon.enter(run_config.interval*3600, 1, main, (run_config, daemon))
    elif not run_config.background:
        _logger.error('not in daemon mode')
    elif not daemon:
        _logger.error('no scheduler')

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
    _logger.info('default config:\n\t%s', config.pretty(default_config, '\n\t'))

    # parse cli options at first because we need the config file path in it
    cli_config = config.CommandLineArgumentsLoader().load(configdb, argv[1:])
    _logger.info('cli arg parsed:\n\t%s', config.pretty(cli_config, '\n\t'))
    run_config = config.merge_config(default_config, cli_config)

    if run_config.generate_config:
        generate_default_config(configdb, run_config.config_file)

    try:
        conf_config = config.from_file(configdb, run_config.config_file)
    except config.ConfigFileLoader.ConfigValueError as err:
        _logger.error(err)
        sysexit(1)

    _logger.info('config file parsed:\n\t%s', config.pretty(conf_config, '\n\t'))
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

def generate_default_config(configdb, filename):
    default_config = config.DefaultValueLoader().load(configdb)
    _logger.info('save default config to file %s:\n\t%s', 
            filename, 
            config.pretty(default_config, '\n\t'))
    save_config(configdb, default_config, filename)
    sysexit(0)

if __name__ == '__main__':
    configdb = prepare_config_db()
    run_config = load_config(configdb)
    set_debug_details(run_config.debug)
    if run_config.background:
        start_daemon()
    else:
        main(None)
    sysexit(0)
