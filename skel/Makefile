PROJECT = ExampleProject
DISTDIR = Dist

# mapping between eagle and physical layers is in eagle_automation.conf
ASSEMBLY_LAYERS = \
	topsilk \
	toppaste \
	topmask \
	topcopper \
	layer2 \
	layer3 \
	bottomcopper \
	bottommask \
	bottompaste \
	bottomsilk \
	measures

# remove layer2 and layer3 for a 2 layers board

####################################################################################

TIMESTAMP = $(shell date +%Y%m%d)
GITREV=$(shell git rev-parse --short HEAD)

OUTDIR = $(DISTDIR)/$(PROJECT)-$(GITREV)

GERBER_ROOT = $(OUTDIR)/Gerber
BOM_ROOT = $(OUTDIR)/BOM

ASSEMBLY_FILES = $(addprefix $(OUTDIR)/$(PROJECT)-,$(addsuffix .pdf,$(ASSEMBLY_LAYERS)))
ASSEMBLY_EXPORT = $(join $(ASSEMBLY_FILES),$(addprefix :,$(ASSEMBLY_LAYERS)))

GERBER_FILES = \
	$(GERBER_ROOT)/$(PROJECT).cmp \
	$(GERBER_ROOT)/$(PROJECT).sol \
	$(GERBER_ROOT)/$(PROJECT).plc \
	$(GERBER_ROOT)/$(PROJECT).pls \
	$(GERBER_ROOT)/$(PROJECT).l2 \
	$(GERBER_ROOT)/$(PROJECT).l3 \
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
	$(Pecho) "🍻  Build finished, assembly files output in: $(OUTDIR)"

precheck:
	$(Pecho) " → Making sure target dirs exists"
	$P mkdir -p $(OUTDIR)
	$P mkdir -p $(GERBER_ROOT)
	$P mkdir -p $(BOM_ROOT)

clean:
	$(Pecho) " → Cleaning up all generated files"
	$P rm -f *.pdf $(GERBER_ROOT)/*.dri $(GERBER_ROOT)/*.gpi $(GERBER_FILES) $(EXCELLON_FILES) $(PP_FILES)

$(ASSEMBLY_FILES): $(PROJECT).brd
	$(Pecho) " → Building each layer PDF"
	$P pea export $< pdf $(ASSEMBLY_EXPORT)

$(PROJECT)-assembly.pdf: $(ASSEMBLY_FILES)
	$(Pecho) " → Building assembly PDF"
	$P pdftk $^ cat output $@

$(DIST): $(GERBER_FILES) $(EXCELLON_FILES) $(PP_FILES)
	$(Pecho) " → Packing up gerber batch into $(DIST)"
	$P cd $(DISTDIR) && zip $(subst $(DISTDIR)/,,$@)  $(subst $(DISTDIR)/,,$^) > /dev/null

$(GERBER_ROOT)/%.cmp: %.brd
	$(Pecho) " → Generating top copper, component side (.cmp) gerber file"
	$P echo "\n\n\n\n" | pea export $< gerber $@:topcopper

$(GERBER_ROOT)/%.sol: %.brd
	$(Pecho) " → Generating bottom copper, solder side (.sol) gerber file"
	$P pea export $< gerber $@:bottomcopper

$(GERBER_ROOT)/%.l2: %.brd
	$(Pecho) " → Generating layer 2, internal (.l2) gerber file"
	$P pea export $< gerber $@:layer2

$(GERBER_ROOT)/%.l3: %.brd
	$(Pecho) " → Generating layer 3, internal (.l3) gerber file"
	$P pea export $< gerber $@:layer3

$(GERBER_ROOT)/%.plc: %.brd
	$(Pecho) " → Generating top silkscreen, component side (.plc) gerber file"
	$P pea export $< gerber $@:topsilk

$(GERBER_ROOT)/%.pls: %.brd
	$(Pecho) " → Generating bottom silkscreen, solder side (.pls) gerber file"
	$P pea export $< gerber $@:bottomsilk

$(GERBER_ROOT)/%.stc: %.brd
	$(Pecho) " → Generating top mask solder stop, component side (.stc) gerber file"
	$P pea export $< gerber $@:topmask

$(GERBER_ROOT)/%.sts: %.brd
	$(Pecho) " → Generating bottom mask solder stop, solder side (.sts) gerber file"
	$P pea export $< gerber $@:bottommask

$(GERBER_ROOT)/%.crc: %.brd
	$(Pecho) " → Generating top paste, component side (.crc) gerber file"
	$P pea export $< gerber $@:toppaste

$(GERBER_ROOT)/%.crs: %.brd
	$(Pecho) " → Generating bottom paste, solder side (.crs) gerber file"
	$P pea export $< gerber $@:bottompaste

$(GERBER_ROOT)/%.oln: %.brd
	$(Pecho) " → Generating outline (.oln) gerber file"
	$P pea export $< gerber $@:outline

$(GERBER_ROOT)/%.dri $(GERBER_ROOT)/%.drd: %.brd
	$(Pecho) " → Generating drills (.dri) gerber/excellion file"
	$P pea export $< excellon $@:drills

$(GERBER_ROOT)/%.drl: $(GERBER_ROOT)/%.dri
	$(Pecho) " → Generating drills (.drl) gerber/excellion file"
	$P eagledrl < $< > $@

$(GERBER_ROOT)/%.mnt: %.brd
	$(Pecho) " → Generating top assembly (.mnt) PNP file"
	$P pea export $< mountsmd $@:topassembly

$(GERBER_ROOT)/%.mnb: %.brd
	$(Pecho) " → Generating bottom assembly (.mnb) PNP file"
	$P pea export $< mountsmd $@:bottomassembly

$(BOM_ROOT)/%.csv $(BOM_ROOT)/%.json $(BOM_ROOT)/%.xlsx: %.sch
	$(Pecho) " → Generating Bill of Materials (.csv, .xlsx and .json)"
	$P pea export $< bom $@

.PHONY: clean
