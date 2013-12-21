# PyBingWallpaper

### What pybingwallpaper does

Download the wallpaper offered by [*Bing.com*](www.bing.com) and set it 
current wallpaper background.

Another project for the same purpose but download from National Geographic can 
be found [here](https://github.com/genzj/pyngwallpaper)

----------

### Auto startup

#### Linux with Gnome
You just need to add a startup application:

    gnome-session-properties

then *add* a startup program with:

    Name: pybingwallpaper
    Command: /path/to/pybingwallpaper/src/main.py
    Comment: download and update wallpaper!

You can also append arguments in *Command* box.

#### Windows

Download installer [from dropbox](https://www.dropbox.com/s/tszcm0dac1tn70y/pybingwp-1-4-0.exe) 
or from [Baidu Disk(百度盘)](http://pan.baidu.com/s/1bnaMORt) 
and install it. A shortcut will be created in your startup folder. 

You can edit the configuration to adjust features.

----------

### Usage

    usage: pybingwallpaper [-h] [-v] [--config-file CONFIG_FILE]
                           [--generate-config] [-b] [--foreground]
                           [-c {au,br,ca,cn,de,fr,jp,nz,us,uk,auto}]
                           [--market MARKET] [-d] [-i INTERVAL] [-k]
                           [-m {prefer,highest,insist,manual,never}]
                           [--image-size IMAGE_SIZE] [-o OFFSET] [--redownload]
                           [-s {no,win}] [--setter-args SETTER_ARGS]
                           [-t OUTPUT_FOLDER]
    
    Download the wallpaper offered by Bing.com and set it current wallpaper
    background.
    
    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show version information
      --config-file CONFIG_FILE
                            specify configuration file
      --generate-config     generate a configuration file containing arguments
                            specified in command line and exit. to generate
                            default config file, issue without other command
                            arguments. path and name of configuration file can be
                            specified with --config-file
      -b, --background      work in background (daemon mode) and check wallpaper
                            periodically (interval can be set by --interval).
      --foreground          force working in foreground mode to cancel the effect
                            of `background` in config file.
      -c {au,br,ca,cn,de,fr,jp,nz,us,uk,auto}, --country {au,br,ca,cn,de,fr,jp,nz,us,uk,auto}
                            select country code sent to bing.com. bing.com in
                            different countries may show different backgrounds.
                            au: Australia br: Brazil ca: Canada cn: China
                            de:Germany fr: France jp: Japan nz: Netherland us: USA
                            uk: United Kingdom auto: select country according to
                            your IP address (by Bing.com) Note: only China(cn),
                            Netherland(nz) and USA(us) have high resolution
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
      -m {prefer,highest,insist,manual,never}, --size-mode {prefer,highest,insist,manual,never}
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
                            resolution specified in `--image-size`
      --image-size IMAGE_SIZE
                            specify resolution of image to download. check
                            `--size-mode` for more
      -o OFFSET, --offset OFFSET
                            start downloading from the photo of 'N' days ago.
                            specify 0 to download photo of today.
      --redownload          do not check history records. Download must be done.
                            downloaded picture will still be recorded in history
                            file.
      -s {no,win,gnome2,gnome3}, --setter {no,win,gnome2,gnome3}
                            specify interface to be called for setting wallpaper.
                            'no' indicates downloading-only; 'gnome2/3' are only
                            for Linux with gnome; 'win' is for Windows only.
                            Customized setter can be added as dev doc described.
                            Default: win
      --setter-args SETTER_ARGS
                            arguments for external setters
      -t OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                            specify the folder to store photos. Use
                            '~/MyBingWallpapers' folder in Linux, 'C:/Documents
                            and Settings/<your-username>/MyBingWallpapers in
                            Windows XP or 'C:/Users/<your-
                            username>/MyBingWallpapers' in Windows 7 by default
    

----------

### Devolopment

#### Customized wallpaper setter
(TBD)

----------

### Release Note
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
