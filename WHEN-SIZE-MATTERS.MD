# Quick DER sizes: Sometimes small is bettar

![Quick DER logo](quick-der-logo.png)

> *This is a decription of the sizes of structures used by Quick DER.  As this
> demonstrates, the library is quite useful for embedded purposes.*

Using Quick DER, an include file is derived from an ASN.1 syntax specification.
The include files contain fixed parsers for the various structure that can be
assigned to constant byte arrays, and then applied to a dowloaded sequence of
bytes in DER format.

Data is generally stored in the form of a dercursor.  This is a combination
of a pointer to DER data with a size of the data from that point.  We measure
memory consumption for data storage in such structures; they point the the
already-allocated memory that holds to-be-analysed DER input.  The length of
the actual data handled is therefore not included below, since it can vary
virtually without bounds.


## Code size

The following data stems from analysis of the `.text` segment of version TODO
of Quick DER:

  * 261 bytes for `der_header()`
  * 079 bytes for `der_iterate_first()`, `der_iterate_next()` and `der_iterate_next()`
  * 141 bytes for `der_skip()` and `der_enter()`
  * 761 bytes for `der_unpack()`
  * 008 bytes for `der_prepack()`
  * 788 bytes for `der_pack()`
  * 376 bytes for `der_walk()`

Note that `der_header()` is the only dependency for most other modules.
Some modules will write into `errno` as well.

The total size of all these modules is 2405 bytes.  Note that this includes
alternatives; it is possible to use just `der_walk()` to walk into structures,
or one might do it with `der_unpack()`.  The choice is there but there is no
need to mix the styles if you are pressed for space.


## Data storage

This is expressed in the number of dercursor structures needed to address
portions of already-allocated DER code space.  Note that Quick DER never
allocates dynamic memory for itself, so you are free()d from memory management
for these routines.

Moreover, the routines help you to avoid allocating dynamic memory too.  The
walker construct, together with basic movements inside DER structures, makes
it easy to setup a cursor and have it traverse paths.  And there are iterators
to walk through SEQUENCE OF and SET OF structures.

The only reason you might have to allocate memory is when you intend to fully
der_unpack() into SEQUENCE OF and SET OF structures.  In this case, the output
in the form of an dercursor array can have any size due to the variable size
of the repeated structure.  You may be forced to use this if your aim is to
der_pack() the structure later, because it may otherwise end up as a Primitive
structure, which may not be what you intended to deliver.  But even then, it
is a matter of dercursor structures, not the full-blown packaged data size.
After taking ample size precautiouns, this might easily be done on a stack.

The other components of variability do not require explicit allocation, because
the space for all their variants can be unfolded and separately stored.
This applies to OPTIONAL / DEFAULT as well as to CHOICE.  Entries that were
not parsed are simply set to NULL dercursor values, so it is detectable that
they were not present in the input (and should not appear in the output).
The ANY element is parsed by providing the entire structure at its position,
including its header (and tag).  You can use der_enter() or der_header() to
skip or analyse the header, and/or you could start a new der_unpack() or
der_walk() to get into the structure, based on the applicable syntax.

The number of dercursor structures created depends on the parser prescription.
Here is the count for der_unpack()ing a few standard structures:

  * 16 dercursor values for a PKIX Certificate
  * 03 dercursor values for a PKIX Certificate Extension
  * 07 dercursor values for a Kerberos5 Ticket
  * 14 dercursor values for a Kerberos5 Ticket's EncTicketPart

Oh, and the walking paths that instruct the parser are very small too:

  * 46 bytes for a PKIX Certificate
  * 07 bytes for a PKIX Certificate Extension
  * 33 bytes for a Kerberos5 Ticket
  * 55 bytes for a Kerberos5 Ticket's EncTicketPart

Quite humble, isn't it?


## Stack size

The storage needed on the stack depends solely on routine nesting depth.
The nesting depth depends on the ASN.1 syntax descriptions being processed;
since it does not depend on the data, there is no risk of a stack overflow
caused by too large data.  (You should of course still be careful when you
allocate dynamically sized, that is, input-determined, data on your stack.)

With der_walk() there is never any nesting.  For der_pack() and der_unpack()
the nesting is determined by the number of ENTER / LEAVE pairs.
In addition, der_pack() will nest for components prepared with der_prepack()
which might also be prepared in a nested fashion.  In addition, der_unpack()
will nest for CHOICE sequences.

The following indications provide some information on the maximum reached
nesting depth while running der_unpack() over some standard structures:

  * 4 nesting levels for a PKIX Certificate
  * 1 nesting levels for a PKIX Certificate Extension
  * 5 nesting levels for a Kerberos5 Ticket's unencrypted part
  * 5 nesting levels for a Kerberos5 Ticket's EncTicketPart

The reason that Kerberos is using a few more nesting levels is that it uses
explicit tagging very liberally.  It's a modest cost for such a bright use
of ASN.1 and especially to achieve extensibility in the data formats.


## Benchmarking Environment

The aforementioned figures were obtained using:

  * `gcc` 4.7.2
  * `CFLAGS=-Os -ggdb3 -c`
  * `objdump -h -j .text *.o`
  * The first GIT checkin of the source code (may be updated later on)

The choice for `-Os` was based on the intention to demonstrate suitability
for embedded environments.  It saved about 42% code size compared to `-O0`
(no optimisation) and about 25% compared to `-O2` (often used in projects as
their default optimisation).

