import os
import sys
from pybingwallpaper.rev import REV
from setuptools import setup, find_packages

if sys.version_info[0] == 2:
    import codecs
    fopen = codecs.open
else:
    fopen = open

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return fopen(os.path.join(os.path.dirname(__file__), fname), encoding='utf8').read()

def os_requires():
    return ['Pillow', 'pypiwin32'] if sys.platform == 'win32' else []

def backport_requires():
    return ['configparser', 'subprocess32'] if sys.version_info[0] == 2 else []

def requires():
    return os_requires() + backport_requires()

setup(
    name = 'PyBingWallpaper',
    version = REV,
    author = 'genzj',
    author_email = 'zj0512@gmail.com',
    description = (
        'A simple Bing.com wallpaper downloader'
    ),
    license = 'MIT',
    keywords = 'bing wallpaper',
    url = 'https://github.com/genzj/pybingwallpaper',


    packages=find_packages(exclude=['res', 'test', 'wiki']),
    install_requires=requires(),

    entry_points={
        'console_scripts': [
            'BingWallpaper=pybingwallpaper.main:main',
        ],
    },

    long_description=read('README.rst'),
    classifiers=[
        'Development Status :: 6 - Mature',
        'Environment :: Console',
        'Topic :: Desktop Environment',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',

        'Operating System :: Microsoft :: Windows :: Windows XP',
        'Operating System :: Microsoft :: Windows :: Windows Vista',
        'Operating System :: Microsoft :: Windows :: Windows 7',
        'Operating System :: Microsoft :: Windows :: Windows 8',
        'Operating System :: Microsoft :: Windows :: Windows 8.1',
        'Operating System :: Microsoft :: Windows :: Windows 10',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: Other',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.3',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
