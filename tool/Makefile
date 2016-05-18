all:

clean:

install:
	#
	# Installing a good DER dumping utility for developers:
	#
	# https://github.com/vanrein/hexio
	#
	# This tool will complain about DER errors -- but continue.
	#
	[ -r hexio/derdump.py ] && install -m 0755 hexio/derdump.py "$(DESTDIR)$(PREFIX)/bin/derdump"

uninstall:
	rm -f "$(DESTDIR)$(PREFIX)/bin/derdump"

