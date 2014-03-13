#!/usr/bin/python

from distutils.core import setup

setup(name='eagle_automation',
      version='0.0.1',
      description='Simple scripts supporting open hardware development using CadSoft EAGLE',
      license='GPL',
      long_description=open("README").read(),
      author='Tomaz Solc',
      author_email='tomaz.solc@tablix.org',

      packages = [ 'eagle_automation' ],
      provides = [ 'eagle_automation' ],

      data_files = [('lib/python/eagle_automation', ['eagle_automation/default.conf'])],

      scripts = ['eaglediff', 'eagleexport', 'eagledrl'],
)
