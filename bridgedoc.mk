THIS_DIR := $(patsubst %/,%,$(dir $(lastword $(MAKEFILE_LIST))))

ifeq ($(strip $(MAIN)),)
    MAIN = system.adoc
endif

ifeq ($(strip $(INSTALL_DIR)),)
    INSTALL_DIR = $(abspath $(CURDIR)/..)
endif

SOURCES = $(wildcard *.bdoc)
ADOCS = $(SOURCES:.bdoc=.adoc)
HTML = index.html

MACROS = $(THIS_DIR)/macros.adoc
STYLE_SHEET = $(THIS_DIR)/bridgedoc.css
PREPROC = python $(THIS_DIR)/bridgedoc.py

.PHONY: all install tidy clean status update pull commit

all: $(HTML)

$(HTML): $(MAIN) $(MACROS) $(ADOCS) $(STYLE_SHEET)
	asciidoctor -a stylesheet=$(STYLE_SHEET) \
		    -a bridgedoc=$(THIS_DIR) $(MAIN) -o $@

%.adoc : %.bdoc
	$(PREPROC) $< $@

install: $(HTML)
	install -m 0664 -t $(INSTALL_DIR) $<

tidy:
	$(RM) $(ADOCS)

clean: tidy
	$(RM) $(HTML) *~

status:
	git status

update pull:
	git pull

commit:
	git commit -a

#	@echo $(shell read -p "Comment: " MSG; svn commit -m "$$MSG" )
