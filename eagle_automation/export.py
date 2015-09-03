"""
{base}, export layers from CadSoft Eagle files
Copyright (C) 2013  Tomaz Solc <tomaz.solc@tablix.org>
Copyright (C) 2015  Bernard Pratz <guyzmo+pea@m0g.net>

Usage: {base} {command} <input> <type> [<output>:<layer> ...]

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

from __future__ import print_function

import os
import re
import sys
import json
import docopt
import tempfile
import subprocess

from .config import config
from .components import PartDatabase
from .bom_output import BOMWriter
from .common import get_extension, ranges
from .exceptions import FileNotFoundError, BadExtension

import logging
log = logging.getLogger('pea').getChild(__name__)






out_types = dict()


class PyEagleExport:
    def __init__(self, workdir=None, verbose=False):
        self.workdir = workdir
        self.verbose = verbose

    def export(self, in_path, layers, out_paths):
        pass

    def clean(self):
        pass


class EagleScriptExport:
    def __init__(self, workdir=None, verbose=False):
        self.workdir = workdir
        self.verbose = verbose

    def export(self, in_path, layers, out_paths):

        open(in_path, "rb").close()

        extension = get_extension(in_path)
        script = self.write_script(extension, layers, out_paths)

        for out_path in out_paths:
            # to stop Eagle trowing up dialogs that
            # files already exist
            try:
                os.unlink(out_path)
            except OSError:
                pass

        script += ['QUIT']

        script_string = ';'.join(script)

        cmd = [config.EAGLE, "-C" + script_string, in_path]
        try:
            subprocess.call(cmd)
        except FileNotFoundError:
            log.error("Eagle executable `{}` not found".format(config.EAGLE))
            log.error("Please check your configuration file or `-c` parameter.")
            log.error("See --help for more details")
            sys.exit(4)

        self.clean()

    def clean(self):
        pass


class EaglePNGExport(EagleScriptExport):
    _page = 1

    def set_page(self, page):
        self._page = page

    def write_script(self, extension, layers, out_paths):

        script = []

        if extension == 'brd':
            script += [
                "DISPLAY ALL",
                "RATSNEST"
            ]
        elif extension == 'sch':
            script += [
                "EDIT .s%d" % self._page
            ]
        else:
            raise BadExtension

        for layer, out_path in zip(layers, out_paths):
            assert out_path.endswith(".png")

            script += [
                "DISPLAY None",
                "DISPLAY %s" % (' '.join(layer['layers']),),
                "EXPORT IMAGE %s MONOCHROME %d" % (out_path, config.DPI)
            ]

        return script


out_types['png'] = EaglePNGExport

class EagleBOMExport(EagleScriptExport):
	ULP_TEMPLATE_HEAD = ""
	ULP_TEMPLATE_TAIL = ""
	ULP_TEMPLATE = r"""
	schematic(SCH) {

		string FileName;
		string json;
		string sep = "";

		FileName = filesetext("%(out_path)s", ".json");

		output(FileName, "wt") {
			printf("{\n");
			printf("\t\"items\": [\n");
			SCH.parts(P) {
				if (P.device.package) {
					json = sep + "\t\t{"
					+   "\"prefix\": \""      + P.device.prefix   + "\", "
					+   "\"designator\": \""  + P.name            + "\", "
					+   "\"value\": \""       + P.value           + "\", "
					+   "\"description\": \"" + P.device.headline + "\", "
					+   "\"package\": \""     + P.device.package.name  + "\" "
					+ "}";
					sep = ",\n";
					printf("%%s", json);
				}
			}
			printf("\n\t]\n}\n");
		}
	}
	"""

	def collapse_bom(self):
		import json
		import csv

		# out_bom[prefix][package][value] -> [devices]
		out_bom = dict()
		with open(os.path.join(self.ulp_dir, "bom.json"), 'r') as bom:
			bom = json.load(bom)
			for bom_path in self.bom_path:
				for part in bom['items']:
					prefix, package, value = part['prefix'], part['package'], part['value']
					out_bom.setdefault(prefix, dict()).setdefault(package, dict()).setdefault(value, list()).append(part)

				if '.json' in bom_path:
					with open(bom_path, 'w') as out:
						out.write(json.dumps(out_bom))

				elif '.csv' in bom_path:
					with open(bom_path, 'w') as csvfile:
						bom_writer = csv.writer(csvfile, dialect='excel', delimiter='	', quotechar='"', quoting=csv.QUOTE_MINIMAL)
						bom_writer.writerow(['Prefix', 'Packaging', 'Value', 'Nb', 'Devices', 'Description'])
						# d[<prefix>][<package>][<value>][1]
						for prefix, packages in out_bom.items():
							for package, items in packages.items():
								for value, devices in items.items():
									range_list = ranges([int(re.sub(r'[a-zA-Z]*', r'', d['designator'])) for d in devices])
									row = [prefix,
											package,
											value,
											len(devices),
											",".join(["{}-{}".format(x,y) if x != y else str(x) for x,y in range_list]),
											devices[0]['description']]
									bom_writer.writerow(row)

				elif '.xlsx' in bom_path:
					try:
						from xlsxwriter.workbook import Workbook
					except ImportError:
						log.error("Please install xlsxwriter: `pip install xlsxwriter`")
						sys.exit(2)
					try:
						workbook = Workbook(bom_path)
						title = workbook.add_format({'bold': True, 'bg_color': 'gray'})
						bom_writer = workbook.add_worksheet()
						bom_writer.set_column(0, 0, 4.50)
						bom_writer.set_column(1, 1, 14.50)
						bom_writer.set_column(2, 2, 16)
						bom_writer.set_column(3, 3, 2)
						bom_writer.set_column(4, 5, 50.00)
						keys = ['Prefix', 'Packaging', 'Value', 'Nb', 'Devices', 'Description']
						for c, key in enumerate(keys):
							bom_writer.write_string(0, c, key, title)
							row_idx =1
							for prefix, packages in out_bom.items():
								for package, items in packages.items():
									for value, devices in items.items():
										range_list = ranges([int(re.sub(r'[a-zA-Z]*', r'', d['designator'])) for d in devices])
										range_list = ",".join(["{}-{}".format(x,y) if x != y else str(x) for x,y in range_list])
										bom_writer.write(row_idx, 0, prefix)
										bom_writer.write(row_idx, 1, package)
										bom_writer.write(row_idx, 2, value)
										bom_writer.write(row_idx, 3, str(len(devices)))
										bom_writer.write(row_idx, 4, range_list)
										bom_writer.write(row_idx, 5, devices[0]['description'])
										row_idx += 1
					finally:
						workbook.close()
				elif '.xls' in bom_path:
					log.error("TODO xls support!")
				log.info("BOM generated into {}".format(bom_path))

	def write_script(self, extension, layers, out_paths):
		if extension != 'sch':
			raise BadExtension

		self.ulp_dir = self.workdir or tempfile.mkdtemp()
		self.ulp_path = os.path.join(self.ulp_dir, "bom.ulp")

		ulp = open(self.ulp_path, "w")
		ulp.write(self.ULP_TEMPLATE_HEAD)

		self.bom_path = []
		for layer, out_path in zip(layers, out_paths):
			self.bom_path.append(out_path)

		assert '"' not in out_path
		ulp.write(self.ULP_TEMPLATE % {
			'out_path': os.path.join(self.ulp_dir, "bom.json"),
		})

		ulp.write(self.ULP_TEMPLATE_TAIL)
		ulp.close()

		log.debug("Script path: {}".format(self.ulp_path))
		log.debug("Raw bom output in {}".format(os.path.join(self.ulp_dir, "bom.json")))

		return [
			"DISPLAY ALL",
			"RUN %s" % (self.ulp_path,)
		]

	def clean(self):
		self.collapse_bom()
		os.unlink(os.path.join(self.ulp_dir, "bom.json"))
		os.unlink(self.ulp_path)
		if not self.workdir:
			os.rmdir(self.ulp_dir)


out_types['bom'] = EagleBOMExport


class EagleDirectoryExport(EagleScriptExport):
    def write_script(self, extension, layers, out_paths):
        if extension != 'lbr':
            raise BadExtension

        script = [
            "EXPORT DIRECTORY %s" % out_paths[0]
        ]

        return script


class EaglePDFExport(EagleScriptExport):
    def write_script(self, extension, layers, out_paths):

        script = []

        if extension == 'brd':
            script += [
                "DISPLAY ALL",
                "RATSNEST"
            ]
        else:
            raise BadExtension

        for layer, out_path in zip(layers, out_paths):

            ll = set(layer['layers']) | set(config.DOCUMENT_LAYERS)

            script += [
                "DISPLAY None",
                "DISPLAY %s" % (' '.join(ll),),
                "PRINT FILE %s BLACK SOLID" % (out_path,),
            ]

        return script


out_types['pdf'] = EaglePDFExport


class EagleMountSMDExport(EagleScriptExport):

    # Following ULP code based on "mountsmd.ulp" by CadSoft

    ULP_TEMPLATE_HEAD = """
    board(B) {
        string fileName;
    """

    ULP_TEMPLATE = """
        fileName = "%(out_path)s";
        output(fileName) {

            B.elements(E) {

                int wasSmd,
                xmax =-2147483648,
                xmin = 2147483647,
                ymax = xmax,
                ymin = xmin;

                wasSmd = 0;

                E.package.contacts(C) {
                    if (C.smd && C.smd.layer == %(pp_id)d) {
                        wasSmd = 1;

                        if (C.x > xmax) xmax = C.x;
                        if (C.y > ymax) ymax = C.y;
                        if (C.x < xmin) xmin = C.x;
                        if (C.y < ymin) ymin = C.y;
                    }
                }

                if (wasSmd)
                    printf("%%s %%5.2f %%5.2f %%3.0f %%s %%s\\n",
                        E.name, u2mm((xmin + xmax)/2), u2mm((ymin + ymax)/2),
                        E.angle, E.value, E.package.name);
            }
        }
    """

    ULP_TEMPLATE_TAIL = """
    }
    """

    def write_script(self, extension, layers, out_paths):

        if extension != 'brd':
            raise BadExtension

        self.ulp_dir = self.workdir or tempfile.mkdtemp()
        self.ulp_path = os.path.join(self.ulp_dir, "export.ulp")

        ulp = open(self.ulp_path, "w")
        ulp.write(self.ULP_TEMPLATE_HEAD)

        for layer, out_path in zip(layers, out_paths):

            pp_id = layer['pp_id']

            assert '"' not in out_path
            ulp.write(self.ULP_TEMPLATE % {
                'out_path': out_path,
                'pp_id': pp_id
            })

        ulp.write(self.ULP_TEMPLATE_TAIL)
        ulp.close()

        log.debug("Script path: {}".format(self.ulp_path))

        return [
            "DISPLAY ALL",
            "RUN %s" % (self.ulp_path,)
        ]

    def clean(self):
        os.unlink(self.ulp_path)
        if not self.workdir:
            os.rmdir(self.ulp_dir)


out_types['mountsmd'] = EagleMountSMDExport


class EagleCAMExport:
    def __init__(self, workdir=None, verbose=False):
        self.verbose = verbose

    def export(self, in_path, layers, out_paths):

        open(in_path, "rb").close()

        extension = get_extension(in_path)
        if extension != 'brd':
            raise BadExtension

        for layer, out_path in zip(layers, out_paths):
            options = ["-X", "-d" + self.DEVICE, "-o" + out_path]
            if layer.get('mirror'):
                options.append("-m")
                cmd = [config.EAGLE] + options + [in_path] + layer['layers']
                subprocess.call(cmd)


class EagleGerberExport(EagleCAMExport):
    DEVICE = "GERBER_RS274X"


out_types['gerber'] = EagleGerberExport


class EagleExcellonExport(EagleCAMExport):
    DEVICE = "EXCELLON"


out_types['excellon'] = EagleExcellonExport


################################################################################

def export_main(verbose=False):
    args = docopt.docopt(__doc__.format(
        base=sys.argv[0],
        command=sys.argv[1],
        types=', '.join(out_types.keys()),
        layers=', '.join(config.LAYERS.keys())
    ))

    log.debug("Arguments:\n{}".format(repr(args)))

    layers = []
    out_paths = []
    for arg in args['<output>:<layer>']:
        try:
            out_path, layer_name = arg.split(":")
        except ValueError:
            out_path = arg
            layer_name = None

        extension = args['<input>'].split('.')[-1].lower()
        if extension == 'brd':
            if layer_name is None:
                log.error("Layer name required when exporting brd files")
                sys.exit(1)

            try:
                layer = config.LAYERS[layer_name]
            except KeyError:
                log.error("Unknown layer: " + layer_name)
                sys.exit(1)
        elif extension == 'sch':
            layer = {'layers': ['ALL']}
        else:
            log.error("Bad extension %s: Eagle requires file names ending in sch or brd" % extension)
            sys.exit(1)

        layers.append(layer)
        out_paths.append(out_path)

    try:
        export_class = out_types[args['<type>']]
    except KeyError:
        log.error("Unknown type: " + out_types[args['<type>']])
        log.error("Use --help to look up usage.")
        sys.exit(1)

    export_class(verbose=verbose).export(args['<input>'], layers, out_paths)


if __name__ == "__main__":
    export_main()
