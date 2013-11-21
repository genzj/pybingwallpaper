#!/usr/bin/env python3

import unittest
import sys
import random

sys.path.append('../src')

import config
from config import ConfigParameter
from config import ConfigDatabase
from config import CommandLineArgumentsLoader
from config import DefaultValueLoader
from config import ConfigFileLoader
from config import ConfigFileDumper
from config import Namespace

def getdb():
    return ConfigDatabase('test1', description='test desc')

# TODO: Add cases to test loader_srcs option
class TestConfigureParameter(unittest.TestCase):
    def setUp(self):
        pass

    def test_import_config_module(self):
        self.assertIsNotNone(ConfigParameter)
        self.assertIsNotNone(ConfigDatabase)

    def test_init_param(self):
        p = ConfigParameter('test1')
        self.assertIsNotNone(p)

    def test_name(self):
        names = ['klb', '1ab', 's#a']
        for n in names:
            p = ConfigParameter(name = n)
            self.assertEqual(p.name, n)

    def test_invalid_name(self):
        names = ['k b', '\tab', 's\na']
        for n in names:
            with self.assertRaises(ValueError, msg="parameter name can't contain space"):
                ConfigParameter(name = n)

class TestConfigureDatabase(unittest.TestCase):
    def setUp(self):
        pass

    def test_prog(self):
        db = getdb()
        self.assertEqual(db.prog, 'test1')

    def test_desc(self):
        db = ConfigDatabase('test1', 'a test database')
        self.assertEqual(db.prog, 'test1')
        self.assertEqual(db.description,  'a test database')

    def test_parameter_init(self):
        params = [
                    ConfigParameter('123'), 
                    ConfigParameter('456')
                 ]
        db = ConfigDatabase('test1', parameters=params)
        self.assertListEqual(db.parameters, params)

    def test_repr(self):
        params = [
                    ConfigParameter('123', type=''), 
                    ConfigParameter('456', type='')
                 ]
        db = ConfigDatabase('test1', description='test desc', parameters=params)
        dbcopy = eval(repr(db))
        self.assertEqual(db.prog, dbcopy.prog)
        self.assertEqual(db.description, dbcopy.description)
        self.assertListEqual(db.parameters, dbcopy.parameters)

    def test_add_parameters(self):
        params = [
                    ConfigParameter('123'), 
                    ConfigParameter('456')
                 ]
        new_param = ConfigParameter('789')
        db = ConfigDatabase('test1', description='test desc', parameters=params)
        self.assertListEqual(db.parameters, params)
        db.add_param(new_param)
        self.assertListEqual(db.parameters, params+[new_param,])

    def test_no_dup_param(self):
        params = [
                    ConfigParameter('123', type=int), 
                    ConfigParameter('456', defaults=9)
                 ]
        new_param = ConfigParameter('123')
        db = ConfigDatabase('test1', description='test desc', parameters=params)
        self.assertListEqual(db.parameters, params)
        with self.assertRaises(NameError, msg='duplicated parameter name "%s" found'%(new_param.name,)):
            db.add_param(new_param)
        self.assertListEqual(db.parameters, params)


class TestCliLoader(unittest.TestCase):
    def getdb(self):
        return ConfigDatabase('test1', description='test desc')

    def getloader(self):
        return CommandLineArgumentsLoader()

    def test_invalid_arg(self):
        loader = self.getloader()
        db = getdb()
        p = ConfigParameter(name='param1', type=int)
        db.add_param(p)
        with self.assertRaises(SystemExit) as se:
            loader.load(db, ['--not-exist'])
        self.assertEqual(se.exception.code, 2)

    def test_version(self):
        loader = self.getloader()
        db = getdb()
        p = ConfigParameter(name='notused', loader_opts={'cli':{
                'action': 'version',
                'flags':('-v','--version'),
                'version': 'test-version-1234'
            }})
        db.add_param(p)
        with self.assertRaises(SystemExit) as se:
            loader.load(db, ['-v'])
        self.assertEqual(se.exception.code, 0)
        with self.assertRaises(SystemExit) as se:
            loader.load(db, ['--version'])
        self.assertEqual(se.exception.code, 0)

    def test_name(self):
        db = getdb()
        cli_opts = {'flags':['-p']}
        p = ConfigParameter(name='param1', type=lambda s:int(s,0), loader_opts={'cli':cli_opts})
        db.add_param(p)
        loader = self.getloader()

        with self.assertRaises(SystemExit) as se:
            loader.load(db, ['--param1', '1'])
        self.assertEqual(se.exception.code, 2)

        ans = loader.load(db, ['-p', '1'])
        self.assertEqual(getattr(ans, p.name), 1)

    def test_load_int(self):
        ds = [ 
                ('0', 0), 
                ('0x1aedead0b', 0x1aedead0b),
                ('0b0011', 3),
                ('-9571293', -9571293),
             ]

        db = getdb()
        p = ConfigParameter(name='param1', type=lambda s:int(s,0))
        db.add_param(p)
        loader = self.getloader()
        for s, d in ds:
            ans = loader.load(db, ['--param1', s])
            self.assertEqual(getattr(ans, p.name), d)
            
    def test_load_str(self):
        ds = [ 
                '    ',
                '#123',
                'as_',
                '9 9'
             ]

        db = getdb()
        p = ConfigParameter(name='param1')
        db.add_param(p)
        loader = self.getloader()
        for s in ds:
            ans = loader.load(db, ['--param1', s])
            self.assertEqual(getattr(ans, p.name), s)

    def test_load_choice(self):
        good = ['c1', 'c3', 'c2']
        choices = ('c0', 'c1', 'c2', 'c3')
        db = getdb()
        p = ConfigParameter(name='param1', defaults='c1', choices=choices)
        db.add_param(p)
        loader = self.getloader()
        # try legal ones
        for s in good:
            ans = loader.load(db, ['--param1', s], generate_default=True)
            self.assertEqual(getattr(ans, p.name), s)
        # test use default
        ans = loader.load(db, [], generate_default=True)
        self.assertEqual(getattr(ans, p.name), good[0])

        # test illegal value
        with self.assertRaises(SystemExit) as se:
            loader.load(db, ['--param1', 'no-good'], generate_default=True)
        self.assertEqual(se.exception.code, 2)
            
    def test_load_true(self):
        cli_opts = {'action':'store_true'}
        db = getdb()
        p = ConfigParameter(name='param1', defaults=False, loader_opts={'cli':cli_opts})
        db.add_param(p)
        loader = self.getloader()
        ans = loader.load(db, ['--param1'])
        self.assertTrue(getattr(ans, p.name))
        ans = loader.load(db, [])
        self.assertFalse(hasattr(ans, p.name))
        ans = loader.load(db, [], generate_default=True)
        self.assertFalse(getattr(ans, p.name))

    def test_load_false(self):
        cli_opts = {'action':'store_false'}
        db = getdb()
        p = ConfigParameter(name='param1', defaults=True, loader_opts={'cli':cli_opts})
        db.add_param(p)
        loader = self.getloader()
        ans = loader.load(db, ['--param1'])
        self.assertFalse(getattr(ans, p.name))
        ans = loader.load(db, [], generate_default=True)
        self.assertTrue(getattr(ans, p.name))

    def test_load_count(self):
        cli_opts = {'action':'count'}
        db = getdb()
        p = ConfigParameter(name='d', defaults=0, loader_opts={'cli':cli_opts})
        db.add_param(p)
        loader = self.getloader()
        ans = loader.load(db, ['-d'], generate_default=True)
        self.assertEqual(getattr(ans, p.name), 1)
        ans = loader.load(db, [], generate_default=True)
        self.assertEqual(getattr(ans, p.name), 0)
        ans = loader.load(db, ['-d', '-d', '-d'], generate_default=True)
        self.assertEqual(getattr(ans, p.name), 3)
        c = random.randint(0, 256)
        ans = loader.load(db, ['-'+'d'*c], generate_default=True)
        self.assertEqual(getattr(ans, p.name), c)

class TestDefaultValueLoader(unittest.TestCase):
    def getloader(self, platform=None):
        return DefaultValueLoader(platform)

    def test_load_plain_def(self):
        loader = self.getloader()
        db = getdb()
        p = ConfigParameter(name='intparam', defaults=0)
        db.add_param(p)
        p = ConfigParameter(name='strparam', defaults='blah blah blah')
        db.add_param(p)
        p = ConfigParameter(name='noneparam')
        db.add_param(p)
        ans = loader.load(db)
        self.assertEqual(ans.intparam, 0)
        self.assertEqual(ans.strparam, 'blah blah blah')
        self.assertIsNone(ans.noneparam)

    def test_load_cur_platform(self):
        loader = self.getloader()
        db = getdb()
        p = ConfigParameter(name='param', defaults={sys.platform:'myval', '*':'otherval'})
        db.add_param(p)
        ans = loader.load(db)
        self.assertEqual(ans.param, 'myval')

    def test_load_other_platform(self):
        defs = {
            'linux': 'linuxval',
            'win': 'win32val',
            '*': 'otherval'
        }
        db = getdb()
        p = ConfigParameter(name='param', defaults=defs)
        db.add_param(p)
        loader = self.getloader('linux')
        ans = loader.load(db)
        self.assertEqual(ans.param, 'linuxval')
        loader = self.getloader('darwin')
        ans = loader.load(db)
        self.assertEqual(ans.param, 'otherval')
        loader = self.getloader('win')
        ans = loader.load(db)
        self.assertEqual(ans.param, 'win32val')

    def test_load_with_type(self):
        loader = self.getloader()
        db = getdb()
        p = ConfigParameter(name='param', type=lambda x:int(x,0), defaults='0xffff')
        db.add_param(p)
        ans = loader.load(db)
        self.assertEqual(type(ans.param), int)
        self.assertEqual(ans.param, 0xffff)

    def test_load_overwrite(self):
        loader = self.getloader()
        db = getdb()
        p = ConfigParameter(name='param', defaults='defval')
        db.add_param(p)
        ans = loader.load(db)
        self.assertEqual(ans.param, 'defval')
        ans.param = 'modified'
        self.assertEqual(ans.param, 'modified')

from io import StringIO
class TestConfigFileLoader(unittest.TestCase):
    def setUp(self):
        self.config_file = StringIO('''
        [DEFAULT]
        # default section values
        topParam1 = 1
        topParam2 = "s-value"
        topParam3 = 

        [section1]
        secParam1 = 1 2 3
        secParam2 = 

        [section3]
        secParam2 = somevalue 
    ''')
    def getloader(self):
        return ConfigFileLoader()
    
    def test_load_plain_value(self):
        loader = self.getloader()
        db = getdb()
        p = ConfigParameter(name='topParam1')
        db.add_param(p)
        p = ConfigParameter(name='topParam2')
        db.add_param(p)
        p = ConfigParameter(name='topParam3')
        db.add_param(p)
        p = ConfigParameter(name='topParamx')
        db.add_param(p)
        ans = loader.load(db, self.config_file)
        self.assertEqual(ans.topParam1, '1')
        self.assertEqual(ans.topParam2, '"s-value"')
        self.assertEqual(ans.topParam3, '')
        self.assertFalse(hasattr(ans, 'topParamx'))

    def test_load_type_cast(self):
        loader = self.getloader()
        db = getdb()
        p = ConfigParameter(name='topParam1', type=int)
        db.add_param(p)
        p = ConfigParameter(name='topParam2', type=None)
        db.add_param(p)
        p = ConfigParameter(name='topParamx', type=float)
        db.add_param(p)
        ans = loader.load(db, self.config_file)
        self.assertEqual(type(ans.topParam1), int)
        self.assertEqual(ans.topParam1, 1)
        self.assertEqual(type(ans.topParam2), str)
        self.assertEqual(ans.topParam2, '"s-value"')
        self.assertFalse(hasattr(ans, 'topParamx'))

    def test_config_section(self):
        loader = self.getloader()
        db = getdb()
        getSection = lambda secname: {'section': secname}
        p = ConfigParameter(name='topParam2', loader_opts={'conffile':getSection(None)})
        db.add_param(p)

        p = ConfigParameter(name='secParam1', loader_opts={'conffile':getSection('section1')})
        db.add_param(p)

        p = ConfigParameter(name='secParam2', loader_opts={'conffile':getSection('section3')})
        db.add_param(p)

        p = ConfigParameter(name='secParamx', loader_opts={'conffile':getSection('sectionx')})
        db.add_param(p)

        ans = loader.load(db, self.config_file)
        self.assertEqual(ans.topParam2, '"s-value"')
        self.assertEqual(ans.secParam1, '1 2 3')
        self.assertEqual(ans.secParam2, 'somevalue')
        self.assertFalse(hasattr(ans, 'topParamx'))

    def test_load_default(self):
        loader = self.getloader()
        db = getdb()
        p = ConfigParameter(name='topParam3', defaults='def-1')
        db.add_param(p)
        p = ConfigParameter(
                name='secParamx',
                type=float, defaults='0',
                loader_opts={'conffile':{'section':'section3'}}
            )
        db.add_param(p)
        ans = loader.load(db, self.config_file, generate_default=True)
        self.assertEqual(ans.topParam3, '')
        self.assertEqual(type(ans.secParamx), float)
        self.assertEqual(ans.secParamx, float(0))

class TestConfigFileDumper(unittest.TestCase):
    def setUp(self):
        self.conf = Namespace()
        choices = ['cal1', 'cal2', 'cal3']
        setattr(self.conf, 'intparam', 0x77992213)
        setattr(self.conf, 'strparam', 'a complicat3d string#!')
        setattr(self.conf, 'trueparam', True)
        setattr(self.conf, 'falseparam', False)
        setattr(self.conf, 'choiceparam', choices[1])
        self.db = getdb()
        p = ConfigParameter(name='intparam', type=int)
        self.db.add_param(p)
        p = ConfigParameter(name='strparam', type=str)
        self.db.add_param(p)
        p = ConfigParameter(name='trueparam', type=bool,
                loader_opts={'conffile':{'section':'section_1'}})
        self.db.add_param(p)
        p = ConfigParameter(name='falseparam', type=bool,
                loader_opts={'conffile':{
                    'converter':lambda x: True if bool(x) and x.lower() != 'false' else False
                    }})
        self.db.add_param(p)
        p = ConfigParameter(name='choiceparam', choices=choices)
        self.db.add_param(p)

    def getloader(self):
        return ConfigFileLoader()

    def getdumper(self):
        return ConfigFileDumper()

    def test_dump_config(self):
        buf = StringIO()
        loader = self.getloader()
        dumper = self.getdumper()
        ret = dumper.dump(self.db, self.conf, buf)
        self.assertNotEqual(ret, 0)
        buf.seek(0)
        ans = loader.load(self.db, buf)
        for k, v in vars(self.conf).items():
            self.assertTrue(hasattr(ans, k))
            self.assertEqual(type(getattr(ans, k)), type(v))
            self.assertEqual(getattr(ans, k), v)
        self.assertEqual(ans, self.conf)

class TestOtherUtil(unittest.TestCase):
    def test_merge(self):
        ns1 = Namespace()
        ns2 = Namespace()
        ns1.param1 = 123
        ns2.param1 = 456
        ns1.parama = 'a'
        ns2.paramb = ('1', 2, 's')
        ans = config.merge_config(ns1, ns2)
        self.assertEqual(ns1.param1, 123)
        self.assertEqual(ns2.param1, 456)
        self.assertEqual(ans.param1, 456)

        self.assertEqual(ns1.parama, 'a')
        self.assertFalse(hasattr(ns2, 'parama'))
        self.assertEqual(ans.parama, 'a')

        self.assertFalse(hasattr(ns1, 'paramb'))
        self.assertEqual(ns2.paramb, ('1', 2, 's'))
        self.assertEqual(ans.paramb, ('1', 2, 's'))

