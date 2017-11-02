#! /bin/sh
#
# Travis CI script for use on every-commit:
#  - build and install Arpa2CM (dependency)
#  - build and install Quick DER
#
test -n "$BUILDDIR" || exit 1
test -n "$SRCDIR" || exit 1

test -d "$BUILDDIR" || exit 1
test -d "$SRCDIR" || exit 1
test -f "$SRCDIR/CMakeLists.txt" || exit 1

cd "$BUILDDIR" || exit 1

### First, ARPA2CM
#
#
git clone https://github.com/arpa2/arpa2cm/ arpa2cm_build || exit 1
( cd arpa2cm_build && mkdir build && cd build && cmake .. && make && make install ) || exit 1

### Second, Quick DER
#
#
cmake .. && make -j

