#!/usr/bin/python

from setuptools import setup

import sys
if sys.platform == 'win32':
	import py2exe

setup(
	name='eagle_automation',
	version='0.1.0',
	description='Simple scripts supporting open hardware development using CadSoft EAGLE',
	license='GPL',
	author='Tomaz Solc, Bernard Pratz',
	author_email='tomaz.solc@tablix.org, guyzmo+pea@m0g.net',
	url='',
	packages=['eagle_automation'],
	long_description_markdown_filename='README.md',
	classifiers=[
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Development Status :: 4 - Beta',
		'License :: OSI Approved',
		'Operating System :: Unix',
	],
	data_files = [('lib/python/eagle_automation', ['eagle_automation/default.conf'])],
	setup_requires=['setuptools-markdown'],
	install_requires=[
		'pillow',
		'docopt',
		'setuptools',
	],
	# windows=[
	#     {
	#         'script': 'eagle_automation/artool.py',
	#         # 'icon_resources': [(1, 'moduleicon.ico')]
	#     }
	# ],
	zipfile=None,
	options={'py2exe':{
		'includes': ['docopt'],
		'bundle_files': 1
	}
	},
	entry_points="""
	# -*- Entry points: -*-
	[console_scripts]
	pea = eagle_automation.pea:main
	""",
	console=["eagle_automation/pea.py"],
)

print("""\
To start using this tool, after `python setup.py install` do `pea --help`
""")
