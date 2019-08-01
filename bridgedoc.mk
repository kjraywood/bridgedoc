THIS_DIR := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))

ifeq ($(strip $(MAIN)),)
    MAIN = system.adoc
endif

ifeq ($(strip $(REMINDERS)),)
    REMINDERS = reminders.adoc
endif

ifeq ($(strip $(INDEX)),)
    INDEX = index.adoc
endif

ifeq ($(strip $(INSTALL_DIR)),)
    INSTALL_DIR = ..
endif

# ICONS_DIR and CSS_DIR are relative to INSTALL_DIR

ifeq ($(strip $(ICONS_DIR)),)
    ICONS_DIR = ../icons
endif

ifeq ($(strip $(CSS_DIR)),)
    CSS_DIR = ../css
endif

SOURCES = $(wildcard *.bdoc)
ADOCS = $(SOURCES:.bdoc=.adoc)

MACROS = $(THIS_DIR)/macros.adoc
STYLE_SHEET_SRC = $(THIS_DIR)/bridgedoc.css
PREPROC = python $(THIS_DIR)/bridgedoc.py
EXTN_SECTNUMOFFSET = $(THIS_DIR)/lib/sectnumoffset-treeprocessor.rb

HTMLS =  $(addprefix $(INSTALL_DIR)/, $(SOURCES:.bdoc=.html))

MAIN_HTML = $(addprefix $(INSTALL_DIR)/, $(MAIN:.adoc=.html))

REMINDERS_CSS = $(REMINDERS:.adoc=.css)
REMINDERS_HTML = $(addprefix $(INSTALL_DIR)/, $(REMINDERS:.adoc=.html))

INDEX_HTML = $(addprefix $(INSTALL_DIR)/, $(INDEX:.adoc=.html))

STYLE_SHEET = $(notdir $(STYLE_SHEET_SRC))

STYLE_SHEET_TGT =  $(INSTALL_DIR)/$(CSS_DIR)/$(STYLE_SHEET)

FUNC_FILEDATE = $(shell date -d "$$(stat --printf '%y' $(1))" '+%B %-d, %Y')

ADOC_CMD = asciidoctor -a bridgedoc=$(THIS_DIR) \
		       -a iconsdir=$(ICONS_DIR) \
		       -a sectnums -a nofooter

CSS_OPTS = -a stylesheet=$(CSS_DIR)/$(STYLE_SHEET) -a linkcss

.PHONY: all parts index system reminders css tidy clean status update pull commit
.INTERMEDIATE: $(ADOCS)

all: parts index system

parts: $(HTMLS)

index: $(INDEX_HTML)

system: $(MAIN_HTML)

reminders: $(REMINDERS_HTML)

css: $(STYLE_SHEET_TGT)

%.adoc : %.bdoc
	$(PREPROC) $< $@

$(INSTALL_DIR)/%.html : %.bdoc
	( cat $(MACROS); echo ; $(PREPROC) $< - ) | $(ADOC_CMD) $(CSS_OPTS) \
	-a toc=left -a revdate="$(call FUNC_FILEDATE, $<)" \
	-r $(EXTN_SECTNUMOFFSET) -o $@ -

$(MAIN_HTML): $(MAIN) $(ADOCS)
	( cat $(MACROS); echo ; cat $< ) | $(ADOC_CMD) $(CSS_OPTS) \
	-a toc=left -a doctype=book \
	-a revdate="$(call FUNC_FILEDATE, .)" -o $@ -

$(REMINDERS_HTML): $(REMINDERS) $(REMINDERS_CSS)
	( cat $(MACROS); echo ; cat $< ) | $(ADOC_CMD) \
	-a stylesheet=$(REMINDERS_CSS) \
	-a revdate="$(call FUNC_FILEDATE, .)" -o $@ -

$(INDEX_HTML): $(INDEX)
	( cat $(MACROS); echo ; cat $< ) | $(ADOC_CMD) $(CSS_OPTS) -a toc! \
	-a revdate="$(call FUNC_FILEDATE, .)" -o $@ -

$(STYLE_SHEET_TGT): $(STYLE_SHEET_SRC)
	install -p -m 0644 $< $@

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
