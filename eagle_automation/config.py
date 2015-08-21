import os

import logging
log = logging.getLogger('pea').getChild(__name__)

from yaml import load, dump
try:
	from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
	from yaml import Loader, Dumper

from eagle_automation.default import Config

DEFAULT_CONFIG_PATHS = [
	'/etc/eagle_automation.conf',
	os.path.join(os.environ.get('HOME', '/'), '.config/eagle_automation.conf'),
	os.path.join(os.environ.get('HOME', '/'), '.eagle_automation.conf'),
	'eagle_automation.conf',
	'.eagle_automation.conf',
]


def __set_value(self, key, val):
	self.__dict__.update({key: val})

def __merge_dict(a, b, path=None):
    "merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict):
                merge(a[key], b[key], path + [str(key)])
            elif a[key] == b[key]:
                pass # same leaf value
            else:
                raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
        else:
            a[key] = b[key]
    return a

def __read_config(self, path):
	if os.path.exists(path):
		with open(path, 'r') as f:
			data = load(f, Loader=Loader)
			__merge_dict(self.__dict__, data)
	else:
		raise FileNotFoundError()

Config.update = __read_config
Config.insert = __set_value

config = Config()

def init():
	for path in DEFAULT_CONFIG_PATHS:
		try:
			config.update(path)
			log.debug("Loaded configuration: {}".format(path))
		except:
			log.debug("Configuration file '{}' not found".format(path))

__all__ = ['config', 'init']
