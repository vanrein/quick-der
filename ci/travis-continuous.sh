#!/bin/bash 
#
# Travis CI script for use on every-commit:
#  - build and install Arpa2CM (dependency)
#  - build and install Quick DER
#
set -e
set -v

test -n "$BUILDDIR"
test -n "$SRCDIR" 

test -d "$BUILDDIR" 
test -d "$SRCDIR" 
test -f "$SRCDIR/CMakeLists.txt"

cd "$BUILDDIR" 

git clone https://github.com/arpa2/arpa2cm/ arpa2cm_build 

cd arpa2cm_build
mkdir build
cd build
cmake ..
make
sudo make install

cd ${BUILDDIR}
