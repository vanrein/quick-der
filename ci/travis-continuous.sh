#!/bin/bash -ve
#
# Travis CI script for use on every-commit:
#  - build and install Arpa2CM (dependency)
#  - build and install Quick DER
#
test -n "$BUILDDIR"
test -n "$SRCDIR" 

test -d "$BUILDDIR" 
test -d "$SRCDIR" 
test -f "$SRCDIR/CMakeLists.txt"

pushd "$BUILDDIR" 

git clone https://github.com/arpa2/arpa2cm/ arpa2cm_build 

pushd arpa2cm_build
mkdir build
pushd build
cmake ..
make
sudo make install
popd
popd

popd

