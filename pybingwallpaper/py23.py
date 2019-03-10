# compatibility with py2 and py3
import sys
from importlib import import_module

from . import log

PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3

_logger = log.getChild('py23@' + ('2' if PY2 else '3'))


def import_moved(py2name, py3name):
    if PY2:
        _logger.debug('importing libs %s for python 2.x', py2name)
        lib = import_module(py2name)
    elif PY3:
        _logger.debug('importing libs %s for python 3.x', py3name)
        lib = import_module(py3name)
    else:
        raise RuntimeError("unknown Python version " + sys.version)
    return lib


def get_moved_attr(py2modulename, py3modulename, attr, attr2=None, attr3=None):
    attr_moved = [attr2 is not None, attr3 is not None]
    if all(attr_moved):
        attr = attr2 if PY2 else attr3
    elif any(attr_moved):
        raise ValueError('both of attr2 and attr3 must be specified')

    result = getattr(import_moved(py2modulename, py3modulename), attr)
    _logger.debug('attr %r found', result)
    return result
