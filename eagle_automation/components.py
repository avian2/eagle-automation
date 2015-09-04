#!/usr/bin/env python

"""
{base}, Manage Components Library and Database with Eagle Files
Copyright (C) 2015  Bernard Pratz <guyzmo+pea@m0g.net>

Usage:
    {base} {command} ls [--category=<category>]
    {base} {command} show <component>
    {base} {command} insert <component> --category=<category> --description=<description>
    {base} {command} alt <component> list
    {base} {command} alt <component> append <item> --status=<status> --category=<category> --manufacturer=<manufacturer> --reference=<reference> --description=<description>
    {base} {command} alt <component> modify <item> [--status=<status>] [--category=<category>] [--manufacturer=<manufacturer>] [--reference=<reference>] [--description=<description>]
    {base} {command} alt <component> preferred <item>
    {base} {command} alt <component> delete <item>
    {base} {command} alt <component> move <item> <position>

"""

import re
import sys
import yaml
import docopt
import pyeagle
import itertools

from .config import config
from .exceptions import DatabaseInvalid

import logging
log = logging.getLogger('pea').getChild(__name__)

################################################################################


class PartLine(dict):
    SPLIT_PART = re.compile(r'([a-zA-Z]+)(\d+)')

    def __init__(self, *args, **kwarg):
        super(PartLine, self).__init__(*args, **kwarg)
        self._parts = []

    def __hash__(self):
        return hash(tuple(self.values()))

    def insert(self, part_name):
        self._parts.append(part_name)

    def get_line(self, keys, range=True):
        # for given list of keys
        for key in keys:
            # if the key is for the list of parts
            if key == 'RefDes':
                if range:
                    yield ','.join(self._build_range(self._parts))
                else:
                    yield ','.join(self._parts)
                    # if it's for the amount of parts
            elif key == 'Quantity':
                yield str(len(self._parts))
                # else it's a descriptor
            else:
                yield self[key]

    def _build_range(self, l):
        def ranges(i):
            for a, b in itertools.groupby(enumerate(i), lambda x: x[1] - x[0]):
                b = list(b)
                yield b[0][1], b[-1][1]

        # Check that all prefixes are identical
        part_prefixes = map(lambda e: self.SPLIT_PART.sub(r'\1', e), l)
        if not len(set(part_prefixes)) <= 1:
            raise Exception("Prefixes are not identical within a part spec, BOM cannot be inconsistent!")
        prefix = part_prefixes[0]

        # build all part ranges
        part_nums = map(lambda e: int(self.SPLIT_PART.sub(r'\2', e)), l)

        # prepend prefix to range
        for first, last in ranges(sorted(part_nums)):
            if first == last:
                yield prefix+str(first)
            else:
                yield '{}{}-{}'.format(prefix, first, last)


class PartDatabase(dict):
    KEYS = set(['Description', 'Category', 'Preferred', 'Alternatives'])
    PART_KEYS = set(['Status', 'Manufacturer', 'Reference'])

    def __init__(self, db, *args, **kwarg):
        self._name = db
        with open(db, 'r') as db:
            args = (yaml.load(db),) + args
            super(PartDatabase, self).__init__(*args, **kwarg)
            self.validate_db()

    def save(self):
        self.validate_db()
        with open(self._name, 'w') as db:
            db.write(yaml.save(self))

    def validate_db(self):
        for item, data in self.items():
            if not (set(data.keys()) == PartDatabase.KEYS or set(data.keys()+['Alternatives']) == PartDatabase.KEYS):
                raise DatabaseInvalid("Item '{}' has inconsistent keys, got: '{}' want: '{}'".format(
                    item,
                    repr(data.keys()),
                    repr(PartDatabase.KEYS))
                )
            if set(data['Preferred'].keys()) != PartDatabase.PART_KEYS:
                raise DatabaseInvalid("Preferred alternative has inconsistent keys, got: '{}' want: '{}'".format(
                    item,
                    repr(data['Preferred'].keys()),
                    repr(PartDatabase.PART_KEYS))
                )
            if 'Alternatives' in data.keys() and data['Alternatives']:
                for i, part in enumerate(data['Alternatives']):
                    if set(part.keys()) != PartDatabase.PART_KEYS:
                        raise DatabaseInvalid("Item #{} of '{}' alternatives has inconsistent keys, got: '{}' want: '{}'".format(
                            i,
                            item,
                            repr(part.keys()),
                            repr(PartDatabase.PART_KEYS))
                        )

    """BOM building"""

    def get_part_line(self, part, attr_dict):
        if config.PARTNUM in attr_dict.keys() and attr_dict[config.PARTNUM] in self.keys():
            part_line = PartLine(**self[attr_dict[config.PARTNUM]]['Preferred'])
            part_line.update({
                'Partnum': attr_dict[config.PARTNUM],
                'Fitted': True,
                'Package': part.device.package.name,
                'Value': part.value,
                'Device': part.device_set.name,
                'Description': self[attr_dict[config.PARTNUM]]['Description']
            })
        else:
            part_line = PartLine(**{
                'Partnum': 'Unspecified',
                'Fitted': False,
                'Package': part.device.package.name,
                'Value': part.value,
                'Manufacturer': 'any',
                'Reference': 'any',
                'Description': '',
                'Device': part.device_set.name
            })
        return part_line

    def build_bom(self, bom_path):
        sch = pyeagle.open(bom_path)
        parts = dict()

        for name, part in sch.parts.items():
            attr_dict = part.device.technologies[part.technology].as_dict()
            attr_dict.update(part.attributes)
            part_line = self.get_part_line(part, attr_dict)

            parts.setdefault(hash(part_line), part_line).insert(part.name)

        return parts.values()

    """list items"""

    def get_categories(self):
        return set([part['Category'] for item, part in self.items()])

    def get_parts_from_category(self, cat):
        return filter(lambda p: p[1]['Category'] == cat, self.items())

    def get_parts_groupby_category(self):
        def cat_key(x): return x[1]['Category']

        return itertools.groupby(sorted(self.items(),
                                        key=cat_key),
                                 key=cat_key)


################################################################################

class Commands:
    registered_command = dict()

    @classmethod
    def register(cls, *args, **kwarg):
        def wrapper(klass):
            for command in args:
                cls.registered_command[command] = klass
            return klass
        return wrapper


class ComponentDatabase:
    def __init__(self, db, verbose=False):
        self.db = db
        self.verbose = verbose


@Commands.register('show')
class ComponentShow(ComponentDatabase):
    """
    % pea db show 200001
    200001:
     Category: Capacitor
     Description: ABC
     Alternatives:
      #1. Manufacturer: any, Reference: any, Status: Active (Preferred)
      #2. Manufacturer: Wurth, Reference: ABC, Status: Active
      #3. Manufacturer: Vishay, Reference: DEF, Status: Active
    """
    @classmethod
    def print_alternatives(cls, component):
        if component['Preferred']:
            print(
                "    #1. Manufacturer: {Manufacturer}, Reference: {Reference}, Status: {Status} (Preferred)".format(**component['Preferred'])
            )
        if component['Alternatives']:
            for i, alt in enumerate(component['Alternatives']):
                print(
                    "    #{}. Manufacturer: {Manufacturer}, Reference: {Reference}, Status: {Status}".format(i+2, **alt)
                )

    def show(self, name, component):
        print(
            "{}:\n"
            "  Category: {Category}\n"
            "  Description: {Description}\n"
            "  Alternatives:"
            "".format(name, **component)
        )

    def run(self, args):
        try:
            self.show(args['<component>'], self.db[args['<component>']])
        except KeyError:
            log.error('Could not find component: {}'.format(args['<component>']))


@Commands.register('ls')
class ComponentList(ComponentDatabase):
    @classmethod
    def print_parts_list(cls, parts):
        for item, part in sorted(parts, key=lambda x: x[0]):
            print(u'  {:<15}: {:<35} ({}, {} alternative{})'.format(
                item,
                part['Description'],
                part['Category'],
                len(part['Alternatives'])+1,
                's' if len(part['Alternatives'])+1 > 1 else ''
            ))

    def run(self, args):
        if args['--category']:
            if args['--category'] not in self.db.get_categories():
                log.error('Category "{}" does not exists.'.format(args['--category']))
                print('Here\'s the list of defined categories:')
                for cat in self.db.get_categories():
                    print(' - {}'.format(cat))
            else:
                self.print_parts_list(self.db.get_parts_from_category(args['--category']))
        else:
            for category, parts in self.db.get_parts_groupby_category():
                print('{}:'.format(category))
                self.print_parts_list(parts)


@Commands.register('insert')
class ComponentInsert(ComponentDatabase):
    """
    % pea db insert 900000 --category=IC --description=Foo bar
    Successfully added to category IC
    """
    def run(self, args):
        new_comp = dict(
            Category=args['--category'],
            Description=args['--description'],
            Preferred=[],
            Alternatives=[],
        )
        if args['<component>'] not in self.db.keys():
            self.db[args['<component>']] = new_comp
            print("Successfully added {} to category {Category}".format(args['<component>'], **new_comp))


@Commands.register('alt')
class ComponentAlternative(ComponentDatabase):
    def list(self, component):
        print("Alternatives for component {}".format(component))
        ComponentShow.print_alternatives(self.db[component])

    def append(self, component, alt):
        if not self.db[component]:
            self.db[component]['Preferred'] = alt
        else:
            self.db[component]['Alternatives'].append(alt)
        self.db.save()
        # show result
        print('Successfully added to position #{} of item {} alternatives:'.format(
            len(self.db[component]['Alternatives']),
            component
        ))
        ComponentShow.list(component)

    def delete(self, component, item):
        print('Removed #{} from {} alternatives. Alternatives list updated:'.format(item, component))
        self.list(component)
        # TODO

    def preferred(self, component, item):
        print('Preferred changed to #{} of {}\'s alternatives. Alternatives list updated:'.format(item, component))
        self.list(component)
        # TODO

    def move(self, component, item, position):
        print('Alternative #{} move to position #{} of {}. Alternatives list updated:'.format(item, position, component))
        self.list(component)
        # TODO

    def modify(self, component, item):
        print('Modified alternative #{} of {}. Alternatives list updated:'.format(item, component))
        self.list(component)
        # TODO

    def run(self, args):
        if args['append']:
            self.insert(args['<component>'], {
                'Reference': args['--reference'],
                'Manufacturer': args['--manufacturer'],
                'Status': args['--status']
            })
        elif args['list']:
            self.list(args['<component>'])
        elif args['delete']:
            self.delete(args['<component>'], args['<item>'])
        elif args['preferred']:
            self.preferred(args['<component>'], args['<item>'])
        elif args['move']:
            self.preferred(args['<component>'], args['<item>'], args['<position>'])


################################################################################

def components_main(verbose=False):
    args = docopt.docopt(__doc__.format(
        base=sys.argv[0],
        command=sys.argv[1],
    ))
    del args[sys.argv[1]]

    log.debug("Arguments:\n{}".format(repr(args)))

    partsdb = PartDatabase(config.partdb)

    command = None
    for arg in filter(lambda a: not a[0] in ('-', '<'), args.items()):
        if arg[1] and arg[0] in Commands.registered_command.keys():
            command = arg[0]
            break

    try:
        cdb = Commands.registered_command[command]
    except KeyError:
        log.error("Unknown subcommand: " + Commands.registered_command[command])
        log.error("Use --help to look up usage.")
        sys.exit(1)

    cdb(db=partsdb, verbose=verbose).run(args)
