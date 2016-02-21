# Quick (and Easy) DER, a Library for parsing ASN.1

![Quick DER logo](quick-der-logo.png)

> *Quick DER, or if you like, "Quick and Easy DER", is a library for handling
> DER, which is a widely used binary representation of ASN.1 syntax in binary
> formats.  The library describes ASN.1 syntax in a parser table that can be
> fed into library routines, resulting in pointer/length descriptors for the
> individual data fragments.*

## Basic Usage

The basic approach of using this library is translating the ASN.1 syntax into
a parser table.  This is done when building your software, as a phase preceding
the compilation of your Quick DER using program.  The translation from ASN.1
to C code can be done manually and **TODO** will in the future be automated with
an ASN.1 parser.

The resulting *path walks* are used in calls like `der_unpack()` to transform
DER into C-style structures, and `der_pack()` to make the opposite transformation.
The C-style structures are derived from the ASN.1 syntax, and permits access to
the information with no further need of understanding the depths of processing
DER.

Since you are handling binary data (rather than character strings), all data
is described in so-called `dercursor` structures; each containing a pointer
and a size of the data pointed at.


## Basic Code Structure

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


## Extra Code Facilities

There are routines `der_iterate_first()` and `der_iterate_next()` routines
to manually iterate over a DER structure's components.  This can be used to
analyse structures that have not been unpacked (yet).  The `der_countelements()`
routine can be used to predict the number of iterations.

There are also routines to manually walk through packaged DER structures,
namely `der_enter()` and `der_skip()` to enter into a nested structure and to
find the next element in a concatenation of such elements.

A much more advanced form of such walks through a DER structure exists in the
form of `der_walk()`, which is fed another kind of walk, a sequence of enter/skip
statements with tags that will be validated.


## Validation of DER

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

### Relation to BER

*This is for ASN.1 experts; others can safely skip this subsection.*

The Quick DER library is designed to process DER, although it will also accept
some of the more general BER format.  If a length or value is written in more
than the minimal space, the library is still likely to accept it.  Note that
the `BIT STRING` type is somewhat likely to run into overflow problems, so
there the full restrictiveness of DER is applied.


## No Memory Allocation

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


## Future Plans

There are a few things that this library can use:

  * **Proper tests.** The current `test` directory is far too small; we can take a PKIX certificate apart and re-compose it, so we're definately doing something good, but this is nowhere near thorough testing.  If you run into a problem case, then *please* share it so we can solve it and extend our test base.
  * **ASN.1 compilation.** The compiler for [libtasn1](http://git.savannah.gnu.org/cgit/libtasn1.git/tree/lib) may be an interesting piece of software to modify to create the `derwalk[]` structures that we currently create by hand, together with the overlay structures with syntax-derived labels.
  * **RFC Library.** A collection of most/all standards that use DER today, in a pre-compiled form that can simply be included as `<quick-der/rfc5280.h>` and then permits processing of the structures defined in it (in this case, PKIX Certificates).

And of course, there are many useful things we may do with this library:

  * **Kerberos in PKIX.** [Certificates wrapping Kerberos Tickets](http://github.com/arpa2/kerberos2pkix) for use with [TLS-KDH](https://tools.ietf.org/html/draft-vanrein-tls-kdh)
  * **Miniature LDAP services.** These can help you centralise your data storage under own control; for instance, your PGP key ring or your vCard collection are good canidadates for sharing locally.

