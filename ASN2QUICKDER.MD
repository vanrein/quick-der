# ASN.1 Compiler Tools for Quick (and Easy) DER

<img alt="Quick DER logo" src="quick-der-logo.png" style="float: right;"/>

> *Quick DER, or if you like, "Quick and Easy DER", is a library for handling
> DER, which is a widely used binary representation of ASN.1 syntax in binary
> formats.  The compilers are used to transform the ASN.1 format into forms
> that can be used in C and Python.  Often, code changes only marginally after
> edits to the data format, which helps to make ASN.1 a Quick `n' Easy data
> format.*

The tools **included** here are:

  * `asn2quickder` for mapping ASN.1 specifications to a programming
    language module.
  * `asn1literate` for mapping ASN.1 specifications to readable MarkDown
    files, supportive of a Literate Programming style description.

The **dependencies** for this package are:

  * [asn1ate](https://github.com/kimgr/asn1ate)
    is the underlying generic ASN.1 parser for which
    `asn2quickder` is a generating backend.

.. contents::


## Split from Quick DER itself

We are trying to distribute `asn2quickder` on its own, so separately
from Quick DER.  This is because they serve different purposes and
are also built in separate stages:

  * `asn2quickder` and `asn1literate` are development tools,
    normally required during development of an ASN.1 based protocol.
  * Quick DER is a library of precompiled ASN.1 modules, mostly for
    standards enhanced with our own work for ARPA2.

We don't know yet if the split will make sense.  Some parts may be
useful to both, such as the libraries.  We shall experiment with it
to learn what is the best option.


## Using asn2quickder with C

The basic data structure for working with Quick DER is the
`dercursor` which holds two elements:

  * `.derptr` points at data;
  * `.derlen` holds the pointed-at length;
  * absent values have their `.derptr` set to `NULL`.

Data is packed and unpacked into arrays of these structures.

We have provided a simple `asn2quickder` compiler based on
[asn1ate](https://github.com/kimgr/asn1ate)
to derive C header files holding the following definitions:

  * `DER_PACK_$(MODULE)_$(TYPE)` holds packer instructures, except
    for a terminating `DER_PACK_END` as that would stop you from
    concatenating packer instructions.
  * `DER_PIMP_$(MODULE)_$(TYPE)` is a variant to these packer
    instructions, taking an initial tag; this may be needed when
    `IMPLICIT TAGS` are being used.
  * `DER_OVLY_$(MODULE)_$(TYPE)` is a data structure that overlays
    the packer's array of `dercursor` data structures, and that
    allows walking through complex structures by using ASN.1
    field names as the field names of structures.

The packer is called `der_pack()` and it combines a `dercursor[]`
with packer instructures to form a DER blob.  The unpacker is called
`der_unpack()` and it takes a DER blob apart to fill a provided
`dercursor[]`.  In both cases, the array is usually aliased with
an overlay for easy navigation with ASN.1 field names.

The ASN.1 modules get translated to a file named `$(MODULE).h` and
these are include with code like

```
#include <arpa2/quick-der.h>
#include <my-app/my-module.h>
```

The first include file provides general definitions, like
`DER_TAG_SEQUENCE` and `DER_PACK_END`, structures such as
`dercursor` and prototypes for the API functions;
the second is the module that `asn2quickder` generated from
an ASN.1 source.


### Very Small

The smallest applications can use Quick DER, especially when they
link statically.  We provide a static library with most functions
separated.  The code is extremely small.

There are efficient standard routines such as `der_get_int32()`
for extracting a 32-bit integer value, or `der_put_uint32()` for
storing one in DER format.


### Batteries included

We provide the Quick DER package with much more than just the
API include file.  So, you can include Quick DER and move on
with one the many standards that are already provided:

```
#include <arpa2/quick-der.h>
#include <quick-der/rfc5280.h>
```

If you need to use ASN.1 from an RFC, then you probably don't
need ASN2QuickDer.  If you want to expand on the standard set
you do.  Please consider donating your ASN.1 source if your
work is moving towards a standard of any kind!  We tend to
add such work to the standard tooling for Quick DER to allow
easy dissimination of ASN.1 formats.  Since they only hold
include files, they have no negative impact on runtimes.


## Using asn2quickder with Python

You can compile to Python and then include the resulting
file as a module, where the ASN.1 type names will show up
as class definitions in the module.

You can then instantiate those classes with a DER blob as
its parameter.

As for C, you only need ASN2QuickDER if you are designing
your own ASN.1 specifications, or if you intend to use
someone else's non-standard modules.  When you distribute
source code with your own ASN.1 specifications, you should
add ASN2QuickDER as a dependency package.


## Using asn1literate

The `asn1literate` tool extracts comment lines that start
with `--` in ASN.1 and makes them into MarkDown content.
Conversely, lines with ASN.1 content are turned into
quoted/literal blocks.

This very simple transformation can be helpful to make your
ASN.1 specifications more easily distributable.  You can
use this by documenting excessively what the meaning is of
each of the structures because, remember: data structure
is not the same thing as semantics.

Literate Programming is a technique by Donald Knuth, who
used it in teaching.  He would write documents and insert
code fragments.  Special tools were used to extract the
formal content and allow it to process.  Several modern
tools follow a similar paradigm, or the reverse where the
documentation is extracted from code.  The `asn1literate`
tool is precisely like that.
