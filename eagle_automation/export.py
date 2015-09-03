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


class EagleScriptBOMExport(EagleScriptExport):
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

    def generate_bom_output(self):
        # out_bom[prefix][package][value] -> [devices]
        with open(os.path.join(self.ulp_dir, "bom.json"), 'r') as bom:
            bom = json.load(bom)
            out_bom = dict()

            for part in bom['items']:
                prefix, package, value = part['prefix'], part['package'], part['value']
                out_bom.setdefault(prefix, dict()).setdefault(package, dict()).setdefault(value, list()).append(part)

            with BOMWriter(self.bom_path) as bom_writer:
                # Write header
                bom_writer.writerow(['Prefix', 'Packaging', 'Value', 'Nb', 'Devices', 'Description'], header=True)

                # Write each bom line
                for prefix, packages in out_bom.items():
                    print(prefix)
                    for package, items in packages.items():
                        print(prefix, package)
                        for value, devices in items.items():
                            print(prefix, package, value, devices)
                            range_list = ranges([int(re.sub(r'[a-zA-Z]*', r'', d['designator'])) for d in devices])
                            row = [prefix,
                                    package,
                                    value,
                                    len(devices),
                                    ",".join(["{}-{}".format(x, y) if x != y else str(x) for x, y in range_list]),
                                    devices[0]['description']]
                            bom_writer.writerow(row)

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
        self.generate_bom_output()
        os.unlink(os.path.join(self.ulp_dir, "bom.json"))
        os.unlink(self.ulp_path)
        if not self.workdir:
            os.rmdir(self.ulp_dir)


class PyEagleBOMExport(PyEagleExport):
    def export(self, in_path, layers, out_paths):
        db = PartDatabase(config.partdb)
        with BOMWriter(out_paths) as writer:
            # header row
            writer.writerow(('Item', 'Partnum', 'Qty', 'Fit', 'Manufacturer', 'Reference', 'Description', 'RefDes'), header=True)

            for i, part_line in enumerate(sorted(db.build_bom(in_path), key=lambda p: p['Partnum'])):
                writer.writerow((str(i+1),) + tuple(part_line.get_line(['Partnum',
                                                                        'Quantity',
                                                                        'Fitted',
                                                                        'Manufacturer',
                                                                        'Reference',
                                                                        'Description',
                                                                        'RefDes'], range=True)
                                                    )
                                )

        log.info("Successfully wrote BOM into {}".format(", ".join(out_paths)))


class EagleBOMExport():
    def __init__(self, workdir=None, verbose=False):
        self.workdir = workdir
        self.verbose = verbose
        self._py_export = PyEagleBOMExport(workdir, verbose)
        self._ea_export = EagleScriptBOMExport(workdir, verbose)

    def export(self, *args, **kwarg):
        try:
            self._py_export.export(*args, **kwarg)
        except Exception as err:
            log.warn(err)
            self._ea_export.export(*args, **kwarg)

    def clean(self):
        pass


out_types['bom'] = EagleBOMExport
out_types['py_bom'] = PyEagleBOMExport
out_types['old_bom'] = EagleScriptBOMExport


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
