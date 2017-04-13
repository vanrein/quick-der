# Installing Quick DER

<img alt="Quick DER logo" src="quick-der-logo.png" style="float: right;"/>

The basic installation that provides you with the library:

    make           # Optional: make PREFIX=/my/path
    make install

Other customary build targets include `test`, `clean` and `uninstall`.
The makefile itself is just a stub, that invokes CMake as a (meta-)
build system for generating the actual build files. You can also use
CMake on its own, or one of its configuration UIs, for more detailed
configuration of the system.

Using just `make` creates a `build/` directory (for an out-of-source
build), runs CMake there, and then performs a regular build.

The default configuration builds the library, Python bindings for the
library, and headers for a selection of standards that use DER-encoding
for data (e.g. the LDAP RFCs).

## Dependencies

These are tools needed to be able to build and install Quick DER.

  * [CMake](https://cmake.org/)
    Meta-buildsystem for doing dependency and configuration.
  * [Python](https://www.python.org/)
    Interpreter for the Python language, which is used in some of the
    build tools.
  * [pyparsing](https://pypi.python.org/pypi/pyparsing)
    The tool `asn2quickder` is used to translate the ASN.1 descriptions
    of RFC data structures to C headers (and Python bindings).
    Note that `asn2quickder` is "good enough" for the mapping of at least
    an important part of the RFCs, but it is work that can still be improved.

## Add-ons

While Quick DER provides tools for manipulating DER-encoded data --
packing and unpacking and parsing -- it can be useful to have some
other DER-related tools installed, for debugging purposes.

  * A utility `derdump` that dumps even *wrongly formatted* DER-encoded
    data.  This is extremely useful to ASN.1 developers.
    You can find the tool in the [hexio](https://github.com/vanrein/hexio)
    which is suggested as a co-install for Quick DER.

## Packaging

Quick DER uses CMake as (meta)buildsystem and you can create installable
packages with CPack. An installed Quick DER package includes both
CMake and pkg-config configuration files so that Quick DER can easily
be discovered by the buildsystem of Quick DER users.

The configuration file templates can be found in `contrib/`
