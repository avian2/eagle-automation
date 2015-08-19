import os

import logging
log = logging.getLogger('pea').getChild(__name__)

CONFIG_PATHS = [
	os.path.join(os.path.dirname(__file__), 'default.py'),
	'/etc/eagle_automation.conf',
	os.path.join(os.environ.get('HOME', '/'), '.config/eagle_automation.conf'),
	'eagle_automation.conf',
]

class Config: pass

def _get_config():

	config = Config()

	for path in CONFIG_PATHS:
		if os.path.exists(path):
			exec(compile(open(path).read(), path, 'exec'), config.__dict__)

	return config

config = _get_config()
