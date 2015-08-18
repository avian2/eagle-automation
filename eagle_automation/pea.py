#!/usr/bin/env python

"""\
Python Eagle Automation v{version}
Usage: {base} [--verbose] [-c <name>=<value>] [--help] <command> [<args>...]

Options:
    -C <config>        Give path to configuration file
    -c <name=value>    Change configuration option
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

__version__ = pkg_resources.require("eagle_automation")[0].version

def main():
    args = docopt.docopt(__doc__.format(base=sys.argv[0], version=__version__),
                  version = __version__,
                  options_first=True)

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
        exit("{} is not a {} command. See 'git help'.".format(args['<command>'], sys.argv[0]))


if __name__ == "__main__":
    main()
