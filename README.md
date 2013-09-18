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
Download [need-installer]() and install it. A shortcut will be created in your 
startup folder. 

You can also create a shortcut by yourself, or add arguments to it.

----------

### How it works

1.  Retrieve URL and information of images from Bing image API, number of images to retrieve can be specified by **persistence**

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

    usage: pybingwallpaper [-h] [-v] [-d] [-f] [--redownload] [-k]
                           [--persistence PERSISTENCE] [-s {no,gnome3,gnome2}]
                           [--setter-args SETTER_ARGS] [-t OUTPUT_FOLDER]

    Download the wallpaper offered by National Geographicphotography website and
    set it current wallpaper background.

    optional arguments:
      -h, --help            show this help message and exit
      -v, --version         show version information
      -d, --debug           enable debug outputs. The more --debug the more
                            detailed the log will be
      -f, --force           adopt this photo even if its size may be strange to be
                            wallpaper. Disabled by default
      --redownload          do not consider history records. Download must be
                            done. But this download will be recorded in history
                            file.
      -k, --keep-file-name  keep the original filename. By default downloaded file
                            will be renamed as 'wallpaper.jpg'. Keep file name
                            will retain all downloaded photos
      --persistence PERSISTENCE
                            go back for at most N-1 pages if photo of today isn't
                            for wallpaper. Backward browsing will be interrupted
                            before N-1 pages tried if either a downloaded page
                            found or a wallpaper link read
      -o OFFSET, --offset OFFSET
                            start downloading from the photo of 'N' days ago.
                            specify 0 to download photo of today.
      -s {no,gnome3,gnome2,win}, --setter {no,gnome3,gnome2,win}
                            specify interface to be called for setting wallpaper.
                            'no' indicates downloading-only; 'gnome2/3' are only
                            for Linux with gnome; 'win' is for Windows only.
                            Customized setter can be added as dev doc described.
                            Default: gnome3(Linux) or win(Win32)
      --setter-args SETTER_ARGS
                            arguments for specified setter
      -t OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER
                            specify the folder to store photos. Use
                            '~/MyBingWallpapers' folder in Linux or 'My
                            Documents/MyBingWallpapers' in Windows by default

----------

### Devolopment

#### Customized wallpaper setter
(TBD)

----------
