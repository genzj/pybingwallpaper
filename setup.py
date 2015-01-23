from cx_Freeze import setup, Executable
import sys
sys.path.append('src')
from main import REV

# Dependencies are automatically detected, but it might need
# fine tuning.
buildOptions = {'packages': ['urllib', 'PIL'],
                'includes': ['win32.win32gui', 'log', 'record', 
                              'webutil', 'setter', 'bingwallpaper'],
                 'excludes': ['tkinter'],
                 'compressed':1,
                 'include_files': [('src/winsetter.py','')],
                 'bin_includes': ['pywintypes34.dll'],
                 'optimize': 2,
               }

executables = [
    Executable('./src/main.py', base='Win32GUI', targetName='BingWallpaper.exe'),
    Executable('./src/main.py', base='Console', targetName='BingWallpaper-cli.exe')
]

setup(name='PyBingWallpaper.exe',
      version = REV,
      description = 'Bing.com Wallpaper Downloader',
      options = {'build_exe': buildOptions},
      executables = executables)
