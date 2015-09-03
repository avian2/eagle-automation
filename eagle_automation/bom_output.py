#!/usr/bin/env python

import sys
import json

from .common import get_extension

import logging
log = logging.getLogger('pea').getChild(__name__)

class BOMWriter():
    extensions = dict()

    def __init__(self, in_files):
        self.writers = []
        for f in in_files:
            f_ext = get_extension(f)
            if f_ext in self.extensions.keys():
                self.writers.append(self.extensions[f_ext](f))
            else:
                raise Exception("File output not supported in the {} format".format(f_ext))

    def __enter__(self, *args, **kwarg):
        for w in self.writers:
            w.open()
        return self

    def __exit__(self, *args, **kwarg):
        for w in self.writers:
            w.close()

    def writerow(self, *args, **kwarg):
        for w in self.writers:
            w.writerow(*args, **kwarg)

    @classmethod
    def register(cls, *args, **kwarg):
        def wrapper(klass):
            for extension in args:
                if extension.startswith('.'):
                    extension = extension[1:]
                cls.extensions[extension] = klass
            return klass
        return wrapper


class BOMWriterBase(object):
    def __init__(self, out):
        self.fname = out

    def open(self):
        self.f = open(self.fname, 'w')
        return self

    def close(self):
        self.f.close()

    def writerow(self, header=False):
        raise NotImplementedError


@BOMWriter.register('.csv')
class CSVWriter(BOMWriterBase):
    def open(self):
        super(CSVWriter, self).open()
        if sys.version_info.major == 3:
            from csv import writer
        else:
            try:
                from unicodecsv import writer
                self.unicode_support = True
            except ImportError:
                log.warning("For writing CSV with unicode characters, please do: pip install unicodecsv")
                log.warning("Falling back to default python2 CSV writer: Unicode not supported!")
                from csv import writer
                self.unicode_support = False

        self.writer = writer(self.f, delimiter=';', dialect='excel')

    def writerow(self, row, header=False):
        if not self.unicode_support:
            row = [unicode(cell).encode('utf-8', 'replace') for cell in row]
        else:
            row = [unicode(cell) for cell in row]
        self.writer.writerow(row)


@BOMWriter.register('.json')
class JSONWriter(BOMWriterBase):
    """Very basic json writer"""
    def open(self):
        super(JSONWriter, self).open()

        self.lines = []

    def writerow(self, row, header=False):
        self.lines.append(row)

    def close(self):
        with open(self.fname, 'w') as f:
            f.write(json.dumps(self.lines))


@BOMWriter.register('.yaml')
class YAMLWriter(BOMWriterBase):
    """Very basic yaml writer"""
    def open(self):
        super(YAMLWriter, self).open()

        self.lines = []

    def writerow(self, row, header=False):
        self.lines.append(list(row))

    def close(self):
        try:
            import yaml
            with open(self.fname, 'w') as f:
                f.write(yaml.dump(self.lines))
        except ImportError:
            raise Exception("Please install yaml: `pip install pyyaml`")


@BOMWriter.register('.xlsx')
class XLSXWriter(BOMWriterBase):
    def open(self):
        try:
            from xlsxwriter.workbook import Workbook
        except ImportError:
            raise Exception("Please install xlsxwriter: `pip install xlsxwriter`")
        self.workbook = Workbook(self.fname)
        self.title_format = self.workbook.add_format({'bold': True, 'bg_color': '#999999'})
        self.alter_format = self.workbook.add_format({'bg_color': '#dddddd'})
        self.writer = self.workbook.add_worksheet()
        self.writer.set_column(0, 0,  4.00)
        self.writer.set_column(1, 1, 14.50)
        self.writer.set_column(2, 2,  3.00)
        self.writer.set_column(3, 3,  4.30)
        self.writer.set_column(4, 5, 20.00)
        self.writer.set_column(6, 7, 48.00)
        self.line = 0

    def writerow(self, row, header=False):
        for col, cell in enumerate(row):
            if header:
                format = self.title_format
            else:
                if self.line % 2 == 0:
                    format = self.alter_format
                else:
                    format = None
            self.writer.write_string(self.line, col, unicode(cell), format)
        self.line += 1

    def close(self):
        self.workbook.close()


@BOMWriter.register('.ods')
class ODSWriter(CSVWriter):
    def open(self):
        BOMWriterBase.open(self)
        try:
            import odswriter as ods
        except ImportError:
            raise Exception("Please install odswriter: `pip install odswriter`")
        self.writer = ods.writer(self.f)
        self.unicode_support = True

    def close(self):
        self.writer.close()


