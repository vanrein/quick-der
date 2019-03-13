#!/usr/bin/env python

from setuptools import setup, Extension, find_packages
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

environ ['PYTHONPATH'] = '%s:%s' % (path.join (here, 'python'), environ.get ('PYTHONPATH', ''))
add1_open_re = re_compile ('[ \t\n]add_asn1_modules[ \t\n]*\(')
asn2cmd = [ path.join (here, 'python', 'scripts', 'asn2quickder'), '-l', 'python' ]
for asn1dir in ['rfc', 'itu', 'arpa2']:
	asn2cmd.append ('-I')
	asn2cmd.append (path.join (here, asn1dir))
	cmf = open (path.join (asn1dir, 'CMakeLists.txt')).read ()
	comment_re = re_compile ('#[^\n]*\n')
	cmf2 = '\n'.join (comment_re.split (cmf))
	for mtch in add1_open_re.split (cmf2) [1:]:
		closed = mtch.find (')')
		if closed == -1:
			continue
		for asn1spec in mtch [:closed].split () [1:]:
			asn1path = path.join (here, asn1dir, asn1spec + '.asn1')
			print ('Generating import module \"quick_der.%s\" from %s%s%s.asn1' % (asn1spec,asn1dir,path.sep,asn1spec))
			check_call (asn2cmd + [ asn1path ], cwd=path.join (here, 'python', 'quick_der'))

# We proceed with the more proper parts of the setup.
# That is, the parts for which we could find documentation.

extension = Extension(name='_quickder',
                      sources=[
                          path.join(here, 'python', 'src', '_quickder.c'),
                          path.join(here, 'lib', 'der_header.c'),
                          path.join(here, 'lib', 'der_unpack.c'),
                          path.join(here, 'lib', 'der_pack.c')],
                      include_dirs=[path.join(here, 'include')],
                      )

setup(
    scripts=['python/scripts/asn1literate', 'python/scripts/asn2quickder'],
    name='quick_der',
    author='Rick van Rein',
    author_email='rick@openfortress.nl',
    license='BSD-2',
    description='Quick (and Easy) DER, a Library for parsing ASN.1',
    long_description=open (path.join (here, 'PYTHON.MD')).read(),
    long_description_content_type='text/markdown',
    url='https://github.com/vanrein/quick-der',
    version='1.2.2',
    ext_modules=[extension],
    packages=find_packages(where='python'),
    package_dir={
        'quick_der': path.join (here, 'python', 'quick_der'),
    },
    install_requires=[
        'six',
        'asn1ate>=0.6.0',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests',
)

