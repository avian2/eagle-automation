from eagle_automation.config import config
import os
import subprocess
import tempfile

def get_extension(path):
	return path.split('.')[-1].lower()

class BadExtension: Exception

class EagleScriptExport:
	def __init__(self, workdir=None):
		self.workdir = workdir

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
		subprocess.call(cmd)

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
			script += [	"DISPLAY ALL",
					"RATSNEST"
				]
		elif extension == 'sch':
			script += [	"EDIT .s%d" % self._page ]
		else:
			raise BadExtension

		for layer, out_path in zip(layers, out_paths):
			assert out_path.endswith(".png")

			script += [	"DISPLAY None",
					"DISPLAY %s" % (' '.join(layer['layers']),),
					"EXPORT IMAGE %s MONOCHROME %d" % (out_path, config.DPI)
				]

		return script

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
							+ " \"designator\": \"" + P.name + "\", "
								   + "\"value\": \"" + P.value + "\", "
								   + "\"description\": \"" + P.device.headline + "\" "
							+ "}";
						sep = ",\n";
						printf("%%s", json);
					}
				}
				printf("\n\t]\n}\n");
			}
		}
		"""

	def write_script(self, extension, layers, out_paths):
		if extension != 'sch':
			raise BadExtension

		self.ulp_dir = self.workdir or tempfile.mkdtemp()
		self.ulp_path = os.path.join(self.ulp_dir, "bom.ulp")

		ulp = open(self.ulp_path, "w")
		ulp.write(self.ULP_TEMPLATE_HEAD)

		for layer, out_path in zip(layers, out_paths):

			assert '"' not in out_path
			ulp.write(self.ULP_TEMPLATE % {
				'out_path': out_path,
			})

		ulp.write(self.ULP_TEMPLATE_TAIL)
		ulp.close()

		print self.ulp_path

		return [	"DISPLAY ALL",
				"RUN %s" % (self.ulp_path,) ]

	def clean(self):
		os.unlink(self.ulp_path)
		if not self.workdir:
			os.rmdir(self.ulp_dir)


class EagleDirectoryExport(EagleScriptExport):

	def write_script(self, extension, layers, out_paths):

		if extension != 'lbr':
			raise BadExtension

		script = [	"EXPORT DIRECTORY %s" % out_paths[0] ]

		return script

class EaglePDFExport(EagleScriptExport):
	def write_script(self, extension, layers, out_paths):

		script = []

		if extension == 'brd':
			script += [	"DISPLAY ALL",
					"RATSNEST"
				]
		else:
			raise BadExtension

		for layer, out_path in zip(layers, out_paths):

			ll = set(layer['layers']) | set(config.DOCUMENT_LAYERS)

			script += [	"DISPLAY None",
					"DISPLAY %s" % (' '.join(ll),),
					"PRINT FILE %s BLACK SOLID" % (out_path,),
				]

		return script

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

		print self.ulp_path

		return [	"DISPLAY ALL",
				"RUN %s" % (self.ulp_path,) ]

	def clean(self):
		os.unlink(self.ulp_path)
		if not self.workdir:
			os.rmdir(self.ulp_dir)

class EagleCAMExport:
	def __init__(self, workdir=None):
		pass

	def export(self, in_path, layers, out_paths):

		open(in_path, "rb").close()

		extension = get_extension(in_path)
		if extension != 'brd':
			raise BadExtension

		for layer, out_path in zip(layers, out_paths):
			options = ["-X", "-d" + self.DEVICE, "-o"  + out_path]
			if layer.get('mirror'):
				options.append("-m")
			cmd = [config.EAGLE] + options + [in_path] + layer['layers']
			subprocess.call(cmd)

class EagleGerberExport(EagleCAMExport):
	DEVICE = "GERBER_RS274X"

class EagleExcellonExport(EagleCAMExport):
	DEVICE = "EXCELLON"
