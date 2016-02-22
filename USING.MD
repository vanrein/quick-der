# Quick DER parsing support

![Quick DER logo](quick-der-logo.png)

> *Quick DER parsing aims to get you started with the parsing of DER (and most
> BER) encoded ASN.1 data really quickly.  It also aims to makes quick parsers,
> by using shared data structures whenever possible.*

**Note: This is a preview of features to come; for now, it is no promise, but merely a rough sketch of what is to come.**

## Outline of using this library

Working with the quick DER library is really quick to learn.

### Preparing your build environment

The first thing you do, is parse an ASN.1 specification that you may have gotten
from any source -- for example, from an RFC.  You map it to a header file and a
parser specification file:

    qder_from_asn1 myspec.asn1 myderparser.c myderparser.h

Your source code dealing with DER should read the entire block, and pass it to
the DER parser.  Initially, it would include:

    #include <der/qparse.h>
    #include "myderparser.h"

and builing should include:

    gcc -o myparser.o myparser.c
    gcc ... myderparser.o -lqder

You may be lucky, and find your favourite spec precompiled.  In that case, you
can limit yourself to things like:

    #define RFC5280_PREFIX pkix_
    #include <der/qparse.h>
    #include <der/rfc5280.h>

and link with simply:

    gcc ... -lqder


### Parsing DER structures

Before you get to parse DER-encoded structures that match the ASN.1 syntax,
you should read the entire data into memory.  The parser output will not
clone bits and pieces of data, but instead point into it with cursors; these
are little structures with a pointer and a length.  Note that this means that
strings are not NUL-terminated; printing them may be different than what you
are accustomed to:

    printf ("%s\n", derelem->ptr);                  // Unbounded string
    printf ("%.*s\n", derelem->len, derelem->ptr);  // Perfect printing

Now, to invoke the parser, you setup a cursor describing the entire content,

   dercursor_t thelot;
   thelot.derptr = ...pointer-to-data...;
   thelot.derlen = ...length-of-data...;

then you invoke the parser, providing it with storage space and the
precompiled structure to follow while parsing:

   struct pkix_Certificate crt;
   int prsok = der_unpack (&thelot, asn1_pkix_Certificate, &crt, 1);

This will parse the DER-encoded data in `thelot` and store the various fields
in `crt`, so it becomes available as individual cursor structures such as
`crt.tbsCertificate.validity.notAfter`.  This follows the structure of the
ASN.1 syntax, and uses field names defined in it, to gradually move into
the structure.  The header file defines those names as part of the
`asn1_pkix_Certificate`.

Something else that can now be done, is switch behaviour based on the the
various fields that contain an `OBJECT IDENTIFIER` for that purposes.  These
can usually be treated as binary settings to be compared as binaries.  The
`dercmp()` utility does this by looking at the length as well as binary
contents of such fields, as in

    if (dercmp (&crt.signatureAlgorith.algorithm, RSA_WITH_SHA1) == 0) {
       ...the OIDs matched...
    } else ...other cases...


## Iterating over repeating structures

Many structures in ASN.1 are variable in the sizes of primitive data types, but
have a fixed composition structure.  And `OPTIONAL` parts can be parsed and their
respective structure fields set to NULL when they are absent.  This also happens
to values setup with a `DEFAULT` value in ASN.1 (note that their default value
is not filled in by the parser).

But some structures are not parsed immediately, because they might have a
repeated structure, and thus won't fit into a structure; not if the assumption
is that dynamic allocation should not be done by the parser.  For such
repeating structure, there are two options, namely iterating over their
contents or allocating memory and having them filled by the parser.

To iterate over a repeated structure, simply use the two routines setup for
that in quick DER, as in:

    if (der_iterate_first (&crt.tbsCertificate.extensions.packed, &iter)) do {
       ...treat extension pointed to by iter...
    } while (der_iterate_next (&crt.tbsCertificate.extensions.packed, &iter));

This requires no dynamic allocation, and simply handles each of the extensions
in a certificate one by one.

## Allocating space for a repeating structure

The structures that repeat are limited to the ASN.1 constructs
`SEQUENCE OF` and `SET OF`.  When these occur, the parser will not unfold
the contained structure, but simply store the whole structure.  We will
refer to that as "packed" representation, meaning the binary DER format.

It is possible to replace packed notation by unpacked, by assigning to it
an array of suitable size to contain the required number of elements,
and then unfold the repeated structure into it:

    size_t count = der_countelements (&crt.tbsCertificate.extensions.packed);
    pkix_Extensions *exts = calloc (count, sizeof (pkcix_Extensions));
    if (exts === NULL) {
       ...handle error...
    }
    prsok = der_unpack (&crt.tbsCertificate.extensions.packed, asn1_pkix_Extension, exts, count);

This will unpack `count` times the structure described by `asn1_pkix_Extension` and place the output in `count` structures in the array `exts`; note that the earlier
call the `der_unpack` had a parameter `1` in the position of `count`.

When successful, the `der_unpack()` routine replaces the `extensions.packed`
structure, which is a plain `dercursor_t`, with an unpacked structure
`unpacked` which has elements `derray` pointing to an array of cursors and
an element `dercnt` with the number of cursors in that array.  When this
is setup, the `.packed` version of the data is destroyed; the `.packed` and
`.unpacked` versions are in fact labels of a union.

Note that structures such as `crt` may hold a lot of useful naming, but they
are just a cleverly constructed overlay form for an array of `dercursor_t` fields,
which is exactly how `der_unpack` treats them.  The ASN.1 parsing instructions
are matched to the structures so that no data will be sticking out of these
array-like structures.

## Composing DER output

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

