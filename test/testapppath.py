#!/usr/bin/env python3

import unittest
import sys
import os

sys.path.append('../src')

from main import get_app_path 

SOURCE_DIR=''

class TestConfigureParameter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.oridir = os.path.abspath(os.curdir)

    def give_work_dir(self, _dir):
        os.chdir(self.oridir)
        os.chdir(_dir)
        self.curdir = os.path.abspath(os.curdir)

    def and_app_src(self, srcfile):
        self.srcfile = srcfile

    def expect_dir(self, _expect):
        _expect = os.path.abspath(_expect)
        _expect = os.path.normcase(_expect)
        self.assertEqual(get_app_path(self.srcfile), _expect, 'apppath incorrect')

    def curdir_still_same(self):
        curdir = os.path.abspath(os.curdir)
        self.assertEqual(curdir, self.curdir, 'curdir changed')
    
    def test_run_in_src_dir(self):
        self.give_work_dir('../src')
        self.and_app_src('main.py')
        self.expect_dir(r'E://Work/Python/pybingwallpaper/src')
        self.curdir_still_same()

    def test_run_in_cur_dir(self):
        self.give_work_dir('.')
        self.and_app_src('../src/main.py')
        self.expect_dir(r'E://Work/Python/pybingwallpaper/src')
        self.curdir_still_same()

    def test_run_from_root(self):
        self.give_work_dir('/')
        self.and_app_src(r'work/python/pybingwallpaper/src/main.py')
        self.expect_dir(r'E:\Work\Python\pybingwallpaper\src')
        self.curdir_still_same()

    def test_run_in_same_disk(self):
        self.give_work_dir('e:\\')
        self.and_app_src(r'work/python/pybingwallpaper/src/main.py')
        self.expect_dir(r'E:\Work\Python\pybingwallpaper\src')
        self.curdir_still_same()

    def test_run_in_other_disk(self):
        self.give_work_dir('d:')
        self.and_app_src(r'e:/work/python/pybingwallpaper/src/main.py')
        self.expect_dir(r'E:\Work\Python\pybingwallpaper\src')
        self.curdir_still_same()

    def test_run_in_other_disk_dir(self):
        self.give_work_dir('c:/windows')
        self.and_app_src(r'e:/work/python/pybingwallpaper/src/main.py')
        self.expect_dir(r'E:\Work\Python\pybingwallpaper\src')
        self.curdir_still_same()
