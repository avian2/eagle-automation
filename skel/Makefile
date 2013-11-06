PROJECT = foo

# mapping between eagle and physical layers is in eagle_automation/config.py
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

ASSEMBLY_FILES = $(addprefix $(PROJECT)-,$(addsuffix .pdf,$(ASSEMBLY_LAYERS)))
ASSEMBLY_EXPORT = $(join $(ASSEMBLY_FILES),$(addprefix :,$(ASSEMBLY_LAYERS)))

GERBER_FILES = \
	$(PROJECT).cmp \
	$(PROJECT).sol \
	$(PROJECT).plc \
	$(PROJECT).pls \
	$(PROJECT).stc \
	$(PROJECT).sts \
	$(PROJECT).crc \
	$(PROJECT).crs \
	$(PROJECT).oln

EXCELLON_FILES = \
	$(PROJECT).drd \
	$(PROJECT).drl

PP_FILES = \
	$(PROJECT).mnt \
	$(PROJECT).mnb

DIST = $(PROJECT)-gerber.zip

all: $(PROJECT)-assembly.pdf $(DIST)

$(ASSEMBLY_FILES): $(PROJECT).brd
	eagleexport $< pdf $(ASSEMBLY_EXPORT)

$(PROJECT)-assembly.pdf: $(ASSEMBLY_FILES)
	pdftk $^ cat output $@

$(DIST): $(GERBER_FILES) $(EXCELLON_FILES) $(PP_FILES)
	zip $@ $^

%.cmp: %.brd
	eagleexport $< gerber $@:topcopper

%.sol: %.brd
	eagleexport $< gerber $@:bottomcopper

%.plc: %.brd
	eagleexport $< gerber $@:topsilk

%.pls: %.brd
	eagleexport $< gerber $@:bottomsilk

%.stc: %.brd
	eagleexport $< gerber $@:topmask

%.sts: %.brd
	eagleexport $< gerber $@:bottommask

%.crc: %.brd
	eagleexport $< gerber $@:toppaste

%.crs: %.brd
	eagleexport $< gerber $@:bottompaste

%.oln: %.brd
	eagleexport $< gerber $@:outline

%.drd %.dri: %.brd
	eagleexport $< excellon $@:drills

%.mnt: %.brd
	eagleexport $< mountsmd $@:topassembly

%.mnb: %.brd
	eagleexport $< mountsmd $@:bottomassembly

%.drl: %.dri
	eagledrl < $< > $@

clean:
	rm -f *.pdf *.dri *.gpi $(GERBER_FILES) $(EXCELLON_FILES) $(PP_FILES) $(DIST)

.PHONY: clean
