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


def _set_value(self, key, val):
	self.__dict__.update({key: val})

def _read_config(self, path):
	if os.path.exists(path):
		data = load(stream, Loader=Loader)
		self.__dict__.update(data)
	else:
		raise FileNotFoundError()

Config.update = _read_config
Config.insert = _set_value

config = Config()

def init():
	for path in DEFAULT_CONFIG_PATHS:
		try:
			config.update(path)
			log.debug("Loaded configuration: {}".format(path))
		except:
			log.debug("Configuration file '{}' not found".format(path))

__all__ = ['config', 'init']
