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
Download installer [from dropbox](https://www.dropbox.com/s/d839yd57dvxqsrk/pybingwp-1-3-0.exe) 
or from [Baidu Disk(百度盘)](http://pan.baidu.com/s/165Rwl) 
and install it. A shortcut will be created in your startup folder. 

You can also create a shortcut by yourself, or add arguments to it.

----------

### How it works

1.  Retrieve URL and information of images from Bing image API

1.  If there is a wallpaper download link:
    * if both its URL and target file name are same as last downloaded photo's, exit without error
    * download it to **specified** folder
    * record the downloading URL, location of saved photo and downloading time in a text file, which locates in current user's personal folder
    * use it as wallpaper unless in **download-only** mode
    * exit

1. If there isn't a wallpaper link:
    * if the **force** switch is on, do same as step 2
    * try next image

----------

### Usage

    usage: pybingwallpaper [-h] [-v] [-b] [-c {au,ca,cn,de,fr,jp,nz,us,uk}] [-d]
                           [-f] [-i INTERVAL] [-k] [-m {prefer,insist,never}]
                           [-o OFFSET] [--persistence PERSISTENCE] [--redownload]
                           [-s {no,win}] [--setter-args SETTER_ARGS]
                           [-t OUTPUT_FOLDER]
    
    Download the wallpaper offered by Bing.com and set it current wallpaper
    background.
    
    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show version information
      -b, --background      work in background (daemon mode) and check wallpaper
                            periodically (interval can be set by --interval).
      -c {au,br,ca,cn,de,fr,jp,nz,us,uk}, --country {au,br,ca,cn,de,fr,jp,nz,us,uk}
                            select country code sent to bing.com. bing.com in
                            different countries may show different backgrounds.
                            au: Australia br: Brazil ca: Canada cn: China
                            de:Germany fr: France jp: Japan nz: Netherland us: USA
                            uk: United Kingdom Note: only China(cn),
                            Netherland(nz) and USA(us) have high resolution
                            (1920x1200) wallpapers; the rest offer 1366x768 only.
      -d, --debug           enable debug outputs. The more --debug the more
                            detailed the log will be
      -f, --force           obsolete since 1.3.0
      -i INTERVAL, --interval INTERVAL
                            interval between each two wallpaper checkings in unit
                            of hours. applicable only in `background` mode. 2
                            hours by default.
      -k, --keep-file-name  keep the original filename. By default downloaded file
                            will be renamed as 'wallpaper.jpg'. Keep file name
                            will retain all downloaded photos
      -m {prefer,insist,never}, --size-mode {prefer,insist,never}
                            set selecting strategy when wallpapers in different
                            size are available (normally 1920x1200 and 1366x768).
                            `prefer` (default) uses high resolution if it's
                            available, otherwise downloads normal resolution;
                            `insist` always use high resolution and ignore other
                            pictures (Note: some countries have only normal size
                            wallpapers, if `insist` is adopted with those sites,
                            no wallpaper can be downloaded, see `--country` for
                            more); `never` always use normal resolution.
      -o OFFSET, --offset OFFSET
                            start downloading from the photo of 'N' days ago.
                            specify 0 to download photo of today.
      --persistence PERSISTENCE
                            obsolete since 1.3.0
      --redownload          do not check history records. Download must be done.
                            downloaded picture will still be recorded in history
                            file.
      -s {no,win}, --setter {no,win}
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

* **2013-09-24 1.3.0**
    * supports high resolution wallpapers
    * change default checking interval to 2 hours
    * obsolete option `-f` and `--persistence`
    * fix none type error when offset exceeds boundary issue #2
    * fix none type error when download picture fails issue #3
