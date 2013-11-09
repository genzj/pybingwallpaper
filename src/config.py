#!/usr/bin/env python3
import log
import argparse
import sys
from argparse import Namespace

_logger = log.getChild('config')

class ConfigParameter:
    ''' 
        ConfigParameter is an abstract of configuration data which integrate config file
        and commandline-like argument data models.
    '''
    def __init__(self, name, defaults=None, type=None, choices=None, help='', loader_opts=None):
        '''
        name        - name of option.
        defaults    - default values which can be specified as a dict with keys 
                    specify different default values of corresponding platform,
                    e.g. {'win32': True, 'linux': False, 'darwin': False, '*': True}
                    name of platforms are defined as in sys.platform and '*' stands for
                    unspecified platforms which is equivalent to assigning value directly
                    to defaults. That is, 'default=1' works same as 'default={'*':1}'
        type        - the type to which the parameter should be converted, e.g.
                    "type=int" employes int() on loaded values by loader.
        choices     - a container of the allowable values for the parameter. a
                    ValueError will be raised if type converted value not a member of
                    not-none choices container
        help        - human readable message describe meaning of this parameter
        loader_opts - options specified as dict will be used by certain loaders
                      read document of loaders for available options
        '''
        self.name = str(name)
        self.validate_name()
        self.defaults = defaults if isinstance(defaults, dict) else {'*': defaults}
        if type is not None: self.type = type
        if choices is not None: self.choices = choices
        self.help = help
        self.loader_opts = loader_opts if loader_opts is not None else dict()

    def validate_name(self):
        if any(map(lambda x:x.isspace(), self.name)):
            raise ValueError("parameter name can't contain space")

    def get_default(self, platform=None):
        if not platform:
            platform = sys.platform
        if platform not in self.defaults:
            platform = '*'
        return self.defaults[platform]

    def __repr__(self):
        return '''{}(name={}, defaults={}, type={}, choices={}, help={}, loader_opts={})'''.format(
                        self.__class__.__name__,
                        repr(self.name),
                        repr(self.defaults),
                        repr(self.type if hasattr(self, 'type') else None),
                        repr(self.choices if hasattr(self, 'choices') else None),
                        repr(self.help),
                        repr(self.loader_opts)
                    )

    def __eq__(self, other):
        return self.name == other.name

class ConfigDatabase:
    def __init__(self, prog, description = None, parameters = None):
        self.prog = prog
        self.description = description
        self.parameters = list(parameters) if parameters is not None else list()

    def add_param(self, param):
        if param not in self.parameters:
            self.parameters.append(param)
        else:
            raise NameError('duplicated parameter name "%s" found'%(param.name,))

    def __repr__(self):
        return '{}(prog={}, description={}, parameters={})'.format(
                    self.__class__.__name__,
                    repr(self.prog),
                    repr(self.description),
                    repr(self.parameters)
                )

class ConfigLoader:
    def load(self, db, *args, **kwargs):
        raise NotImplemented()

class ConfigDumper:
    def dump(self, db, *args, **kwargs):
        raise NotImplemented()

class ConfigFileLoader(ConfigLoader):
    def load(self, data, db):
        pass

class ConfigFileDumper(ConfigDumper):
    pass

class CommandLineArgumentsLoader(ConfigLoader):
    '''
    Options keyword: 'cli'
    Supported options: 
        flags - container which will be converted to CLI option flags
        other options can be found here 
            http://docs.python.org/3/library/argparse.html#argparse.ArgumentParser.add_argument
    '''
    OPT_KEY = 'cli'
    def __init__(self, generate_default=False):
        self.generate_default = generate_default

    def param_to_arg_opts(self, param):
        # load common options
        opts = {
                'help': param.help,
                'dest': param.name,
            }
        if hasattr(param, 'type'): opts['type'] = param.type
        if hasattr(param, 'choices'): opts['choices'] = param.choices

        if self.generate_default:
            opts['default'] = param.get_default()
        
        # load specific options at last so that
        # specific ones take higher priority in case a same
        # key occurs in both common part and loader_opts part
        specific_opts = param.loader_opts.get(self.OPT_KEY, dict())
        opts.update(specific_opts)
        if 'flags' in opts: del(opts['flags'])
        return opts

    def param_to_arg_flags(self, param):
        opts = param.loader_opts.get(self.OPT_KEY, dict())
        if 'flags' in opts:
            ans = opts['flags']
        elif len(param.name) == 1:
            # simple name like 'a' will be converted to '-a'
            ans = ['-'+param.name,]
        else:
            # long name like 'debug' will be converted to '--debug'
            ans = ['--'+param.name,]
        return ans

    def assemble_parser(self, db):
        self.parser = argparse.ArgumentParser(prog = db.prog, description = db.description)
        for param in db.parameters:
            self.parser.add_argument(
                    *self.param_to_arg_flags(param), 
                    **self.param_to_arg_opts(param)
            )

    def load(self, db, data):
        self.assemble_parser(db)
        return self.parser.parse_args(data)

class DefaultValueLoader(ConfigFileLoader):
    OPT_KEY = 'defload'

    def __init__(self, platform=None):
        self.platform = platform

    def load(self, db, data=None):
        ans = Namespace()
        for param in db.parameters:
            val = param.get_default(self.platform)
            val = param.type(val) if hasattr(param, 'type') else val
            setattr(ans, param.name, val)
        return ans


class JsonFileLoader(ConfigFileLoader):
    pass

class JsonFileDumper(ConfigFileDumper):
    pass
