# -*- mode: python -*-

block_cipher = None


a = Analysis(['src\\main.py'],
             pathex=[],
             binaries=None,
             datas=[('src\\winsetter.py', '.')],
             hiddenimports=[
                 'PIL','PIL.Image',
                 'win32', 'win32.win32gui',
             ],
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
          name='main',
          debug=False,
          strip=False,
          upx=True,
          console=True )
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='main')

# vim: ft=python:
