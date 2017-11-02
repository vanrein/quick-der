#!/usr/bin/env python

from setuptools import setup, Extension, find_packages
from os import path

here = (path.dirname(path.realpath(__file__)))


extension = Extension(name="_quickder",
                      sources=[
                          path.join(here, "src/_quickder.c"),
                          path.join(here, "../lib/der_header.c"),
                          path.join(here, "../lib/der_unpack.c"),
                          path.join(here, "../lib/der_pack.c")],
                      include_dirs=[path.join(here, "../include")],
)

setup(
    scripts=['scripts/asn1literate', 'scripts/asn2quickder'],
    name='quick_der',
    author='Rick van Rein',
    author_email='rick@openfortress.nl',
    license='BSD-2',
    description="Quick `n' Easy DER library",
    url="https://github.com/vanrein/quick-der",
    version='1.2.2',
    ext_modules=[extension],
    packages=find_packages(),
    install_requires=[
        'asn1ate>0.5'
    ],
    dependency_links=[
        'git+ssh://git@github.com/kimgr/asn1ate.git@baf6a89b2f08892f184cf36c4c7a250251b195b1#egg=asn1ate-0.5.1.dev0',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
    test_suite='tests',
)
