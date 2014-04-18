#!/usr/bin/env python3
import log
import json
import time
import datetime
import sqlite3
from os.path import isfile
from collections import UserDict

_logger = log.getChild('record')
#_logger.setLevel(log.DEBUG)

class DownloadRecord(dict):
    def __init__(self, url, local_file, description, download_time=None, raw=None, is_accompany=False):
        UserDict.__init__(self)
        if download_time is None:
            download_time = datetime.datetime.fromtimestamp(time.time())
        timestr = download_time.isoformat()

        self['url'] = url
        self['local_file'] = local_file
        self['description'] = description
        self['time'] = timestr
        self['raw'] = raw
        self['is_accompany'] = is_accompany

null_record = DownloadRecord('', '', datetime.datetime.fromtimestamp(0))

class DownloadRecordManager(dict):
    def __init__(self, name):
        dict.__init__(self)
        self.name = name
        self.clear()

    def save(self, f):
        json.dump(self, f)

    def load(self, f):
        self.clear()
        try:
            content = json.load(f)
        except:
            _logger.warning('error occurs when load json file', exc_info=1)
            return
        _logger.debug('json file loaded:\n%s', str(content))
        for r in content.values():
            try:
                exists = isfile(r['local_file'])
            except:
                _logger.debug('error occurs when detecting saved file', exc_info=1)
                exists = False
            if exists:
                self.add(r)
            else:
                _logger.debug('%s doesn\'t exist any more', r)
        _logger.debug('history %s loaded', self)
    
    def add(self, r):
        r = dict(r)
        if 'raw' in r:
            r.pop('raw')
        self[r['url']] = r

    def get_by_url(self, url, default_rec=null_record):
        return self.get(url, default_rec)

default_manager = DownloadRecordManager('default')

class SqlDatabaseRecordManager(DownloadRecordManager):
    def add(self, r):
        self[r['url']] = r

    def save(self, f):
        conn = sqlite3.connect(f)
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS [BingWallpaperRecords] (
              [Url] CHAR(1024) NOT NULL ON CONFLICT FAIL, 
              [DownloadTime] DATETIME NOT NULL ON CONFLICT FAIL, 
              [LocalFilePath] CHAR(1024), 
              [Description] TEXT(1024), 
              [Image] BLOB, 
              [IsAccompany] BOOLEAN DEFAULT False, 
              CONSTRAINT [sqlite_autoindex_BingWallpaperRecords_1] PRIMARY KEY ([Url]));
        ''')
        conn.commit()
        for k,v in self.items():
            cur.execute('''
                INSERT OR REPLACE INTO [BingWallpaperRecords] 
                  (Url, DownloadTime, LocalFilePath, Description, Image, IsAccompany)
                  VALUES (?, ?, ?, ?, ?, ?)
            ''', (k, v['time'], v['local_file'], v['description'], v['raw'], v['is_accompany']))
        conn.commit()

    def load(self, f):
        raise NotImplementedError("sql database is write-only")
