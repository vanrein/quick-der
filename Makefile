DESTDIR ?=
PREFIX ?= /usr/local

VERSION = 0.1-RC5

# SUBDIRS = lib asn2qder test rfc arpa2 itu
SUBDIRS = lib tool test rfc

SUBMAKE=$(MAKE) PREFIX='$(PREFIX)' DESTDIR='$(DESTDIR)' VERSION='$(VERSION)'

all:
	#
	# You will need the Python package asn1ate from
	#
	# https://github.com/vanrein/asn2quickder
	#
	# This provides the ASN.1 language core for the asn2quickder compiler;
	# we use it to produce header files from RFC's.
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

