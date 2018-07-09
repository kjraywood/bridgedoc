THIS_DIR := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))

ifeq ($(strip $(MAIN)),)
    MAIN = system.adoc
endif

ifeq ($(strip $(INSTALL_DIR)),)
    INSTALL_DIR = ..
endif

ifeq ($(strip $(ICONS_DIR)),)
    ICONS_DIR = ../icons
endif

SOURCES = $(wildcard *.bdoc)
ADOCS = $(SOURCES:.bdoc=.adoc)

HTMLS =  $(addprefix $(INSTALL_DIR)/, $(SOURCES:.bdoc=.html))

MAIN_HTML = $(addprefix $(INSTALL_DIR)/, $(MAIN:.adoc=.html))

MACROS = $(THIS_DIR)/macros.adoc
STYLE_SHEET = $(THIS_DIR)/bridgedoc.css
PREPROC = python $(THIS_DIR)/bridgedoc.py

UPDATED = Last updated $(shell date '+%B %-d, %Y')

ADOC_CMD = asciidoctor -a bridgedoc=$(THIS_DIR) \
		       -a stylesheet=$(STYLE_SHEET) \
		       -a iconsdir=$(ICONS_DIR) \
		       -a nofooter \
		       -a revdate="$(UPDATED)"

.PHONY: all tidy clean status update pull commit
.INTERMEDIATE: $(ADOCS)

all: $(MAIN_HTML) $(HTMLS)

%.adoc : %.bdoc
	$(PREPROC) $< $@

$(INSTALL_DIR)/%.html : %.adoc
	( cat $(MACROS); echo ; cat $< ) | $(ADOC_CMD) -a toc=left -o $@ -

$(HTMLS): $(MACROS) $(STYLE_SHEET)

$(MAIN_HTML): $(MAIN) $(ADOCS) $(STYLE_SHEET) $(MACROS)
	( cat $(MACROS); echo ; cat $< ) | $(ADOC_CMD) -a toc=left \
	-a doctype=book -o $@ -

clean:
	$(RM) $(ADOCS) *~

status:
	git status

update pull:
	git pull

commit:
	git commit -a

echo:
	@echo INSTALL_PATH=$(INSTALL_PATH)
	@echo MAIN_HTML=$(MAIN_HTML)
	@echo HTMLS=$(HTMLS)
