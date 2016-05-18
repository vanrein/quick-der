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

HEADERS = RemotePKCS11.h KXOVER.h
LITERATE = RemotePKCS11.md RemotePKCS11.rst RemotePKCS11.html RemotePKCS11.epub \
		RemotePKCS11.tex RemotePKCS11.pdf \
		KXOVER.md KXOVER.rst KXOVER.html KXOVER.epub KXOVER.tex KXOVER.pdf \
		KXOVER.txt \
		CommunicationFilter.md
TARGETS = $(HEADERS) $(LITERATE)

ASN2QUICKDER_DIR = ../tool/asn1ate

ASN2QUICKDER = PYTHONPATH='$(ASN2QUICKDER_DIR)' $(ASN2QUICKDER_DIR)/asn1ate/asn2quickder.py

ASNLITERATE = ../tool/asn1literate.py 

KXOVER_DEPS = ../rfc/rfc4120.asn1 ../rfc/rfc5280.asn1

all: $(TARGETS) test

test: $(HEADERS)
	@ $(foreach h,$(HEADERS),echo > '$(h:.h=.c)' '#include "$(h)"' && gcc -c '$(h:.h=.c)' && ) echo 'Passed all header compilation tests'

%.h: %.asn1
	$(ASN2QUICKDER) '$<' $(foreach f,$($(<:.asn1=_DEPS)),$f)

%.md: %.asn1
	@ if grep -q '	' '$<' ; then echo 'Please remove tabs from $<, they mess up the layout' ; exit 1 ; fi
	$(ASNLITERATE) '$<'

%.txt: %.md
	@ [ -x /usr/bin/pandoc ] && pandoc --self-contained -o '$@' '$<' || echo Pandoc is not installed -- skipping TeX and PDF generation

%.rst: %.md
	@ [ -x /usr/bin/pandoc ] && pandoc --self-contained -o '$@' '$<' || echo Pandoc is not installed -- skipping RST generation

%.html: %.md
	@ [ -x /usr/bin/pandoc ] && pandoc --self-contained -o '$@' '$<' || echo Pandoc is not installed -- skipping HTML generation

%.epub: %.md
	@ [ -x /usr/bin/pandoc ] && pandoc --self-contained -o '$@' '$<' || echo Pandoc is not installed -- skipping EPUB generation

%.tex: %.md
	@ [ -x /usr/bin/pandoc ] && pandoc --self-contained -o '$@' '$<' || echo Pandoc is not installed -- skipping TeX and PDF generation

%.pdf: %.tex
	@ [ -x /usr/bin/pdflatex -a -r '$<' ] && pdflatex '$<' || echo pdfLaTeX is not installed -- skipping PDF generation

clean:
	rm -f $(TARGETS) $(foreach h,$(TARGETS),$(h:.h=.c) $(h:.h=.o))

anew: clean all

install: all
	@ mkdir -p $(DESTDIR)$(PREFIX)/include/quick-der
	@ $(foreach h,$(TARGETS),install '$(h)' '$(DESTDIR)$(PREFIX)/include/quick-der' && ) echo Installed header files

uninstall:
	@ $(foreach h,$(TARGETS),rm -f '$(DESTDIR)$(PREFIX)/include/quick-der/$(h)' && ) echo Removed header files
	@ rmdir --ignore-fail-on-non-empty '$(DESTDIR)$(PREFIX)/include/quick-der'

