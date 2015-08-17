PROJECT = Example
DISTDIR = Dist

# mapping between eagle and physical layers is in eagle_automation.conf
ASSEMBLY_LAYERS = \
	topsilk \
	toppaste \
	topmask \
	topcopper \
	bottomcopper \
	bottommask \
	bottompaste \
	bottomsilk \
	measures

####################################################################################

TIMESTAMP = $(shell date +%Y%m%d)
GITREV=$(shell git rev-parse --short HEAD)

OUTDIR = $(DISTDIR)/$(PROJECT)-$(GITREV)

GERBER_ROOT = $(OUTDIR)/Gerber

ASSEMBLY_FILES = $(addprefix $(OUTDIR)/$(PROJECT)-,$(addsuffix .pdf,$(ASSEMBLY_LAYERS)))
ASSEMBLY_EXPORT = $(join $(ASSEMBLY_FILES),$(addprefix :,$(ASSEMBLY_LAYERS)))

GERBER_FILES = \
	$(GERBER_ROOT)/$(PROJECT).cmp \
	$(GERBER_ROOT)/$(PROJECT).sol \
	$(GERBER_ROOT)/$(PROJECT).plc \
	$(GERBER_ROOT)/$(PROJECT).pls \
	$(GERBER_ROOT)/$(PROJECT).stc \
	$(GERBER_ROOT)/$(PROJECT).sts \
	$(GERBER_ROOT)/$(PROJECT).crc \
	$(GERBER_ROOT)/$(PROJECT).crs \
	$(GERBER_ROOT)/$(PROJECT).oln

EXCELLON_FILES = \
	$(GERBER_ROOT)/$(PROJECT).drd \
	$(GERBER_ROOT)/$(PROJECT).drl

PP_FILES = \
	$(GERBER_ROOT)/$(PROJECT).mnt \
	$(GERBER_ROOT)/$(PROJECT).mnb

DIST = $(DISTDIR)/$(PROJECT)-$(GITREV)-$(TIMESTAMP)-gerbers.zip

# set V=1 (eg, "make V=1") to print the full commands etc.
ifneq ($V,1)
 Pecho=@echo
 P=@
else
 Pecho=@:
 P=
endif

all: precheck $(PROJECT)-assembly.pdf $(ASSEMBLY_FILES) $(DIST)
	$(Pecho) " 🍻  Build finished, assembly files output in: $(OUTDIR)"

precheck:
	$(Pecho) " → Making sure target dirs exists"
	$P mkdir -p $(OUTDIR)
	$P mkdir -p $(GERBER_ROOT)

clean:
	$(Pecho) " → Cleaning up all generated files"
	$P rm -f *.pdf $(GERBER_ROOT)/*.dri $(GERBER_ROOT)/*.gpi $(GERBER_FILES) $(EXCELLON_FILES) $(PP_FILES)

$(ASSEMBLY_FILES): $(PROJECT).brd
	$(Pecho) " → Building each layer PDF"
	$P eagleexport $< pdf $(ASSEMBLY_EXPORT)

$(PROJECT)-assembly.pdf: $(ASSEMBLY_FILES)
	$(Pecho) " → Building assembly PDF"
	$P pdftk $^ cat output $@

$(DIST): $(GERBER_FILES) $(EXCELLON_FILES) $(PP_FILES)
	$(Pecho) " → Packing up gerber batch into $(DIST)"
	$P cd $(DISTDIR) ; zip $@ $^

$(GERBER_ROOT)/%.cmp: %.brd
	$(Pecho) " → Generating top copper (.cmp) gerber file"
	$P echo "\n\n\n" | eagleexport $< gerber $@:topcopper

$(GERBER_ROOT)/%.sol: %.brd
	$(Pecho) " → Generating bottom copper (.sol) gerber file"
	$P eagleexport $< gerber $@:bottomcopper

$(GERBER_ROOT)/%.l2: %.brd
	$(Pecho) " → Generating layer 2 (.l2) gerber file"
	$P eagleexport $< gerber $@:layer2

$(GERBER_ROOT)/%.l3: %.brd
	$(Pecho) " → Generating layer 3 (.l3) gerber file"
	$P eagleexport $< gerber $@:layer2

$(GERBER_ROOT)/%.plc: %.brd
	$(Pecho) " → Generating top silk (.plc) gerber file"
	$P eagleexport $< gerber $@:topsilk

$(GERBER_ROOT)/%.pls: %.brd
	$(Pecho) " → Generating bottom silk (.pls) gerber file"
	$P eagleexport $< gerber $@:bottomsilk

$(GERBER_ROOT)/%.stc: %.brd
	$(Pecho) " → Generating top mask (.stc) gerber file"
	$P eagleexport $< gerber $@:topmask

$(GERBER_ROOT)/%.sts: %.brd
	$(Pecho) " → Generating bottom mask (.sts) gerber file"
	$P eagleexport $< gerber $@:bottommask

$(GERBER_ROOT)/%.crc: %.brd
	$(Pecho) " → Generating top paste (.crc) gerber file"
	$P eagleexport $< gerber $@:toppaste

$(GERBER_ROOT)/%.crs: %.brd
	$(Pecho) " → Generating bottom paste (.crs) gerber file"
	$P eagleexport $< gerber $@:bottompaste

$(GERBER_ROOT)/%.oln: %.brd
	$(Pecho) " → Generating outline (.oln) gerber file"
	$P eagleexport $< gerber $@:outline

$(GERBER_ROOT)/%.dri $(GERBER_ROOT)/%.drd: %.brd
	$(Pecho) " → Generating drills (.dri) gerber/excellion file"
	$P eagleexport $< excellon $@:drills

$(GERBER_ROOT)/%.drl: $(GERBER_ROOT)/%.dri
	$(Pecho) " → Generating drills (.drl) gerber/excellion file"
	$P eagledrl < $< > $@

$(GERBER_ROOT)/%.mnt: %.brd
	$(Pecho) " → Generating top assembly (.mnt) PNP file"
	$P eagleexport $< mountsmd $@:topassembly

$(GERBER_ROOT)/%.mnb: %.brd
	$(Pecho) " → Generating bottom assembly (.mnb) PNP file"
	$P eagleexport $< mountsmd $@:bottomassembly

.PHONY: clean
