#!/usr/bin/env python3
from pybingwallpaper import setter

from tempfile import NamedTemporaryFile
import sys
import os
import time


if sys.platform == 'darwin':
    from appscript import app, mactypes, its


    class DarwinWallpaperSetter(setter.WallpaperSetter):
        def set(self, path, args):
            blankbmp = None
            try:
                blankbmp = NamedTemporaryFile(prefix='bingwp', suffix='.bmp', delete=False)
                blankbmp.close()
                se = app('System Events')
                desktops = se.desktops.display_name.get()
                for d in desktops:
                    desk = se.desktops[its.display_name == d]
                    desk.picture.set(mactypes.File(blankbmp.name))
                    time.sleep(0.5)
                    desk.picture.set(mactypes.File(path))
                    time.sleep(0.5)
            finally:
                if blankbmp:
                    os.unlink(blankbmp.name)


    setter.register('darwin', DarwinWallpaperSetter)

