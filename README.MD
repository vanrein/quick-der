# Quick (and Easy) DER, a Library for parsing ASN.1

<img alt="Quick DER logo" src="quick-der-logo.png" style="float: right;"/>

> *Quick DER, or if you like, "Quick and Easy DER", is a library for handling
> DER, which is a widely used binary representation of ASN.1 syntax in binary
> formats.  The library describes ASN.1 syntax in a parser table that can be
> fed into library routines, resulting in pointer/length descriptors for the
> individual data fragments.*

See also:

 - [Building and installing Quick DER](INSTALL.MD)
 - [Extended usage examples](USING.MD)
 - [Embedded systems use](WHEN-SIZE-MATTERS.MD)
 - [Python bindings](PYTHON.MD)
 - Syntax definitions for [walks](WALK-SYNTAX.MD)
   and [packing](PACK-SYNTAX.MD)
 - [Changelog](CHANGELOG.MD) (high-level history since 1.1)
 - [License](LICENSE.MD) (BSD 2-Clause)

## Basic Usage

Quick DER is a three-pronged fork:
 - you can use the library to process DER data at a low level (e.g. as a
   sequence of nested tags with a data payload),
 - you can use the data structures provided by the library for a wide variety
   of RFCs to process data from those RFCs at a higher level (e.g. LDAP
   messages with named fields),
 - the tools provided with the library can be used to translate ASN.1 syntax
   into (C language) data structures and Python bindings for use as above.

Since Quick DER handles binary data (rather than character strings), all data
is described in so-called `dercursor` structures; each containing a pointer
and a size of the data pointed at.

### Low Level Interface

The routine `der_header()` can be used to examine the component at the
start of the DER data. This provides information on the tag and payload
length of the component.

There are routines `der_iterate_first()` and `der_iterate_next()` routines
to manually iterate over a DER structure's components.  This can be used to
analyse structures that have not been unpacked (yet).  The `der_countelements()`
routine can be used to predict the number of iterations.

There are also routines to manually walk through packaged DER structures,
namely `der_enter()` and `der_skip()` to enter into a nested structure and to
find the next element in a concatenation of such elements.

A more advanced form of such walks through a DER structure exists in the
form of `der_walk()`, which is fed a sequence of enter/skip statements with
tags that will be validated.

### Higher Level Interface

The preferred approach of using this library is translating the ASN.1 syntax into
a parser table.  This is done when building your software, as a phase preceding
the compilation of your Quick DER using program.  The translation from ASN.1
to C code can be done manually or integrated into the buildsystem for your
project (see below).

The resulting *path walks* are used in calls like `der_unpack()` to transform
DER into C-style structures, and `der_pack()` to make the opposite transformation.
The C-style structures are derived from the ASN.1 syntax, and permits access to
the information with no further need of understanding the depths of processing
DER.

The output from mapping ASN.1 to a parser table is an include file for the
C programming language.  This defines the various *path walks* that can be
used to unpack and pack DER data.  The output and input of these routines
takes the form of an array of `dercursor` values.

To simplify use of the unpacked data, there are overlay structures for the
`dercursor` array.  These overlay structures use the same labels that are
used in the ASN.1 syntax, so it is possible to walk around in the structures.

Some parts of the syntax indicate `OPTIONAL` elements.  Such elements result
in the respective `dercursor` variables to be NULL values; specifically, the
function `der_isnull()` returns a true value for these elements.

The storage structure for the `SEQUENCE OF` and `SET OF` elements is not
the usual `dercursor` field with `uint8_t *derptr` and `size_t derlen`
attributes, but another field type `dernode` which can take a number of forms,
namely a `dercursor` with `uint8_t *wire.derptr` and `size_t wire.derlen`
or a `derarray` with an array of similar entries under `info.derray` and
an array length under `info.dercnt`. It is the caller's responsibility to
keep track of which parsing-phase is active, and so which kind of data
is stored in the `dernode`.

### ASN.1 Compiler

We have provided a simple `asn2quickder` compiler based on
[asn1ate](https://github.com/kimgr/asn1ate)
to generate both the overlay data structures and the
byte codes for `der_pack()` and `der_unpack()`.  For most everyday ASN.1
this should suffice to produce a header file from an ASN.1 module.

The compiler generates annotations for external callers that wish to unpack
`SEQUENCE OF` and `SET OF` syntax elements.  These annotations can be used
for invoking the sub-unpacking and sub-packing procedures in a reasonably
general manner.  We think this is the best trade-off between simplicity
on the side of Quick DER, and ability on the side of a potentially more
demanding ASN.1 application.

The tool can generate C language headers and Python bindings for an
ASN.1 description. An additional tool, `asn1literate` produces documentation
from an ASN.1 description.

For users of CMake, the macros in `cmake/MacroASN1Module.cmake` may be
an inspiration to automate ASN.1 compilation in those projects. The macros
should not be used verbatim, since they are tied up with compiling ASN.1
before the tools are installed.


## Features

Quick DER accepts a liberal superset of DER, while making no memory
allocations (although it can use extra memory for handling variable-
length structures if you help it). It provides a library of pre-
compiled headers and bindings to common protocols that use DER.

### No Memory Allocation

The entire library has been designed to operate without dynamic memory allocation.
This means that there will never be a memory leak as a result of using Quick DER.

When DER information is unpacked, it is assumed to be loaded into a memory buffer
by the calling program, and the `dercursor` structures point to portions of that
buffer.  The data is stored in `dercursor` arrays which the user program may
overlay with meaningful, ASN.1-labelled structures.  In many applications, such
structures can be allocated on the stack.

Some portions of the data may be dynamically sized, notably the `SEQUENCE OF`
and `SET OF` structures, which indicate that the structural description following
it may be repeated in the binary data.  Such data portions will be stored and
not yet unpacked by `der_unpack()`.  Based on the stored DER data in a `dercursor`,
the calling application can choose to use iterators, `der_walk()` and so on to
avoid actually unpacking it; or it may allocate memory dynamically, and use that
to repeatedly call `der_unpack()` to find the individual entries.

In short, the Quick DER library *never* needs to perform memory allocation, and
it provides the calling program with a lot of control to avoid it too.  This is
ideal for embedded applications, but is also beneficial for a secure programming
style.

### Optional Memory Allocation for Sequences

Software built around Quick DER, such as
[LillyDAP](https://github.com/vanrein/lillydap)
for example, may well have its own regime of memory management.
If this is the case, it is quite possible to unpack `SEQUENCE OF` and
`SET OF` elements.  The `dernode` type can be overlaid on a regular
`dercursor`, and the caller can subsequently allocate memory sufficient
for handling the array of dercursors.

The structure inserting the extra symbols `wire` for wire format and
`info` for the array is union named `dernode`; `der_unpack()` will fill it
with the `wire` form, but it is assumed that the caller's post-parser will
invoke `der_unpack()` again on the components, and deliver the result in
`info`, thereby overwriting the original `wire` format.  Before sending out an
`info` structure with `der_pack()`, the calling application should revert to
`wire` form again through preparing calls to `der_pack()`.

### Embedding

The library can be built for static linking, and can be optimized for
code size when linking. See the [embedded Quick DER](WHEN-SIZE-MATTERS.MD)
file for details.

### RFC Collection

We have started a collection of RFC's, stripped down to ASN.1 modules,
that can be mapped to header files that can simply be include in a C program:

    #include <quick-der/rfc5280.h>
    #include <quick-der/rfc4120.h>
    #include <quick-der/rfc4511.h>

These examples are included with Quick DER:

  * X.509 certificate and CRL structures,
  * Kerberos packet formats and messaging,
  * LDAP as a protocol description,
  * .. a dozen other RFC protocol descriptions.

Most ASN.1 descriptions do things that confuse the compiler, so small changes
have been made, and clearly marked with `asn1ate` and an explanation in the
ASN.1 files in the `rfc/`, `itu/` and `arpa2/` directories.  The issues found
were usually quite simple:

  * Using uppercase initial characters in type names
  * Removing complex constraints (Quick DER does not implement them anyway)
  * Cutting an infinitely circular reference for `Filter.not` in LDAP.

There are some specifications that go far beyond the abilities of `asn1ate`,
by using such concepts as macros.  This applies to the SNMP RFC's (which are
not included).

### Python Bindings ###

There are Python (both Python 2 and Python 3) bindings that can be generated
when building the library.

See [Python and Quick DER](PYTHON.MD) for a plan that greatly simplifies
ASN.1 processing with Python.

### Relation to BER

*This is for ASN.1 experts; others can safely skip this subsection.*

The Quick DER library is designed to process DER, although it will also accept
some of the more general BER format.  If a length or value is written in more
than the minimal space, the library is still likely to accept it.  Note that
the `BIT STRING` type is somewhat likely to run into overflow problems, so
there the full restrictiveness of DER is applied.

Integer types longer than four octets (i.e. 32 bit) are not supported directly.

## Typical Use

The library comes with a collection of tests which may also be used as
examples of the library's use. The test / example `ldapsearch` is
extensively documented; it reads a binary dump (DER) of an LDAP
search request, and prints out the filter expression that is found
in that search.

The example works with the low level interface: it explicitly calls
routines like `der_enter()` to explore the DER data.

### Validation of DER

To validate the structures written in DER, both `der_unpack()` and `der_walk()`
can be used.  Most other routines are coded for flexibility and should not be
assumed to validate DER in more detail than strictly required.

The `der_unpack()` routine runs through the entire structure, and validates
the tags it runs by, as well as the complete nesting structure it encounters.
It is a complete validation of the structures.

The `der_walk()` routine performs *lazy validation*, meaning that it will
carefully check tags and nesting inasfar as it is needed to get from its
starting point to its end point.  Anything but the paths explored will be
accepted without question.

### LDAP Handling

The [LillyDAP](https://github.com/vanrein/lillydap/) framework builds on
top of Quick DER to process LDAP messages. It uses the headers for LDAP
(RFC 4511) from Quick DER and the higher level API to translate DER data
into C structures.

LillyDAP, in turn, is a framework for building miniature LDAP services.
These can help you centralise your data storage under own control; for
instance, your PGP key ring or your vCard collection are good candidates
for sharing locally.

## Future Plans

There are a few things that this library can use:

  * **More testing.** The current `test` directory is far too small; we can
    take a PKIX certificate apart and re-compose it, so we're definately doing
    something good, but this is nowhere near thorough testing.  If you run
    into a problem case, then *please* share it so we can solve it and extend
    our test base.
  * **Compiler output testing.** The compiler output is currently compiled to
    see if there are C syntactical problems, but that is all.  They have been
    visually compared to manually crafted code, too.  More exhaustive tests,
    including a full application, would be in order.

And of course, there are many useful things we may do with this library:

  * **Kerberos in PKIX.** [Certificates wrapping Kerberos Tickets][pkix] for
    use with [TLS-KDH](https://tools.ietf.org/html/draft-vanrein-tls-kdh),
  * **Remote PKCS #11.** The main issue in doing this well is proper
    encapsulation, but with Quick and Easy DER, and the emphasis of both on
    security and well-defined sizes, it appears to be a perfect match to
    wrap PKCS #11 arguments in DER structures.

[pkix]: (http://github.com/arpa2/kerberos2pkix)
