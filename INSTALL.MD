# Installing Quick DER

<img alt="Quick DER logo" src="quick-der-logo.png" style="float: right;"/>

> To do a basic installation that provides you with a default build of the
> library, (but not the Python bindings), C headers and tools:
>
>     make           # Optional: make PREFIX=/my/path
>     make install

Quick DER uses CMake as a (meta-)buildsystem. There is a top-level
Makefile that provides convenience targets for default builds;
the `all` target will build the default configuration.
You can also use CMake on its own, or one of its configuration UIs,
for more detailed configuration of the Quick DER build.

Using just `make` creates a `build/` directory (for an out-of-source
build), runs CMake there, and then performs a regular build.

Other customary build targets include `test`, `clean` and `uninstall`,
and `package` which uses CPack (part of CMake) to build local packages.

The default configuration builds the library, Python bindings for the
library, and headers for a selection of standards that use DER-encoding
for data (e.g. the LDAP RFCs).

## Dependencies

These are tools needed to be able to build and install Quick DER.

  * [CMake](https://cmake.org/)
    Meta-buildsystem for doing dependency and configuration.
  * [Python](https://www.python.org/)
    Interpreter for the Python language, which is used in some of the
    build tools. Both (or either of) Python 2 and Python 3 are supported.
    Note that you also need the Python development headers, in order to
    build Python extensions.
  * [pyparsing](https://pypi.python.org/pypi/pyparsing)
    The tool `asn2quickder` is used to translate the ASN.1 descriptions
    of RFC data structures to C headers (and Python bindings).
    Note that `asn2quickder` is "good enough" for the mapping of at least
    an important part of the RFCs, but it is work that can still be improved.
  * Python packages `setuptools`, `asn1ate` and `six`.

Suggested packages are:

  * **Debian** cmake python-pyparsing python-dev python-setuptools, and then
    *easy_install* six asn1ate
  * **FreeBSD** cmake python-pyparsing and then *easy_install* asn1ate.

## Configuration

The following compile-time options are supported. These can be set from
the CMake command-line or by using the `ccmake` command. All of the options
default to *on*.

 - `DEBUG` When enabled, prints progress and status information about
   walks and DER operations to stdout. This is not recommended for
   production use.
 - `SPEC_RFC`, `SPEC_ITU`, `SPEC_ARPA2` each of these options controls
   the generation of C header files and Python bindings for a set of
   ASN.1 specifications.

You should set PYTHONPATH to suitable values for the eventual installation
path of Quick DER, so that the Python extensions can be correctly installed.

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

If any downstream package intends to use the CMake macro's from
MacroASN1Module, you will need to deal with packaging the Python
tools for it; see [setup.py](setup.py) and the
[Python install documentation](python/INSTALL.MD).
