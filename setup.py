#!/usr/bin/env python

from setuptools import setup, Extension, find_packages
from os import path, mkdir
from subprocess import check_call
from tempfile import mkdtemp
from atexit import register as atexit_register

here = (path.dirname(path.realpath(__file__)))

extension = Extension(name='_quickder',
                      sources=[
                          path.join(here, 'python', 'src', '_quickder.c'),
                          path.join(here, 'lib', 'der_header.c'),
                          path.join(here, 'lib', 'der_unpack.c'),
                          path.join(here, 'lib', 'der_pack.c')],
                      include_dirs=[path.join(here, 'include')],
                      )

# Before we enter setup() we need to build the Python libraries
# from their ASN.1 sources using the asn2quickder script.

a2qd = mkdtemp ()
dest_parent = path.join(a2qd, 'python')
dest_pkgdir = path.join(a2qd, 'python', 'quick_der')
orig_pkgdir = path.join(here, 'python', 'quick_der')
a2qd_pkgdir = path.join(a2qd, 'python', 'testing')

atexit_register (check_call, ['cmake', 'remove_directory', a2qd])

mkdir (dest_parent)
mkdir (dest_pkgdir)

check_call (['cmake', here], cwd=a2qd)
check_call (['cmake', '--build', a2qd])
#RECURSIVE# check_call (['ctest', '-VV'], cwd=a2qd)
check_call (['cmake', '-E', 'copy_directory', a2qd_pkgdir, dest_pkgdir], cwd=a2qd)
check_call (['cmake', '-E', 'copy_directory', orig_pkgdir, dest_pkgdir], cwd=a2qd)

#DEBUG# check_call (['ls', dest_pkgdir])

setup(
    scripts=['python/scripts/asn1literate', 'python/scripts/asn2quickder'],
    name='quick-der',
    author='Rick van Rein',
    author_email='rick@openfortress.nl',
    license='BSD-2',
    description="Quick `n' Easy DER library",
    long_description=open (path.join (here, 'README.MD')).read(),
    long_description_content_type='text/markdown',
    url="https://github.com/vanrein/quick-der",
    version='1.2.2',
    ext_modules=[extension],
    packages=find_packages(where=dest_parent),
    package_dir={
        'quick_der': dest_pkgdir,
         #DO_NOT_INSTALL# 'tests': path.join ('python', 'tests'),
    },
    install_requires=[
        'six',
        'asn1ate>=0.6.0',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests',
)

