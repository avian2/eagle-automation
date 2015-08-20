#!/usr/bin/env python

"""\
Python Eagle Automation v{version}
Usage: {base} [--verbose] [-c <config> [-c <config>]] [--help] <command> [<args>...]

Options:
    -c <config>        Give path to configuration file, or set a configuration value
                       following the scheme: `-c key=value`
    -v,--verbose       Give verbose output
    -h,--help          This message

The commands are the following:
    export  Export data out of the brd/sch/lbr for manufacturing
    drill   Export drill data for manufacturing
    diff    Do a diff

See '{base} help <command>' for more information on a specific command.

Copyright (C) 2015  Bernard Pratz <guyzmo+github@m0g.net>
Copyright (C) 2014  Tomaz Solc <tomaz.solc@tablix.org>
Distributed under GPL license.
"""

from __future__ import print_function
import pkg_resources  # part of setuptools

import sys
import docopt
import logging
log = logging.getLogger('pea')

import eagle_automation.config as config

__version__ = pkg_resources.require("eagle_automation")[0].version

def main():
    args = docopt.docopt(__doc__.format(base=sys.argv[0], version=__version__),
                  version = __version__,
                  options_first=True)

    if args['--verbose']:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    log.debug('Parameters:\n{}'.format(repr(args)))

    config.init()

    if args['-c']:
        for arg in args['-c']:
            if '=' in args['-c']:
                key, val = args['-c'].split('=')
                config.config.insert(key, val)
            else:
                try:
                    config.config.update(args['-c'])
                except:
                    log.error('Could not open file: {}'.format(args['-c']))

    log.debug('Configuration:\n{}'.format(repr(config.__dict__)))

    sys.argv = [sys.argv[0]] + [args['<command>']] + args['<args>']
    if args['<command>'] == 'export':
        import eagle_automation.export
        return eagle_automation.export.export_main(verbose=args['--verbose'])
    elif args['<command>'] == 'drill':
        import eagle_automation.drill
        return eagle_automation.drill.drill_main(verbose=args['--verbose'])
    elif args['<command>'] == 'diff':
        import eagle_automation.diff
        return eagle_automation.diff.diff_main(verbose=args['--verbose'])
    elif args['<command>'] in ['help', None]:
        exit(call(['python', sys.argv[0], '--help']))
    else:
        exit("{} is not a {base} command. See '{base} help'.".format(args['<command>'], base=sys.argv[0]))


if __name__ == "__main__":
    main()
