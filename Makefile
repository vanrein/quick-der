DESTDIR ?=
PREFIX ?= /usr/local

# SUBDIRS = lib asn2qder test rfc arpa2 itu
SUBDIRS = lib tool test rfc

SUBMAKE=$(MAKE) PREFIX='$(PREFIX)' DESTDIR='$(DESTDIR)'

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

clean:
	@ $(foreach d,$(SUBDIRS),$(SUBMAKE) -C '$d' clean &&) echo "Cleaned all subdirectories"

