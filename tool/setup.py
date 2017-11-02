#!/usr/bin/env python
#
# Setup for the bundled asn2qd1ate, which is needed by the other scripts
# in this directory.
from setuptools import setup, Extension

if __name__ == '__main__':
	setup (
		name='asn2qd1ate',
		version='0.5.1',
		scripts=['asn1literate.py', 'asn2quickder.py'],
		install_requires=[
			"git+git://github.com/kimgr/asn1ate.git@baf6a89b2f08892f184cf36c4c7a250251b195b1",

		],
		packages = ['asn2qd1ate']
	)

