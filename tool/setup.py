#!/usr/bin/env python
#
# Setup for the bundled asn2qd1ate, which is needed by the other scripts
# in this directory.
from setuptools import setup, Extension

if __name__ == '__main__':
	setup (
		name='asn2qd1ate',
		version='0.5.1',
		package_dir={ '': '.' },
		packages = ['asn2qd1ate']
	)

