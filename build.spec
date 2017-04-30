# -*- mode: python -*-
import inspect
import sys
from os.path import join as pathjoin, dirname, abspath

def current_path():
    f = inspect.getabsfile(current_path)
    return dirname(abspath(f))

hiddenimports = []
datas = []

if sys.platform.startswith('win'):
    hiddenimports.extend([
        'PIL','PIL.Image',
        'win32', 'win32.win32gui',
    ])
    datas.insert(0, (pathjoin('pybingwallpaper', 'winsetter.py'), '.'))

block_cipher = None

a = Analysis([pathjoin('bin', 'BingWallpaper')],
             pathex=[current_path(), ],
             binaries=None,
             datas=datas,
             hiddenimports=hiddenimports,
             hookspath=[],
             runtime_hooks=[],
             excludes=[
                 'tkinter', 'tk', 'tcl',
             ],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='BingWallpaper',
          debug=False,
          strip=True,
          upx=True,
          console=False )
cliexe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='BingWallpaper-cli',
          debug=False,
          strip=True,
          upx=True,
          console=True )
coll = COLLECT(exe, cliexe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='BingWallpaper')
