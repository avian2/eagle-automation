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
	$(PROJECT).drl \

all: $(PROJECT)-assembly.pdf $(GERBER_FILES) $(EXCELLON_FILES)

$(ASSEMBLY_FILES): $(PROJECT).brd
	eagleexport $< pdf $(ASSEMBLY_EXPORT)

$(PROJECT)-assembly.pdf: $(ASSEMBLY_FILES)
	pdftk $^ cat output $@

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

%.drl: %.dri
	eagledrl < $< > $@

clean:
	rm -f *.pdf *.dri $(GERBER_FILES) $(EXCELLON_FILES)

.PHONY: clean
