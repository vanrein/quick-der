#!/usr/bin/env python

from setuptools import setup, find_packages, Library

sharedlib = Library (
	"_quickder",
	sources = [ "_quickder.c", "../lib/der_header.c", "../lib/der_unpack.c", "../lib/der_pack.c" ],
	# library_dirs = [ "/usr/local/lib" ],	#TODO# CMake
	# libraries =  [ "quickder" ]
)

setup (
	name = 'quick_der',
	version = "0.1",	#TODO# CMake
	packages = find_packages (),
	scripts = [ 'ASN1Object.py' ],
	ext_modules = [ sharedlib ],

	install_requires = [],

	package_data = {
		'': ['ASN1Object.py', '_quickder.c'],
	},

	# metadata for upload to PyPI
	author = "Me",	#TODO# CMake
	author_email = "me@example.com",	#TODO# CMake
	description = "Quick `n' Easy DER library",  #TODO# CMake
	license = "TODO",
	keywords = "DER ASN.1 Quick-DER",
	url = "https://github.com/vanrein/quick-der",

	# could also include long_description, download_url, classifiers, etc.
)

