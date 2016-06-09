#
# This directory holds .asn1 files derived from the pristine versions in orig/
# that were adapted (and commented with "--asn1ate" where this is done) to make
# it pass through the compiler.
#
# Current TODO:
#  - order definitions, the compiler now runs into problems
#  - check for undefined names, if possible
#  - map ... to DER_PACK_OPTIONAL, DER_PACK_LEAVE -- and process accordingly
#

CC ?= gcc

TARGETS = rfc3280.h rfc4120.h rfc4511.h rfc5280.h \
	rfc2898.h rfc2315.h rfc5208.h rfc7292.h \
	rfc2578.h
#DOWNWARD-SPIRAL-INTO-ITU# TARGETS += InformationFramework.h UsefulDefinitions.h

ASN2QUICKDER_CMD = $(shell which asn2quickder)
ASN2QUICKDER_RUN = $(ASN2QUICKDER_CMD)

all: $(TARGETS) test

test: $(TARGETS)
	rm -f quick-der
	ln -s . quick-der
	@ $(foreach h,$(TARGETS),echo > '$(h:.h=.c)' '#include "$(h)"' && [ -r $h ] && $(CC) -I ../include -I . -c '$(h:.h=.c)' && ) echo 'Passed all header compilation tests' || echo Skipped compilation of skipped header files

%.h: %.asn1
	@ [ -r $(ASN2QUICKDER_CMD) ] && $(ASN2QUICKDER_RUN) $< || echo Skipped ASN.1 header file generation for $<

clean:
	rm -f $(TARGETS) $(foreach h,$(TARGETS),$(h:.h=.c) $(h:.h=.o))

anew: clean all

install: all
	@ mkdir -p $(DESTDIR)$(PREFIX)/include/quick-der
	@ [ -r $(ASN2QUICKDER_CMD) ] && $(foreach h,$(TARGETS),install '$(h)' '$(DESTDIR)$(PREFIX)/include/quick-der' && ) echo Installed header files

uninstall:
	@ $(foreach h,$(TARGETS),rm -f '$(DESTDIR)$(PREFIX)/include/quick-der/$(h)' && ) echo Removed header files
	@ rmdir --ignore-fail-on-non-empty '$(DESTDIR)$(PREFIX)/include/quick-der'

