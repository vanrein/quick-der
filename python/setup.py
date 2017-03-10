#!/usr/bin/env python

from distutils.core import setup, Extension

sharedlib = Extension (
	"_quickder",
	[ "_quickder.c" ],
	library_dirs=[ '/usr/local/lib' ],	#TODO#
	libraries = [ "quickder" ],
	# extra_objects = [
	# 	"unix/x86_64/_quickder.so"
	# ]
)

if __name__ == '__main__':
	setup (
		name='quickder',
		verion='${PACKAGE_VERSION}',
		#TODO# package_dir={ '': '${CMAKE_CURRENT_SOURCE_DIR}' },
		package_dir={ '': '.' },
		ext_modules=[ sharedlib ],
		packages=['.']
	)

