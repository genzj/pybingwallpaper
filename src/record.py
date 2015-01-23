#!/usr/bin/env python3
import log
import json
import datetime
import sqlite3
from os.path import isfile
from collections import UserDict

_logger = log.getChild('record')
#_logger.setLevel(log.DEBUG)

class DownloadRecord(dict):
    def __init__(self, url, local_file, description,
                  download_time=None, raw=None, is_accompany=False, market=''):
        UserDict.__init__(self)
        if download_time is None:
            download_time = datetime.datetime.utcnow()
        timestr = download_time.isoformat()

        self['url'] = url
        self['local_file'] = local_file
        self['description'] = description
        self['time'] = timestr
        self['raw'] = raw
        self['is_accompany'] = is_accompany
        self['market'] = market

null_record = DownloadRecord('', '', 'Null Record', datetime.datetime.utcfromtimestamp(0))

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
    LATEST_DB_VERSION = (4, 4, 2)
    DB_UPGRADE_SCRIPTS = {
            #from_ver:  (to_ver, sql)
            (4, 4, 1):  ((4, 4, 2), '''
            ALTER TABLE [BingWallpaperRecords]
            ADD COLUMN Market TEXT(64) DEFAULT "";

            CREATE TABLE [BingWallpaperCore]
            ([MajorVer] INTEGER,
              [MinorVer] INTEGER,
              [Build] INTEGER);

            INSERT INTO [BingWallpaperCore] 
              (MajorVer, MinorVer, Build)
              VALUES (4, 4, 2);'''),
        }

    def add(self, r):
        self[r['url']] = r

    def save(self, f):
        _logger.info('trying to save history to %s', f)
        conn = sqlite3.connect(f)
        self.upgrade_db(conn)
        cur = conn.cursor()
        for k,v in self.items():
            cur.execute('''
                INSERT OR REPLACE INTO [BingWallpaperRecords] 
                  (Url, DownloadTime, LocalFilePath, Description, Image, IsAccompany, Market)
                  VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (k, v['time'], v['local_file'], v['description'], v['raw'], v['is_accompany'], v['market']))
        conn.commit()

    def load(self, f):
        raise NotImplementedError("sql database is write-only")

    def upgrade_db(self, conn):
        ver = self.judge_version(conn)
        _logger.debug('dealing with database created in %s', ver)
        if ver == (0, 0, 0):
            self.create_scheme(conn)
            return
        elif self.vercmp(ver, self.LATEST_DB_VERSION) > 0:
            raise Exception('''Can't deal with database created by higher program version %s'''%(ver,))

        _logger.info('current db version %s needs upgrade to %s', ver, self.LATEST_DB_VERSION)
        while self.vercmp(ver, self.LATEST_DB_VERSION) < 0:
            next_ver, script = self.DB_UPGRADE_SCRIPTS[ver]
            _logger.debug('upgrading database from %s to %s, execute %s', ver, next_ver, script)
            cur = conn.cursor()
            try:
                cur.executescript(script)
            except Exception as err:
                _logger.fatal('error happened during database upgrade "%s"', 
                                script, exc_info=1)
                conn.rollback()
                raise err
            ver = next_ver
        _logger.info('upgrading script executed successfully, now db is %s', self.judge_version(conn))

    def create_scheme(self, conn):
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE [BingWallpaperRecords] (
              [Url] CHAR(1024) NOT NULL ON CONFLICT FAIL, 
              [DownloadTime] DATETIME NOT NULL ON CONFLICT FAIL, 
              [LocalFilePath] CHAR(1024), 
              [Description] TEXT(1024), 
              [Market] TEXT(64) DEFAULT "",
              [Image] BLOB, 
              [IsAccompany] BOOLEAN DEFAULT False, 
              CONSTRAINT [sqlite_autoindex_BingWallpaperRecords_1] PRIMARY KEY ([Url]));
        ''')
        cur.execute('''
            CREATE TABLE [BingWallpaperCore] (
              [MajorVer] INTEGER,
              [MinorVer] INTEGER,
              [Build] INTEGER);
        ''')
        cur.execute('''
            INSERT INTO [BingWallpaperCore] 
              (MajorVer, MinorVer, Build)
              VALUES (?, ?, ?)
        ''', self.LATEST_DB_VERSION)
        conn.commit()
        _logger.debug('created db from prog version %s', self.judge_version(conn))

    def vercmp(self, ver1, ver2):
        if ver1 == ver2:
            return 0
        elif ver1[0] > ver2[0] or \
                (ver1[0] == ver2[0] and ver1[1] > ver2[1]) or \
                (ver1[0] == ver2[0] and ver1[1] == ver2[1] and ver1[2] > ver2[2]):
            return 1
        return -1


    def judge_version(self, conn):
        ver = None
        cur = conn.cursor()
        tables = cur.execute('''
            SELECT lower(name) FROM [sqlite_master] WHERE type=='table';
        ''').fetchall()
        _logger.debug('find tables %s in database', tables)
        if ('bingwallpaperrecords',) not in tables and ('bingwallpapercore',) not in tables:
            ver = (0, 0, 0)
        elif ('bingwallpaperrecords',) in tables and ('bingwallpapercore',) not in tables:
            ver = (4, 4, 1)
        elif ('bingwallpaperrecords',) in tables and ('bingwallpapercore',) in tables:
            ver = cur.execute('''
                SELECT MajorVer, MinorVer, Build FROM [BingWallpaperCore];
            ''').fetchone()
        if not ver:
            raise Exception('Corrupted database with tables %s', tables)
        return ver
