#!/usr/bin/env python
#
# asn1literate.py -- Literate programming for ASN.1
#
# This takes in an ASN.1 module and treats its comment lines as MarkDown syntax.
# The non-comment lines are inserted as literal text.  Note that ASN.1 is usually
# a series of global definitions in arbitrary order, so it lends itself easily
# to this approach.
#
# There are a few special annotations, which are defined herein, that start with
# "--WORD: " and that lead to a standardised remark with the code shown but
# commented-out.
#
# From: Rick van Rein <rick@openfortress.nl>


import sys
import string


#
# Commandline processing
#
if len (sys.argv) not in [2,3]:
	sys.stderr.write ('Usage: %s literalfile.asn [literalfile.md]\n' % sys.argv [0])
	sys.exit (1)
infile = sys.argv [1]
if len (sys.argv) > 2:
	otfile = sys.argv [2]
else:
	if infile [-5:] == '.asn1':
		otfile = infile [:-5] + '.md'
	else:
		otfile = infile = '.md'

#
# Read input data line by line
#
inf = open (infile, 'r')
otf = open (otfile, 'w')
mode = 'md'
for ln in inf.readlines ():
	if ln == '\n' or ln == '--\n':
			otf.write ('\n')
	elif ln [:3] == '-- ':
		# Looks like MarkDown, so reproduce after comment lines
		if mode != 'md':
			mode = 'md'
			otf.write ('\n')
		otf.write (ln [3:])
	else:
		# Looks like ASN.1, so reproduce literally with 4-space indent
		if mode != 'asn1':
			mode = 'asn1'
			otf.write ('\n')
		otf.write ('    ' + ln)
inf.close ()

