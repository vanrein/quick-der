# Quick DER parsing support

<img alt="Quick DER logo" src="quick-der-logo.png" style="float: right;"/>

> *Quick DER parsing aims to get you started with the parsing of DER (and most
> BER) encoded ASN.1 data really quickly.  It also aims to makes quick parsers,
> by using shared data structures whenever possible.*

The low-level API for Quick DER is documented in `quick-der/api.h`, the
header that is installed with the library. The document here describes
general usage patterns and how to process your own ASN.1 definitions
for your own projects.

## Quick DER Patterns

Working with DER data and the Quick DER `dercursor_t` requires some diligence,
since the data is packed and strings are not NUL-terminated.

### Printf() and DER cursors

DER strings are not NUL-terminated (as in C) but have a length field.
The `dercursor_t` has a pointer to the data and a length field, so
printing them may be different than what you are accustomed to:

    printf ("%s\n", cursor->ptr);                  // BAD: Unbounded string
    printf ("%.*s\n", cursor->len, cursor->ptr);   // GOOD:  Bounded print

### Memory Management

Quick DER does no dynamic memory allocation, although for ASN.1
structures with a dynamic size (e.g. SET OF) you can use external
memory allocation and overlay `dernode_t` over a cursor.

A converse of no allocation means that memory management of
the buffers and data regions for DER data must be done externally
as well. It is the caller's responsibility to read (complete)
DER data into a buffer somewhere and set up a `dercursor_t`
pointing to that data:

    dercursor_t thelot;
    thelot.derptr = ...pointer-to-data...;
    thelot.derlen = ...length-of-data...;

### Iterating over repeating structures

Many structures in ASN.1 are variable in the sizes of primitive data types,
but have a fixed composition structure (e.g. `SEQUENCE OF`).  Any `OPTIONAL`
parts can be parsed and their respective structure fields set to NULL when
they are absent.  This also happens to values setup with a `DEFAULT` value
in ASN.1 (note that their default value is not filled in by the parser).

A no-allocation pattern for dealing with these structures will iterate over
the (not-parsed) repetitive structure using the two routines setup for
that in quick DER, as in:

    /* Assuming cursor points to a repeating structure */
    dercursor_t iter;
    if (der_iterate_first (&cursor, &iter)) do {
       /* ...handle DER data pointed to by iter... */
    } while (der_iterate_next (&iter));

Note that most Quick DER functions return 0 for success, but these
iterator-functions do not do so, so that they can be used in this
pattern (sticking to the other calling convention would require
putting in strange-looking nots).

### Allocating space for a repeating structure

The structures that repeat are limited to the ASN.1 constructs
`SEQUENCE OF` and `SET OF`.  When these occur, the parser will not unfold
the contained structure, but simply store the whole structure.  We will
refer to that as "packed" representation, meaning the binary DER format.

It is possible to replace packed notation by unpacked, by assigning to it
an array of suitable size to contain the required number of elements,
and then unfold the repeated structure into it:

    /* Assuming cursor points to a repeating structure of
       some DER type, and that there are Quick DER generated
       foo_t (for the type) and asn1_foo_t (for the packing walk).
    */
    size_t count = der_countelements (&cursor);
    foo_t *foo_cursors = calloc (count, sizeof (foo_t));
    if (exts === NULL) {
       /* ...handle error... */
    }
    prsok = der_unpack (&cursor, asn1_foo_t, foo_cursors, count);

This will unpack `count` times the structure described by `asn1_foo_t` and
place the output in `count` structures in the array `foo_cursors`; note that
the usual way to call `der_unpack` has the parameter `count` set to `1`.

When successful, the `der_unpack()` routine replaces the `cursor`
structure, which is a plain `dercursor_t`, with an unpacked structure
`unpacked` which has elements `derray` pointing to an array of cursors and
an element `dercnt` with the number of cursors in that array.  When this
is setup, the `.packed` version of the data is destroyed; the `.packed` and
`.unpacked` versions are in fact labels of a union.

Note that structures such as `foo_t` may hold a lot of useful naming, but
they are just a cleverly constructed overlay form for an array of
`dercursor_t` fields, which is exactly how `der_unpack` treats them.  The
ASN.1 parsing instructions are matched to the structures so that no data
will be sticking out of these array-like structures.

### Composing DER output

The composition of DER output uses the same ASN.1 structural descriptions as
the unpacking process.  It is possible to use `.packed` structures, but once
they are unpacked it becomes necessary to prepare repeating structures for
repackaging.  This uses the `der_prepack()` function:

    int prsok = der_prepack (TODO);

This sets up a third flavour of the repeated structure, namely `.prepacked`.
In this form, the `derlen` value has been set to the eventual length of
the to-be-formed DER structure, but the `derray` value still points to the
array of `dercursor_t` holding the to-be-filled data.  This `derlen` field
can subsequently be used during the future packing process.

TODO: How to distinguish packed, unpacked and prepacked lengths?  Tag or size bits?


## Using Quick DER with Custom ASN.1

The first thing you do, is parse an ASN.1 specification that you may have
gotten from any source.  You map it to a header file and a parser
specification file:

    $ asn2quickder myspec.asn1   # creates myspec.h and myspec.h

Your source code dealing with DER should read the entire block, and pass it to
the DER parser.  Initially, `myspecparser.c` would include the
Quick DER and myspec headers:

    #include <quick-der/api.h>  /* low-level Quick DER API */
    #include "myspec.h"         /* high-level API for myspec */

and building should include:

    gcc -c -o myspecparser.o myspecparser.c
    gcc ... myparser.o -lquickder

If you have `pkg-config` installed, you can use it to get the
compile and library flags for Quick DER:

    gcc `pkg-config quick-der` -c -o myparser.o myparser.c
    gcc ... myparser.o `pkg-config quick-der --libs`

If you use CMake as (meta-) build system, then use the standard
CMake module-finding tools:

    find_package (Quick-DER REQUIRED)
    include_directories (${Quick-DER_INCLUDE_DIRS})
    target_link_libraries(myspecparsertarget ${Quick-DER_LIBRARIES})
    # Alternative, link to ${Quick-DER_STATIC_LIBRARIES}

This approach should only be needed for your private ASN.1 specifications,
since Quick DER strives to include header files for common standards,
including RFCs, as well as ITU and ARPA2 specifications.  (If you need to do
the work on any of these, please send us a patch to include it in future
development packages of Quick DER!)  Specifications that have been included
with the library can be used simply by including the appropriate header
(e.g. for certificates from RFC 5280):

    #include <quick-der/api.h>
    #include <quick-der/rfc5280.h>


## Example: Parsing RFC5280 structures

> This is an outline of a program for handling RFC5280 certificates.
> For a full worked example, see [test/ldapsearch.c] which is included
> with the library (and used as one of the tests).

Since Kerberos structures are defined (in the default configuration) of
a Quick DER installation, the header file can simply be included:

    #include <quick-der/api.h>
    #include <quick-der/rfc5280.h>

Before you get to parse DER-encoded structures that match the ASN.1 syntax,
you should read the entire data into memory.  The parser output will not
clone bits and pieces of data, but instead point into it with cursors; these
are little structures with a pointer and a length.

Now, to invoke the parser, you setup a cursor describing the entire content,

    dercursor_t thelot;
    thelot.derptr = ...pointer-to-data...;
    thelot.derlen = ...length-of-data...;

then you invoke the parser, providing it with storage space and the
precompiled structure to follow while parsing. The header for RFC 5280
defines C structures of named `dercursor_t` for the datatypes defined
by the RFC. Since the top-level structure is a Certificate, use that
structure and the corresponding packing walk:

    struct DER_OVLY_rfc5280_Certificate crt;
    static const derwalk certificate_walk[] = {
      DER_PACK_rfc5280_Certificate, DER_PACK_END };

    int prsok = der_unpack (&thelot, certificate_walk, &crt, 1);

This will parse the DER-encoded data in `thelot` and store the various fields
in `crt`, so it becomes available as individual cursor structures such as
`crt.tbsCertificate.validity.notAfter`.  This follows the structure of the
ASN.1 syntax, and uses field names defined in it, to gradually move into
the structure.  The header file defines those names as part of
`DER_OVLY_rfc5280_Certificate`.

Something else that can now be done, is switch behaviour based on the the
various fields that contain an `OBJECT IDENTIFIER` for that purposes.  These
can usually be treated as binary settings to be compared as binaries.  The
`dercmp()` function does this by looking at the length as well as binary
contents of such fields, as in

    if (dercmp (&crt.signatureAlgorith.algorithm, RSA_WITH_SHA1) == 0) {
       /* ...the OIDs matched... */
    } else {
       /* ...other cases... */
    }

TODO: dercmp() doesn't actually exist.

