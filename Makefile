DESTDIR ?=
PREFIX ?= /usr/local

VERSION = 0.1-RC5

# SUBDIRS = lib asn2qder test rfc arpa2 itu
ifndef UNTESTED
SUBDIRS = lib tool test rfc
else
SUBDIRS = lib tool      rfc
endif

SUBMAKE=$(MAKE) PREFIX='$(PREFIX)' DESTDIR='$(DESTDIR)' VERSION='$(VERSION)'

all:
	#
	# To incorporate subprojects with valuable add-ons, run:
	#
	# git submodule update --init
	#
	@ $(foreach d,$(SUBDIRS),$(SUBMAKE) -C '$d' all &&) echo "Made all subdirectories"

install:
	@ $(foreach d,$(SUBDIRS),$(SUBMAKE) -C '$d' install &&) echo "Installed all subdirectories"

uninstall:
	@ $(foreach d,$(SUBDIRS),$(SUBMAKE) -C '$d' uninstall &&) echo "Uninstalled all subdirectories"

$PHONY: clean

anew: clean all

clean:
	@ $(foreach d,$(SUBDIRS),$(SUBMAKE) -C '$d' clean &&) echo "Cleaned all subdirectories"

