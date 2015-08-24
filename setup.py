#!/usr/bin/python
# -+- encoding: utf-8

from setuptools import setup

import sys

opts = dict()
if sys.platform == 'win32':
	import py2exe
	opts.update(
		dict(
			zipfile=None,
			options={
				'py2exe':{
					'includes': ['docopt'],
					'bundle_files': 1
				}
			},
			console=["eagle_automation/pea.py"],
		))
	# windows=[
	#     {
	#         'script': 'eagle_automation/artool.py',
	#         # 'icon_resources': [(1, 'moduleicon.ico')]
	#     }
	# ],

# We do not need pandoc when installing through pypi
if sys.argv[0] == 'setup.py':
    opts.update(dict(
        long_description_markdown_filename='README.md',
        setup_requires=['setuptools_markdown'],
    ))
else:
    opts.update(dict(
        long_description=open('README.md', 'r').read(),
    ))

setup(
	name='eagle_automation',
	version='0.1.12',
	description='Simple scripts supporting open hardware development using CadSoft EAGLE',
	license='GPL',
	author='Tomaz Solc, Bernard Pratz',
	author_email='tomaz.solc@tablix.org, guyzmo+pea@m0g.net',
    url='https://github.com/guyzmo/eagle-automation',
	packages=['eagle_automation'],
	classifiers=[
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Development Status :: 4 - Beta',
		'License :: OSI Approved',
		'Operating System :: Unix',
	],
	install_requires=[
		'PyPDF2',
		'PyYAML',
		'pillow',
		'docopt',
		'setuptools',
	],
	entry_points="""
	# -*- Entry points: -*-
	[console_scripts]
	pea = eagle_automation.pea:main
	""",
    **opts
)

# offer a nice message when doing pip install
if sys.argv[0] == 'setup.py' and 'install' in sys.argv:
    print("🍻  To start using this tool, do `pea --help`")
