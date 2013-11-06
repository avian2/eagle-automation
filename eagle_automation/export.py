from eagle_automation.config import *
import os
import subprocess
import tempfile

class BadExtension: Exception

class EagleScriptExport:
	def __init__(self, workdir=None):
		self.workdir = workdir

	def export(self, in_path, layers, out_paths):

		open(in_path, "rb").close()

		extension = in_path.split('.')[-1].lower()

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

		cmd = [EAGLE, "-C" + script_string, in_path]
		subprocess.call(cmd)

class EaglePNGExport(EagleScriptExport):
	def write_script(self, extension, layers, out_paths):

		script = []

		if extension == 'brd':
			script += [	"DISPLAY ALL",
					"RATSNEST"
				]
		elif extension == 'sch':
			pass
		else:
			raise BadExtension

		for layer, out_path in zip(layers, out_paths):
			assert out_path.endswith(".png")

			script += [	"DISPLAY None",
					"DISPLAY %s" % (' '.join(layer['layers']),),
					"EXPORT IMAGE %s MONOCHROME %d" % (out_path, DPI)
				]

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

			ll = set(layer['layers']) | set(DOCUMENT_LAYERS)

			script += [	"DISPLAY None",
					"DISPLAY %s" % (' '.join(ll),),
					"PRINT FILE %s BLACK SOLID" % (out_path,),
				]

		return script

class EagleCAMExport:
	def __init__(self, workdir=None):
		pass

	def export(self, in_path, layers, out_paths):

		open(in_path, "rb").close()

		extension = in_path.split('.')[-1].lower()
		if extension != 'brd':
			raise BadExtension

		for layer, out_path in zip(layers, out_paths):
			options = ["-X", "-d" + self.DEVICE, "-o"  + out_path]
			if layer.get('mirror'):
				options.append("-m")
			cmd = [EAGLE] + options + [in_path] + layer['layers']
			subprocess.call(cmd)

class EagleGerberExport(EagleCAMExport):
	DEVICE = "GERBER_RS274X"

class EagleExcellonExport(EagleCAMExport):
	DEVICE = "EXCELLON"
