#!/usr/bin/env python3
import logging
from logging import INFO, DEBUG

# bypass import optimization, levels are meant to be imported for other modules although not used in this file
assert [INFO, DEBUG]

PAGEDUMP = 5
logging.addLevelName(PAGEDUMP, 'PAGEDUMP')

_logger = None
_children = []


def __init(app_name):
    global _logger
    _logger = logging.getLogger(app_name)
    if not _logger.handlers:
        _loggerHandler = logging.StreamHandler()
        _loggerHandler.setLevel(PAGEDUMP)
        _loggerHandler.setFormatter(logging.Formatter('[%(asctime)s - %(levelname)s - %(name)s] %(message)s'))
        _logger.addHandler(_loggerHandler)
        _logger.setLevel(INFO)


def getChild(*args, **kwargs):
    child_logger = _logger.getChild(*args, **kwargs)
    if child_logger not in _children:
        _children.append(child_logger)
    return child_logger


def setDebugLevel(level):
    _logger.setLevel(level)
    list(map(lambda l: l.setLevel(level), _children))


__init('bingwallpaper')

if __name__ == '__main__':
    log = _logger.getChild('logtest')
    log.setLevel(logging.DEBUG)
    log.info('Info test')
    log.warn('Warn test')
    log.error('Error test')
    log.critical('Critical test')
    log.debug('debug test')
    try:
        def __ex_test():
            raise Exception('exception test')


        __ex_test()
    except Exception as ex:
        log.exception(ex)
