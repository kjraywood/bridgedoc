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

ifeq ($(strip $(RECENT_CHANGES)),)
    RECENT_CHANGES = recent-changes.html
endif

ifeq ($(strip $(CHANGELOG)),)
   CHANGELOG = changelog.adoc
endif

ifeq ($(strip $(STAGING)),)
    STAGING = staging.adoc
endif

ifeq ($(strip $(INSTALL_DIR)),)
    INSTALL_DIR = html
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
PREPROC = python $(THIS_DIR)/bridgedoc.py

MAIN_HTML = $(addprefix $(INSTALL_DIR)/, $(MAIN:.adoc=.html))
STAGING_HTML = $(addprefix $(INSTALL_DIR)/, $(STAGING:.adoc=.html))

REMINDERS_CSS = $(REMINDERS:.adoc=.css)
REMINDERS_HTML = $(addprefix $(INSTALL_DIR)/, $(REMINDERS:.adoc=.html))

INDEX_HTML = $(addprefix $(INSTALL_DIR)/, $(INDEX:.adoc=.html))
CHANGELOG_HTML = $(addprefix $(INSTALL_DIR)/, $(CHANGELOG:.adoc=.html))

MAIN_STYLE_SHEET = bridgedoc.css
INDEX_STYLE_SHEET = multicol-index.css

ALL_STYLE_SHEETS = $(MAIN_STYLE_SHEET) $(INDEX_STYLE_SHEET)

STYLE_SHEET_TGTS =  $(addprefix $(INSTALL_DIR)/$(CSS_DIR)/, $(ALL_STYLE_SHEETS))

FUNC_FILEDATE = $(shell date -d "$$(stat --printf '%y' $(1))" '+%B %-d, %Y')

ADOC_CMD = asciidoctor -a bridgedoc=$(THIS_DIR) \
		       -a iconsdir=$(ICONS_DIR) \
		       -a docinfodir=$(THIS_DIR) \
		       -a docinfo=shared \
		       -a sectnums -a nofooter

MAIN_CSS_OPTS  = -a stylesheet=$(CSS_DIR)/$(MAIN_STYLE_SHEET) -a linkcss
INDEX_CSS_OPTS = -a stylesheet=$(CSS_DIR)/$(INDEX_STYLE_SHEET) -a linkcss

INSERT_RECENT_CHANGES = ( unfound=true; \
                          while IFS= read -r line; \
                          do echo "$$line";\
                             if eval $$unfound \
                                && [[ "$$line" == '<div id="toc" class="toc2">' ]]; \
                             then cat $(RECENT_CHANGES); \
                                  unfound=false; \
                             fi; \
                          done; \
                        )

.PHONY: all parts index system staging reminders changelog css tidy clean status update pull commit
.INTERMEDIATE: $(ADOCS)

all: index system changelog staging

index: $(INDEX_HTML)

system: $(MAIN_HTML)

changelog: $(CHANGELOG_HTML)

reminders: $(REMINDERS_HTML)

staging: $(STAGING_HTML)

css: $(STYLE_SHEET_TGTS)

$(STAGING_HTML): $(STAGING) $(RECENT_CHANGES)

%.adoc : %.bdoc
	$(PREPROC) $< $@

$(MAIN_HTML): $(MAIN) $(ADOCS) $(RECENT_CHANGES)
	( cat $(MACROS); echo ; cat $< ) | $(ADOC_CMD) $(MAIN_CSS_OPTS) \
	-a toc=left -a doctype=book \
	-a revdate="$(call FUNC_FILEDATE, .)" -o - - \
	| $(INSERT_RECENT_CHANGES) >| $@

$(STAGING_HTML): $(STAGING) $(RECENT_CHANGES)
	( cat $(MACROS); echo ; cat $< ) | $(ADOC_CMD) $(MAIN_CSS_OPTS) \
	-a toc=left -a doctype=book \
	-a revdate="$(call FUNC_FILEDATE, .)" -o - - \
	| $(INSERT_RECENT_CHANGES) >| $@

$(REMINDERS_HTML): $(REMINDERS) $(REMINDERS_CSS)
	( cat $(MACROS); echo ; cat $< ) | $(ADOC_CMD) \
	-a stylesheet=$(REMINDERS_CSS) \
	-a revdate="$(call FUNC_FILEDATE, .)" -o $@ -

$(INDEX_HTML): $(INDEX)
	( cat $(MACROS); echo ; cat $< ) | $(ADOC_CMD) $(INDEX_CSS_OPTS) -a toc! \
	-o $@ -

$(CHANGELOG_HTML): $(CHANGELOG)
	( cat $(MACROS); echo ; cat $< ) | $(ADOC_CMD) $(INDEX_CSS_OPTS) -a toc! \
	-o $@ -

$(INSTALL_DIR)/$(CSS_DIR)/%.css: $(THIS_DIR)/%.css
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
