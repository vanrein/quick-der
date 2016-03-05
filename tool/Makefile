PREFIX=/usr/local

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
	[ -r hexio/derdump.py ] && install -m 0755 hexio/derdump.py "$(PREFIX)/bin/derdump"

uninstall:
	rm -f "$(PREFIX)/bin/derdump"

