#!/usr/bin/env python

from setuptools import setup, Extension, find_packages
from sys import executable
from os import path, environ
from re import compile as re_compile
from subprocess import check_call
from tempfile import mkdtemp

here = (path.dirname(path.realpath(__file__)))

# Before we enter setup() we need to build the Python libraries
# from their ASN.1 sources using the asn2quickder script.
# We work around CMake, but then need regexp matching on scripts.
# CMake however, is quite troublesome in multilinux targets.

# In terms of Python setuptools, this is not perfect either.  We
# should have made an Extension next to the one for the C library.
# But then again, we should have found documentation on how this
# is done.  If we missed it, please send us a reference!

#UNUSED# environ ['PYTHONPATH'] = '%s:%s' % (here, environ.get ('PYTHONPATH', ''))
#UNUSED# add1_open_re = re_compile ('[ \t\n]add_asn1_modules[ \t\n]*\(')
#UNUSED# asn2cmd = [ executable, path.join (here, 'scripts', 'asn2quickder'), '-l', 'python' ]

setup(
    scripts=[path.join (here, 'scripts', 'asn1literate'), path.join (here, 'scripts', 'asn2quickder')],
    name='asn2quickder',
    author='Rick van Rein',
    author_email='rick@openfortress.nl',
    license='BSD-2',
    description='ASN.1 Compiler for Quick (and Easy) DER',
    long_description=open (path.join (here, '..', 'ASN2QUICKDER.MD')).read(),
    long_description_content_type='text/markdown',
    url='https://gitlab.com/arpa2/asn2quickder',
    version='1.2.2',
    packages=['asn2quickder', 'asn2quickder.generators'],
    package_dir={
	'asn2quickder'           : path.join (here, 'asn2quickder'              ),
	'asn2quickder.generators': path.join (here, 'asn2quickder', 'generators'),
    },
    install_requires=[
        'six',
        'asn1ate>=0.6.0',
    ],
)

