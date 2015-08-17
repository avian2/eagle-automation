#!/usr/bin/env python

"""
Usage: {} <command> [<args>...]

Options:
    -c <name=value>     Change configuration option
    -h, --help          This message

The commands are the following:
    export  Export data out of the brd/sch/lbr for manufacturing
    drill   Export drill data for manufacturing
    diff    Do a diff
    help    This message

"""

from __future__ import print_function

import sys
import docopt

def main():
    args = docopt.docopt(__doc__.format(sys.argv[0]),
                  version='0.1.0',
                  options_first=True)
    sys.argv = [sys.argv[0]] + [args['<command>']] + args['<args>']
    if args['<command>'] == 'export':
        import eagle_automation.export
        return eagle_automation.export.export_main()
    elif args['<command>'] == 'drill':
        import eagle_automation.drill
        return eagle_automation.drill.drill_main()
    elif args['<command>'] == 'diff':
        import eagle_automation.diff
        return eagle_automation.diff.diff_main()
    elif args['<command>'] in ['help', None]:
        exit(call(['python', sys.argv[0], '--help']))
    else:
        exit("{} is not a {} command. See 'git help'.".format(args['<command>'], sys.argv[0]))


if __name__ == "__main__":
    main()
