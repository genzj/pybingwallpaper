# PyBingWallpaper

### What pybingwallpaper does

Download the wallpaper offered by [*Bing.com*](www.bing.com) and set it 
current wallpaper background.

Another project for the same purpose but download from National Geographic can 
be found [here](https://github.com/genzj/pyngwallpaper)

----------

### Auto startup

#### Windows

Download installer from [releases page](https://github.com/genzj/pybingwallpaper/releases) and install it.

<p>**Note: Please backup the `settings.conf` under the installation path before upgrading!**</p>
<p>**注意：建议升级前备份安装目录下的`settings.conf`文件！**</p>


A shortcut will be created in your startup folder. You can edit the configuration to adjust features.

#### Linux with Gnome
You just need to add a startup application:

    gnome-session-properties

then *add* a startup program with:

    Name: pybingwallpaper
    Command: python3 /path/to/pybingwallpaper/src/main.py -b
    Comment: download and update wallpaper!

You can also append arguments in *Command* box.


----------

### Usage
    usage: pybingwallpaper [-h] [-v] [--config-file CONFIG_FILE]
                           [--generate-config] [-b] [--foreground]
                           [-c {au,br,ca,cn,de,fr,jp,nz,us,uk,auto}]
                           [--market MARKET] [-d] [-i INTERVAL] [-k]
                           [-m {prefer,collect,highest,insist,manual,never}]
                           [--collect COLLECT] [--image-size IMAGE_SIZE]
                           [-o OFFSET] [--proxy-server PROXY_SERVER]
                           [--proxy-port PROXY_PORT]
                           [--proxy-username PROXY_USERNAME]
                           [--proxy-password PROXY_PASSWORD] [--redownload]
                           [-s {no,win,gnome2,gnome3}] [--setter-args SETTER_ARGS]
                           [-t OUTPUT_FOLDER] [--database-file DATABASE_FILE]
                           [--database-no-image] [--server {global,china,custom}]
                           [--custom-server CUSTOMSERVER]

    Download the wallpaper offered by Bing.com and set it current wallpaper
    background.

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show version information
      --config-file CONFIG_FILE
                            'specify configuration file, use `settings.conf` in
                            installation directory by default.
      --generate-config     generate a configuration file containing arguments
                            specified in command line and exit. to generate
                            default config file, issue without other command
                            arguments. path and name of configuration file can be
                            specified with --config-file
      -b, --background      work in background (daemon mode) and check wallpaper
                            periodically (interval can be set by --interval).
      --foreground          force working in foreground mode to cancel the effect
                            of `background` in config file.
      -c {au,br,ca,cn,de,fr,jp,nz,us,uk,auto}, --country {au,br,ca,cn,de,fr,jp,nz,us
    ,uk,auto}
                            select country code sent to bing.com. bing.com in
                            different countries may show different backgrounds.
                            au: Australia br: Brazil ca: Canada cn: China
                            de:Germany fr: France jp: Japan nz: New Zealand us:
                            USA uk: United Kingdom auto: select country according
                            to your IP address (by Bing.com) Note: only China(cn),
                            New Zealand(nz) and USA(us) have high resolution
                            (1920x1200) wallpapers; the rest offer 1366x768 only.
      --market MARKET       specify market from which the wallpaper should be
                            downloaded. Market is a more generic way to specify
                            language-country of bing.com. The list of markets may
                            grow sometimes, and different language of the same
                            country may have different image, so consider using it
                            instead of country. Market code should be specified in
                            format 'xy-ab' such as en-us. Note: specify this
                            parameter will override any settings to --country.
      -d, --debug           enable debug outputs. The more --debug the more
                            detailed the log will be
      -i INTERVAL, --interval INTERVAL
                            interval between each two wallpaper checkings in unit
                            of hours. applicable only in `background` mode. at
                            lease 1 hour; 2 hours by default.
      -k, --keep-file-name  keep the original filename. By default downloaded file
                            will be renamed as 'wallpaper.jpg'. Keep file name
                            will retain all downloaded photos
      -m {prefer,collect,highest,insist,manual,never}, --size-mode {prefer,collect,h
    ighest,insist,manual,never}
                            set selecting strategy when wallpapers in different
                            size are available (normally 1920x1200 and 1366x768).
                            `prefer` (default) uses high resolution if it's
                            available, otherwise downloads normal resolution;
                            `insist` always use high resolution and ignore other
                            pictures (Note: some countries have only normal size
                            wallpapers, if `insist` is adopted with those sites,
                            no wallpaper can be downloaded, see `--country` for
                            more); `highest` use the highest available resolution,
                            that is, 1920x1200 for HD sites, 1920x1080 for others;
                            `never` always use normal resolution; `manual` use
                            resolution specified in `--image-size` `collect` is
                            obsolete and only kept for backward compatibility,
                            equals highest mode together with --collect=accompany
                            option.
      --collect COLLECT     items to be collected besides main wallpaper, can be
                            assigned more than once in CLI or as comma separated
                            list from config file. currently `accompany`, `video`
                            and `hdvideo` are supported. `accompany` - some
                            markets (i.e. en-ww) offers two wallpapers every day
                            with same image but different Bing logo (English and
                            Chinese respectively). enables this will download both
                            original wallpaper and its accompanyings. `video` -
                            bing sometimes (not everyday) release interesting
                            animated mp4 background, use this to collect them.
                            `hdvideo` - HD version of video.
      --image-size IMAGE_SIZE
                            specify resolution of image to download. check
                            `--size-mode` for more
      -o OFFSET, --offset OFFSET
                            start downloading from the photo of 'N' days ago.
                            specify 0 to download photo of today.
      --proxy-server PROXY_SERVER
                            proxy server url, ex: http://10.1.1.1
      --proxy-port PROXY_PORT
                            port of proxy server, default: 80
      --proxy-username PROXY_USERNAME
                            optional username for proxy server authentication
      --proxy-password PROXY_PASSWORD
                            optional password for proxy server authentication
      --redownload          do not check history records. Download must be done.
                            downloaded picture will still be recorded in history
                            file.
      -s {no,win,gnome2,gnome3}, --setter {no,win,gnome2,gnome3}
                            specify interface to be called for setting wallpaper.
                            'no' indicates downloading-only; 'gnome2/3' are only
                            for Linux with gnome; 'win' is for Windows only.
                            Customized setter can be added as dev doc described.
                            Default: win for win32, gnome3 for Linux
      --setter-args SETTER_ARGS
                            arguments for external setters
      -t OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                            specify the folder to store photos. Use
                            '~/MyBingWallpapers' folder in Linux, 'C:/Documents
                            and Settings/<your-username>/MyBingWallpapers in
                            Windows XP or 'C:/Users/<your-
                            username>/MyBingWallpapers' in Windows 7 by default
      --database-file DATABASE_FILE
                            specify the sqlite3 database used to store meta info
                            of photos. leave it blank to disable database storage.
      --database-no-image   images will be embedded into database by default.
                            Exclude images from database can reduce the size of
                            database file.
      --server {global,china,custom}
                            select bing server used for meta data and wallpaper
                            pictures. it seems bing.com uses different servers and
                            domain names in china. global: use bing.com of course.
                            china: use s.cn.bing.net. (note: use this may freeze
                            market or country to China zh-CN) custom: use the
                            server specified in option "customserver"
      --custom-server CUSTOMSERVER
                            specify server used for meta data and wallpaper photo.
                            you need to set --server to 'custom' to enable the
                            custom server address.
----------

### Release Note

* **2019-04-30 1.5.5**
    * Compatible with Bing's new URL format (accompany pictures this time, #55 #56)
    
* **2019-03-15 1.5.4**
    * Compatible with Bing's new URL format

* **2016-04-06 1.5.1**
    * Minor bug fix for Python 3.5 (#43)
    * Obsolete 1.5.0 due to MS Windows Defender raise (false) alarm on the
      installer (#44)

* **2015-12-08 1.5.0**
    * Can collect video now! (#34)
    * Decouple collect mode from market setting (#35)
    * Better compatibility with win 8 and higher (#31 and #40)
    * Avoid deleting collected wallpaper at uninstallation (#33)

* **2014-09-08 1.4.4**
    * Support configurable bing server address (#27)

* **2014-04-18 1.4.4b01**
    * Support download records database (#18), you can build you own bing album now. 

* **2013-12-24 1.4.3**
    * Fix #13 enhance robustness of network connection status: retry in
      60 seconds after network failure 
    * Fix #14 download image with Chinese logo whenever a 1920x1200 picture is
      downloaded: add a collect mode, read 
      [use collect mode](https://github.com/genzj/pybingwallpaper/wiki/Use-collect-mode) 
      [使用收集模式](https://github.com/genzj/pybingwallpaper/wiki/%E4%BD%BF%E7%94%A8%E6%94%B6%E9%9B%86%E6%A8%A1%E5%BC%8F)
      for more
    * Fix #15 use n=1 instead of n=10 for more backtracking room: change
      default n to 1
    * Fix #16 can't read settings.conf when run out of installation dir: read
      settings.conf from the same path of main.py by default

* **2013-12-24 1.4.2**
    * Support http/https proxy.
    Read
    [配置指南](https://github.com/genzj/pybingwallpaper/wiki/%E5%A6%82%E4%BD%95%E9%85%8D%E7%BD%AE%E4%BB%A3%E7%90%86%E6%A8%A1%E5%BC%8F) 
    [Proxy guidance](https://github.com/genzj/pybingwallpaper/wiki/How-to-use-pybingwallpaper-with-proxy) 
    for details.

* **2013-12-21 1.4.1**
    * Background mode bugfix

* **2013-12-21 1.4.0**
    * Use configuration file;
    * Support specify market
    * Support manually set picture resolution
    * Support downloading 1920x1080 images for pages without wallpaper link

* **2013-09-24 1.3.0**
    * supports high resolution wallpapers
    * change default checking interval to 2 hours
    * obsolete option `-f` and `--persistence`
    * fix none type error when offset exceeds boundary issue #2
    * fix none type error when download picture fails issue #3
