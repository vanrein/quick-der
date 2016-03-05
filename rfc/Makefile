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

PREFIX = /usr/local

TARGETS = rfc3280.h rfc4120.h rfc4511.h rfc5280.h

ASN2QUICKDER_DIR = ../tool/asn1ate

ASN2QUICKDER = PYTHONPATH='$(ASN2QUICKDER_DIR)' $(ASN2QUICKDER_DIR)/asn1ate/asn2quickder.py

all: $(TARGETS) test

test: $(TARGETS)
	@ $(foreach h,$(TARGETS),echo > '$(h:.h=.c)' '#include "$(h)"' && gcc -c '$(h:.h=.c)' && ) echo 'Passed all header compilation tests'

%.h: %.asn1
	$(ASN2QUICKDER) $<

clean:
	rm -f $(TARGETS) $(foreach h,$(TARGETS),$(h:.h=.c) $(h:.h=.o))

anew: clean all

install: all
	@ mkdir -p $(PREFIX)/include/quick-der
	@ [ -r $(ASN2QUICKDER) ] && $(foreach h,$(TARGETS),install '$(h)' '$(PREFIX)/include/quick-der' && ) echo Installed header files

uninstall:
	@ $(foreach h,$(TARGETS),rm -f '$(PREFIX)/include/quick-der/$(h)' && ) echo Removed header files
	@ rmdir --ignore-fail-on-non-empty '$(PREFIX)/include/quick-der'

