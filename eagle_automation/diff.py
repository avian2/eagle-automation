#!/usr/bin/env python

"""pea diff: compare CadSoft Eagle files

USAGE: {prog} {command} [--page=N] [--output=F] <from-file> <to-file>

Parameters:
	<from-file>	 File to diff from
	<to-file>	   File to diff to

Options:
	-p,--page=N	   Page to compare on multi-page schematics [default: 1]
	-o,--output=F  File to output diff into

Copyright (C) 2015  Bernard Pratz <guyzmo+github@m0g.net>
Copyright (C) 2014  Tomaz Solc <tomaz.solc@tablix.org>
"""

from __future__ import print_function

import os
import sys
import docopt
import difflib
import tempfile
import subprocess

import logging
log = logging.getLogger('pea').getChild(__name__)

from PIL import Image, ImageOps, ImageChops

from eagle_automation.config import config
from eagle_automation.export import get_extension, BadExtension, EaglePNGExport, EagleDirectoryExport

def to_png(in_path, page):
	with tempfile.TemporaryDirectory() as workdir:
        extension = in_path.split('.')[-1].lower()
        if extension == 'brd':
            layers = config.LAYERS.values()
            out_paths = [	os.path.join(workdir, layer + '.png')
                    for layer in config.LAYERS.keys() ]
        elif extension == 'sch':
            layers = [{'layers': ['ALL']}]
            out_paths = [os.path.join(workdir, 'all.png')]
        else:
            os.rmdir(workdir)
            raise BadExtension

        export = EaglePNGExport(workdir=workdir)
        export.set_page(page)
        export.export(in_path, layers, out_paths)

        oim = None
        for i, out_path in enumerate(out_paths):
            im = Image.open(out_path).convert("L")
            if oim is None:
                oim = im
            else:
                oim = Image.blend(oim, im, 1.0/(1.0+i))

            os.unlink(out_path)

		workdir.cleanup()

        return oim

def to_txt(in_path):
	with tempfile.TemporaryDirectory() as workdir:
        out_path = os.path.join(workdir, "out.txt")

        export = EagleDirectoryExport()
        export.export(in_path, None, [ out_path ])

        directory = open(out_path).read()

		workdir.cleanup()

        return directory


def pdf_concatenate(fname, files):
	from PyPDF2 import PdfFileWriter, PdfFileReader

	def append_pdf(input,output):
		[output.addPage(input.getPage(page_num)) for page_num in range(input.numPages)]

	output = PdfFileWriter()

	for f in files:
		append_pdf(PdfFileReader(open(f, "rb")), output)

	with open(fname, "wb") as f:
		output.write(f)

def diff_visual(from_file, to_file, page=0, output=None):
	with tempfile.TemporaryDirectory() as workdir:
		pages = []
		first = last = 1
		preview = False

		if not output:
			output = os.path.join(
						workdir,
						"{from_file}-{to_file}.pdf".format(from_file=os.path.basename(from_file).split('.')[0],
															to_file=os.path.basename(to_file).split('.')[0])
			)
			preview = True

		if not page:
			try:
				with open(from_file) as _from:
					with open(to_file) as _to:
						_from = _from.read()
						_to = _to.read()
						# TODO use pyeagle!
						if not '<schematic' in _from and not '<board' in _from:
							raise SyntaxError('File {} is not an eagle/xml design file!'.format(from_file))
						if not '<schematic' in _to and not '<board' in _to:
							raise SyntaxError('File {} is not an eagle/xml design file!'.format(to_file))
						if not _from.count('<sheet>') == _to.count('<sheet>'):
							raise Exception('File {} does not have the same number of sheets as {}'.format(from_file, to_file))
						last = _from.count('<sheet>') or _from.count('<board')
			except Exception as err:
				log.warning(err.message)
				log.warning("Considering file as an Eagle v5 binary format.")
				first = last = page
		else:
			first = last = page

		for page in range(first, last+1):
			log.info("Checking page {} of {}".format(page, last))
			a_im = to_png(from_file, page=page)
			b_im = to_png(to_file, page=page)

			# make the sizes equal
			# if a sheet contains the filename, it is updated with the temporary name
			# and may thus change the size of the image
			width  = max( (a_im.size[0], b_im.size[0]) )
			height = max( (a_im.size[1], b_im.size[1]) )
			a_im2 = Image.new( "L", (width,height) )
			a_im2.paste( a_im, (0,0) )
			a_im = a_im2
			a_im2 = None
			b_im2 = Image.new( "L", (width,height) )
			b_im2.paste( b_im, (0,0) )
			b_im = b_im2
			b_im2 = None

			added = ImageOps.autocontrast(ImageChops.subtract(b_im, a_im), 0)
			deled = ImageOps.autocontrast(ImageChops.subtract(a_im, b_im), 0)
			same = Image.blend(a_im, b_im, 0.5)

			deled = ImageOps.colorize(deled, "#000", "#f00")
			added = ImageOps.colorize(added, "#000", "#00f")
			same = ImageOps.colorize(same, "#000", "#777")

			im = ImageChops.add(ImageChops.add(added, deled), same)
			fname = "{from_file}-{to_file}-page_{page}.pdf".format(from_file=os.path.basename(from_file.split('.')[0]),
																							to_file=os.path.basename(to_file.split('.')[0]),
																							page=page)
			im.save(os.path.join(workdir, fname))
			pages.append(os.path.join(workdir, fname))

		if len(pages) > 0:
			pdf_concatenate(output, pages)
			log.info("Diff output in file: {}".format(output))
			if preview:
				try:
					subprocess.call([config.OPEN, output])
				except FileNotFoundError as err:
					log.warning("Cannot find open utility: `{}`".format(config.OPEN))
					log.warning("Open your file manually to check it")
				input("Press enter to flush all outputs")
		else:
			log.error("No diff output.")

		workdir.cleanup()

def diff_text(from_file, to_file):
	a_txt = to_txt(from_file)
	b_txt = to_txt(to_file)

	a_lines = a_txt.split('\n')
	b_lines = b_txt.split('\n')

	diff = difflib.unified_diff(a_lines, b_lines, fromfile=from_file, tofile=to_file, lineterm='')
	print('\n'.join(list(diff)))

def diff(from_file, to_file, page=0, output=None):
	extension = get_extension(from_file)

	if get_extension(to_file) != extension:
		log.error("%s: both files should have the same extension" % (to_file,))
		return

	if extension == 'brd':
		diff_visual(from_file, to_file, page, output)
	elif extension == 'sch':
		diff_visual(from_file, to_file, page, output)
	elif extension == 'lbr':
		diff_text(from_file, to_file)
	else:
		log.error("%s: skipping, not a board or schematic" % (from_file,))
		return


################################################################################

def diff_main(verbose=False):
	args = docopt.docopt(__doc__.format(prog=sys.argv[0], command=sys.argv[1]))
	log.debug("Arguments:\n{}".format(repr(args)))

	diff(args['<from-file>'], args['<to-file>'], int(args['--page'] if args['--page'] else 0), args['--output'])

if __name__ == '__main__':
	diff_main()
