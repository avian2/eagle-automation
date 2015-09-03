#!/usr/bin/env python

"""
{base}, Manage Components Library and Database with Eagle Files
Copyright (C) 2015  Bernard Pratz <guyzmo+pea@m0g.net>

Usage: {base} {command} <command>

### db file management

% pea db list -category Capacitor
200001: ABC
200002: DEF
% pea db show 200001
200001:
 Category: Capacitor
 Description: ABC
 Alternatives:
  #1. Manufacturer: any, Reference: any, Status: Active (Preferred)
  #2. Manufacturer: Wurth, Reference: ABC, Status: Active
  #3. Manufacturer: Vishay, Reference: DEF, Status: Active
% pea db insert 900000 --status=active --category=IC --manufacturer=TI --reference=1G17
Added to position #3 of item 900000 alternatives:
  #1. Manufacturer: TI, Reference: ABC, Status: Active (Preferred)
  #2. Manufacturer: NXP, Reference: DF, Status: Active
  #3. Manufacturer: TI, Reference: 1G17, Status: Active
% pea db alternative 900000 preferred 3
Preferred changed to #3 of 900000's alternatives. Alternatives list updated:
  #1. Manufacturer: TI, Reference: 1G17, Status: Active (Preferred)
  #2. Manufacturer: TI, Reference: ABC, Status: Active
  #3. Manufacturer: NXP, Reference: DF, Status: Active
% pea db alternative 900000 delete 3
Removed #3 from 900000 alternatives. Alternatives list updated:
  #1. Manufacturer: TI, Reference: 1G17, Status: Active (Preferred)
  #2. Manufacturer: TI, Reference: ABC, Status: Active

###

Commands:
    library
    db

Options:
    <input>               .brd, .sch or .lbr file to extract data from
    <type>                chosen output type
    <output>              filename to export data to
    <layer>               loyer to export data from, linked with the output file

<type> can be any of:
    {types}
    <layer> can be any of:
        {layers}

"""

import re
import sys
import yaml
import docopt
import pyeagle
import itertools


import logging
log = logging.getLogger('pea').getChild(__name__)

################################################################################

PARTNUM = '#PARTNUM'


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
                raise Exception("Item '{}' has inconsistent keys, got: '{}' want: '{}'".format(
                    item,
                    repr(data.keys()),
                    repr(PartDatabase.KEYS))
                )
            if set(data['Preferred'].keys()) != PartDatabase.PART_KEYS:
                raise Exception("Preferred alternative has inconsistent keys, got: '{}' want: '{}'".format(
                    item,
                    repr(data['Preferred'].keys()),
                    repr(PartDatabase.PART_KEYS))
                )
            if 'Alternatives' in data.keys() and data['Alternatives']:
                for i, part in enumerate(data['Alternatives']):
                    if set(part.keys()) != PartDatabase.PART_KEYS:
                        raise Exception("Item #{} of '{}' alternatives has inconsistent keys, got: '{}' want: '{}'".format(
                            i,
                            item,
                            repr(part.keys()),
                            repr(PartDatabase.PART_KEYS))
                        )

    def get_part_line(self, part, attr_dict):
        if PARTNUM in attr_dict.keys() and attr_dict[PARTNUM] in self.keys():
            part_line = PartLine(**self[attr_dict[PARTNUM]]['Preferred'])
            part_line.update({
                'Partnum': attr_dict[PARTNUM],
                'Fitted': True,
                'Package': part.device.package.name,
                'Value': part.value,
                'Device': part.device_set.name,
                'Description': self[attr_dict[PARTNUM]]['Description']
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


################################################################################

def components_main(verbose=False):
    args = docopt.docopt(__doc__.format(
        base=sys.argv[0],
        command=sys.argv[1],
    ))

    log.debug("Arguments:\n{}".format(repr(args)))

    raise Exception("TODO")
