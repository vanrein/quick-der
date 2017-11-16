#!/usr/bin/env python

from setuptools import setup, Extension, find_packages
from os import path

here = (path.dirname(path.realpath(__file__)))

extension = Extension(name="_quickder",
                      sources=[
                          path.join(here, "python/src/_quickder.c"),
                          path.join(here, "lib/der_header.c"),
                          path.join(here, "lib/der_unpack.c"),
                          path.join(here, "lib/der_pack.c")],
                      include_dirs=[path.join(here, "include")],
                      )

setup(
    scripts=['python/scripts/asn1literate', 'python/scripts/asn2quickder'],
    name='pyquickder',
    author='Rick van Rein',
    author_email='rick@openfortress.nl',
    license='BSD-2',
    description="Quick `n' Easy DER library",
    url="https://github.com/vanrein/quick-der",
    version='1.2.2',
    ext_modules=[extension],
    packages=find_packages(where='python'),
    package_dir={
        'quick_der': 'python/quick_der',
         'tests': 'python/tests'
    },
    install_requires=[
        'six',
        'asn1ate>=0.6.0',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests',
)
