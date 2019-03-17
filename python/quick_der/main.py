#!/usr/bin/env python
#
# asn2quickder -- Generate header files for C for use with Quick `n' Easy DER
#
# This program owes a lot to asn1ate, which was built to generate pyasn1
# classes, but which was so well-written that it could be extended with a
# code generator for Quick DER.
#
# Much of the code below is diagonally inspired on the pyasn1 backend, so
# a very big thank you to Schneider Electric Buildings AB for helping to
# make this program possible!
#
# Copyright (c) 2016-2017 OpenFortress B.V. and InternetWide.org
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of Schneider Electric Buildings AB nor the
#       names of contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#


import getopt
import os.path
import re
import sys

from asn1ate.sema import build_semantic_model, parser

from quick_der.generators.header import QuickDER2c
from quick_der.generators.python import QuickDER2py
from quick_der.generators.source import QuickDER2source
from quick_der.generators.testdata import QuickDER2testdata
from quick_der.util import dprint


def parse_opts(script_name, script_args):
	# Test case notation: [asn1id=] [[ddd]-]ddd ...
	casesyntax = re.compile('^(?:([A-Z][A-Za-z0-9-]*)=)?((?:([0-9]*-)?[0-9]+)(?:,(?:[0-9]*-)?[0-9]+)*)$')
	cases2find = re.compile('(?:([0-9]*)(-))?([0-9]+)')

	incdirs = []
	langopt = ['c', 'python']
	langsel = set()
	testcases = {}
	(opts, restargs) = getopt.getopt(script_args, 'vI:l:t:', longopts=langopt)
	for (opt, optarg) in opts:
		if opt == '-I':
			incdirs.append(optarg)
		elif opt == '-v':
			dprint.enable = True
		elif opt == '-l':
			if optarg not in langopt:
				sys.stderr.write(
					'No code generator backend for ' + optarg + '\nAvailable backends: ' + ', '.join(langopt) + '\n')
				sys.exit(1)
			langsel.add(optarg)
		elif opt == '-t':
			m = casesyntax.match(optarg)
			if m is None:
				sys.stderr.write('Wrong syntax for -t [asn1id=][[ddd]-]ddd,...\n')
				sys.exit(1)
			asn1id = m.group(1) or ''
			series = m.group(2)
			for (start, dash, end) in cases2find.findall(series):
				end = int(end)
				if len(start) > 0:
					start = int(start)
				elif len(dash) == 0:
					start = end
				else:
					start = 0
				if not asn1id in testcases:
					testcases[asn1id] = []
				testcases[asn1id].append((start, end))
		elif optarg[:2] == '--' and optarg[2:] in langopt:
			langsel.add(optarg)
		else:
			sys.stderr.write(
				'Usage: {} [-I incdir] [-l proglang] [-t testcases] ...'
				' main.asn1 [dependency.asn1] ...\n'.format(script_name))
			sys.exit(1)

	if len(langsel) == 0:
		langsel = set(langopt)

	return langsel, langopt, restargs, incdirs, testcases


def realise(incdirs, restargs):
	defmods = {}
	refmods = {}

	incdirs.append(os.path.curdir)
	for file_ in restargs:
		modnm = os.path.basename(file_).lower()
		dprint('Parsing ASN.1 syntaxdef for "%s"', modnm)
		with open(file_, 'r') as asn1fh:
			asn1txt = asn1fh.read()
			asn1tree = parser.parse_asn1(asn1txt)
		dprint('Building semantic model for "%s"', modnm)
		asn1sem = build_semantic_model(asn1tree)
		defmods[os.path.basename(file_)] = asn1sem[0]
		refmods[os.path.splitext(modnm)[0]] = asn1sem[0]
		dprint('Realised semantic model for "%s"', modnm)

	imports = list(refmods.keys())
	while len(imports) > 0:
		dm = refmods[imports.pop(0).lower()]

		if not dm.imports:
			continue

		for rm in dm.imports.imports.keys():
			rm = str(rm).lower()
			if rm not in refmods:
				dprint('Importing ASN.1 include for "%s"', rm)
				modfh = None
				for incdir in incdirs:
					try:
						modfh = open(incdir + os.path.sep + rm + '.asn1', 'r')
						break
					except IOError:
						continue
				if modfh is None:
					raise Exception('No include file "{}.asn1" found'.format(rm))
				asn1txt = modfh.read()
				asn1tree = parser.parse_asn1(asn1txt)
				dprint('Building semantic model for "%s"', rm)
				asn1sem = build_semantic_model(asn1tree)
				refmods[rm] = asn1sem[0]
				imports.append(rm)
				dprint('Realised semantic model for "%s"', rm)
	return defmods, refmods


def generate(langsel, defmods, refmods, testcases):

	# Generate C header files
	if 'c' in langsel:
		for modnm in defmods.keys():
			dprint('Generating C header file for "%s"', modnm)
			cogen = QuickDER2c(defmods[modnm], modnm, refmods)
			cogen.generate_head()
			cogen.generate_overlay()
			cogen.generate_pack()
			cogen.generate_psub()
			cogen.generate_tail()
			cogen.close()
			dprint('Ready with C header file for "%s"', modnm)

	# Generate Python modules
	if 'python' in langsel:
		for modnm in defmods.keys():
			dprint('Generating Python module for "%s"', modnm)
			cogen = QuickDER2py(defmods[modnm], modnm, refmods)
			cogen.generate_head()
			cogen.generate_classes()
			cogen.generate_values()
			cogen.generate_tail()
			cogen.close()
			dprint('Ready with Python module for "%s"', modnm)

	if 'source' in langsel:
		for modnm in defmods.keys():
			dprint('Generating C pack/unpack source for "%s"', modnm)
			cogen = QuickDER2source(defmods[modnm], modnm, refmods)
			cogen.generate_head()
			cogen.generate_pack()
			cogen.generate_unpack()
			cogen.generate_tail()
			cogen.close()
			dprint('Ready with C pack/unpack source for "%s"', modnm)

	# Generate test data
	if testcases != {}:
		for modnm in defmods.keys():
			print ('Generating test cases for ' + modnm)
			cogen = QuickDER2testdata(defmods[modnm], modnm, refmods)
			cogen.generate_testdata()
			for typenm in cogen.all_typenames():
				if typenm in testcases:
					cases = testcases[typenm]
				elif '' in testcases:
					cases = testcases['']
				else:
					cases = []
				casestr = ','.join([str(s) + '-' + str(e) for (s, e) in cases])
				for (casenr, der_packer) in cogen.fetch_multi(typenm, cases):
					if der_packer is None:
						break
					print ('Type %s case %s packer %s' % (typenm, casenr, der_packer.encode('hex')))
			cogen.close()
			print('Generated  test cases for ' + modnm)


def main(script_name, script_args):
	"""The main program asn2quickder is called with one or more .asn1 files,
	   the first of which is mapped to a C header file and the rest is
	   loaded to fulfil dependencies.
	"""
	langsel, langopt, restargs, incdirs, testcases = parse_opts(script_name, script_args)
	defmods, refmods = realise(incdirs, restargs)
	generate(langsel, defmods, refmods, testcases)
