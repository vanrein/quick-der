# Compiling ASN.1 to the Python mapping of Quick-DER

> *This document explains the structures and conventions used in the
> Python mapping of Quick DER.*

The Python mapping of Quick DER consists of library modules, mainly the
`api.py` file that supplies the `quick_der.api` include, and packages
such as `quick_der.rfc4120` that are derived from specifications.  The
Quick DER package generates and installs such packages for many standards.
It allows the user to say such things as

    from quick_der.rfc4120 include Ticket
    tkt = Ticket (derblob=...)

Below are the rules that cause this sort of magic to work.


## Name Spaces for ASN.1 and Python

There are several places where the name spaces of ASN.1 and Python need to
co-exist.  In these cases, the Python names start with an underscore.

ASN.1 names combine letters, digits and dashes, but they start with a letter.
As a result, even though we map dashes to underscores, we can never have a
name clash on account of that.

The `api` module is specifically meant to capture a Python name space with
classes such as `ASN1Object`.  There are no ASN.1 names in this context.
Do be careful when including it though; it may need to be included as `_api`
when name clashes can occur.  This is only really a concern when including
it in generated Python code however.


## ASN.1 Type Assignments map to Python Classes

An ASN.1 module can hold various kinds of definitions; we only look at
type assignments (for now), which define a name for a type having an ASN.1
definition.  Such names are mapped to a Python class by the same name,
within a file that indicates which module held the definition.

ASN.1 modules can include symbols from other ASN.1 modules, which is
mapped pretty much literally to the same Python construct.  This means
that definitions can incorporate fields of a type defined in another
module.

The classes defined for an ASN.1 type assignment are subclasses of a
few general definitions in the `quick_der.api` package.  The following
general definitions are used, each of which is a subclass of the most
general class `ASN1Object`:

  * `ASN1Atom` defines elementary values, such as integers and strings.
     NOTE: It is not clear yet if we will use this everywhere; often,
     it should suffice to just supply the literal bytes as a Python
     `string`.

  * `ASN1ConstructedType` defines name-to-type mappings at the class
     level, and name-to-value mappings at the instance level.  This
     is used to map `SEQUENCE`, `SET` and `CHOICE` types.

  * `ASN1SequenceOf` defines repeated values that are each of the same
     type.  It can be manipulated like Python's `list` type, of which
     it is a subclass.

  * `ASN1SetOf` defines repeated values that are each of the same
     type.  It can be manipulated like Python's `set` type, of which
     it is a subclass.

When types have a name due to an ASN.1 type assignment, they will be
generated in a class that subclasses these values.  If no name is
available, then a direct instance of the aforementioned classes is
made, which requires setting a few internal veriables defined below,
mostly to describe the structure and its processing.


## User Calling Conventions

Users of ASN.1 modules mapped to Python can use the generated type-named
classes as follows, where we use `Ticket` from RFC 4120 as an example class:

    import quick_der.api
    from quick_der.rfc4120 import Ticket

    # Construct an empty Ticket instance
    tkt = Ticket ()

    # Construct a new Ticket instance for a given DER blob
    tkt = Ticket (derblob=der_data)

    # Map a Ticket instance to DER
    der_data = tkt._der_pack ()

    # Map an object to DER, alternative form
    der_data = quick_der.api.der_pack (tkt)

Plus, named fields as well as list and set elements may be manipulated as
the user sees fit.

### Why NULL is not None

Values that are set to `None` indicate that nothing
was parsed for them; please note that this is fundamentally different
from the `NULL` object in DER, which does have an encoding and will indeed
be stored as any other type; its value is usually the empty string but
having a value set is what it is about -- it will respond positively when
Python tests the value to differ from `None` to indicate presence of the
`NULL` element in the DER flow.

Note how this distinction can make a vital difference in the semantics of
a simple ASN.1 type like `NULL OPTIONAL` -- which is `None` when the `NULL`
is not encoded, or an empty string object when it is encoded.


## Static Class Descriptors

When a class is constructed (for a type assignment), it will be setup with
two variables that are considered shared by all instances:

  * `_der_packer` is the packer description used by the internal
    `der_pack()` and `der_unpack()` routines (from the C code, imported
    as a `_quickder` shared object).  It is a binary string that ends in
    the defined code for `DER_PACK_END`.

    It is possible to design custom `_der_packer` values in your own classes,
    using the symbols defined in both the C header and the `quick_der.api`
    package.  Be careful, you can easily crash your system if you do this
    badly; but once it runs reliably you will not have to worry anymore,
    so it can provide solid DER parser code.  Of course you may also write
    your own ASN.1 specification and map it using `asn2quickder` yourself;
    this is normally done when building the Quick DER package.

  * `_recipe` describes how the output from `der_unpack()`, which is a
    list of blobs, should be further processed to construct the instance
    value.  Following the structure of the actual data, this forms a
    nested type.  Where type definitions may be recursive, this is reflected
    in a `_recipe` through references to type-named classes.

  * `_context` is the name context in which the class is created.  It is
    simply set to the return value of `globals()` at the time, and it serves
    as a reference context for the lazy linking procedure described below.

  * `_numcursori` is the number of `dercursor` structures output by the
    `_der_packer`.  Its main use is to construct an empty `ASN1Object`
    instance, for which it needs to be known how many `None` elements are
    to be setup.

The output of `der_unpack()` is further described as `_bindata`, which is
a Python list holding Python binary strings with each of the pieces of data
stored through a `DER_PACK_STORE | DER_TAG_xxx` byte in the generated packer.
When a bit of the encoding is absent, it will be set to `None` instead of to
a binary string.  Note that this occurs habitually in places where ASN.1
uses `OPTIONAL` or `DEFAULT` flags, or for non-selected parts of `CHOICE`
elements.

The `_recipe` can take on a number of forms, but is generally a tuple whose
first field is used to determine the variant; this first field is either an
underscore plus a fixed name, or it is a user-defined ASN.1 type name which
is also a Python name for a generated, type-named class.  There is one
optimisation however; we do not write `('_INDEX',offset)` but use the `int`
type of `offset` to distinguish this outcome.

  * `offset` presents an integer `offset` into the current
    `_bindata`, after addition of the contextual `_offset`
  * `('_NAMED',{ field: sub_recipe, ... })` defines
    a dictionary to map `field` names in
    ASN.1 constructed types `SEQUENCE`, `SET` and `CHOICE` to a `sub_recipe`
    that adheres to the same format; the `sub_recipe` can suggest the
    instantion of an element attached to the named `field`
  * `('_SEQOF',allidx,pack_recipe,element_recipe)` tuples indicate that a
    `SEQUENCE OF` must be instantiated, with the total contents stored in
     `allidx` and, for further analysis, a `pack_recipe` from which a
     `der_packer` can be derived for the sequence elements, and
    `element_recipe` used to instantiate elements.
  * `('_SETOF',allidx,pack_recipe,element_recipe)` tuples indicate that a
    `SET OF` must be instantiated, with the total contents stored in
    `allidx` and, for futhre analysis, a `pack_recipe` from which a
    `der_packer` can be derived for the set elements, and
    `element_recipe` used to instantiate elements.
  * `('_TYPTR',[class],ofs)` tuples reference an `ASN1Object` subclass, whose
    contained `_recipe` is used to further nail down the `_bindata`
    starting at `ofs`, which is relative to the `_offset` of the object
    whose class holds the `_recipe` in which this form occurs; so the
    `offset` parameter used to instantiate the `class` is the sum of this
    reference `_offset` and the `ofs` supplied here.  The `class` may be a
    name (typed `str`) or, after late linking, it may be a subclass of
    `ASN1Object`.  The form `[class]` instead of `class` permits in-place
    substitution of the value.

Note how the outer level of each of these can be used to derive the choice
between `ASN1Atom`, `ASN1ConstructedType`, `ASN1SequenceOf` and `ASN1SetOf`.
The `_TYPTR` plays a special role; it may be dereferenced or instantiated,
or it may be used to make an immediate equation when types are equated to
form aliases, so ASN.1 notation `D ::= C` could translate to Python `D = C`
instead of a full class abstraction.  (Although we probably won't do that;
this both requires ordering of such a rule under the definition of `C` and
it suppresses class information which may be useful on its own.)

The `pack_recipe` is a form from which a `_der_packer` can be derived, namely
a list of strings.  Most of the strings are a `DER_xxx` macros, or perhaps
two with an intermittent `|` operator.  This form is used to generate the
binary string form that is directly usable to Quick DER.  In the `pack_recipe`
however, the nicest form is a single binary string that can be employed
directly for further unpacking.  The problem is that it might include type
references that have not been resolved at the time the `pack_recipe` is
parsed, so a lazy linking mechanism is needed.  This is achieved as follows:

  * The `pack_recipe` is generally a list of at least one element.  The first
    element holds either `None` or the linked form, which is substituted
    after lazy linking it.
  * When a `pack_recipe [0] is not None` its further elements will be ignored,
    so it may be removed (except perhaps in the interest of debugging).
  * When encountering a `pack_recipe [0] is None`, the linking is started and
    the substitution is made.
  * A valid `pack_recipe [0]` is a single binary string in the same format as
    the `_der_packer`, including the final `DER_PACK_END`.  This format is
    obtained by the lazy linking mechanism, and inserted in place so that
    it only needs to perform the linking once per occurrence.
  * The `der_packer [1:]` is a list of descriptions in the
    same form as passed internally by the generator (strings like
    `DER_PACK_ENTER | DER_PACK_SEQUENCE`) interspersed with an extra form
    `?TypeName` that lazily resolves to a reference to the class `TypeName`,
    similar to the `_TYPTR` mechanism that will usually parallel it.
  * In addition to the above, the `DER_xxx` labels may be prefixed with a
    package name, so they only need to pass through `chr()`; this prefix is
    a normal Python identifier, so it will never start with `?` and can thus
    be clearly distinguished.
  * The rewriting of each form results in a list expression that can be
    passed into `eval()`, which will yield a binary string in the same format
    as the `_der_packer` in a class.  This form adds a final `DER_PACK_END`,
    as with a class's `_der_packer`.
  * The context in which the `pack_recipe` occurs is always a list, and it
    is possible to substitute the respective part of that tuple with another
    value in-place; this means that future references to the same place in
    the code (which is part of the global data structure) will henceforth be
    the resolved `_der_packer` form.


## Internal Data Storage

Internally, we make a point of sharing the binary data after it has been
unpacked; in terms of the C version of Quick DER, these are the so-called
arrays of `dercursor` structures.  We represent those arrays with Python
lists, because those allow us to manipulate their contents without changing
the shared nature of the list.  Given a class, the number of elements in
the list are fixated.

To achieve maximum sharing, the `ASN1Object` subclasses store the following
information in each instance:

  * `_bindata` is a list of binary strings holding basic typing information
  * `_offset` is the offset in the `_bindata` where this particular object
    starts

Any given type covers a given number of entries in the `_bindata`, and thanks
to the `_offset` we know where it starts.  Any references into `_bindata` are
made relative to the `_offset`, so as to allow a complex type to be stored
in it.

The general procedure in finding this format is as follows:

 1. The user calls a type constructor with a `derblob` parameter
 2. The type holds a `_der_packer` instruction for packing and unpacking such
    `derblob` values; this is used to derive the `_bindata` for the initial
    type, together with `_offset` 0
 3. The type holds a `_recipe` that describes how the `_bindata` is to be
    turned into instance data; this may involve creating other instances that
    are subclassed off `ASN1Object`

In general, the `_recipe` attempts to construct named types whenever
possible.  This is often possible because fields often refer to an ASN.1
type name rather than an on-the-spot definition.  The result is that the
user of the Python instance can get more information about the data types.


## Internal Calling Conventions for Generated Python Code

The Python code generated by `asn2quickder` defines classes with a
`_der_packer`, `_recipe` and `_numcursori`, and it has `__init__` functions
that will immediately go from a `derblob` to a `_bindata` and `_offset`, which
is exclusively used for internal instantiation calls.  Even the
`ASN1Atom`, `ASN1SequenceOf` and `ASN1SetOf` will be setup with a
reference to a `_bindata` and `_offset`, so they can modify the actual data
that came out of `der_unpack()` and that goes into `der_pack()`.

Empty instances of type-named classes are formed by creating the number of
`_bindata` elements that are needed for the type, and these are then filled
with `None` to indicate no data has been assigned to the various fields
and indexes yet, and the `_offset` is set to 0 for the outermost instance.
The complete structure is then built as would be done after unpacking a
DER blob.  When an `ASN1SequenceOf` or `ASN1SetOf` is constructed, it will
be setup as though it had been supplied with an empty DER blob, so they
will form an empty list and an empty set respectively, but they will
also be filled with the type information that they need.

And this brings us to a final point about the use of anonymous classes,
so the ones that do not follow an ASN.1 type name.  Such classes need
to be initialised with a `_der_packer`, `_recipe` and `_numcursori`,
and that calls for extra parameters supplied to their `__init__` function,
named `der_packer`, `recipe` and `numcursori`.  These values are considered
readonly, just like the corresponding static class elements, thus allowing
for sharing and thereby offloading of memory and the garbage collector.
To accommodate that, the compiler `asn2quickder` does what it can to
generate structures that can be shared.


# Calling Conventions for the Python Code Generator

The Python code that generates code is the `asn2quickder` compiler, which
itself is written in Python.  Its task is to map an ASN.1 specification
into code in C header files and in Python; it currently does both mappings
in one call, but may in future releases take a language parameter, probably
like Swig does it, with a language selector flag `--c` or `--python`.

The intention is to create type-named classes as much as possible, because
this improves the preparedness of the individual classes as well as the
ability to reflect on the data structures, both while debugging data and
having code work on it.  This means that type descriptions are not generated
on the fly, but that a recipe for them is returned by the various type
description structures in the semantical framework of `asn2quickder`.

The structure for a type recipe is simple enough, it is a tuple of the form

    `(packer, recipe)`

in addition there is a counter `cursor_offset` that increments for every
`dercursor` that is generated, and upon return from a type evaluation its
value indicates the `numcursori` value.

  * We used to pass a `typname` with a string for the intermediate class from
    `quick_der.api`, until we realised that this could be derived from `recipe`
    as one of `ASN1StructuredType`, `ASN1SequenceOf`, `ASN1SetOf`, `ASN1Atom`.
    It is either used to construct an anonymous type which is then supplied
    with the `der_packer`, `recipe` and `numcursori` parameters, or it can
    be used to construct a Python class named by an ASN.1 type assignment,
    whose field contain the `_der_cursor`, `_packer` and `_numcursori`
    values in a statically shared manner.

  * The `packer` is a list of strings, each holding a string with one or more
    `DER_xxx` constant names composed with a spaced `|` operator.  As an
    example, it could be `DER_PACK_STORE | DER_PACK_SEQUENCE`.  This form
    is nice to read and easy enough to map to a binary form.  Although a
    packer generally ends with `DER_PACK_END`, this instruction is added
    just before actually generating output, so as to simplify compisitions
    caused by nested invocations.

  * The `recipe` holds a structure for instantiation in a Python format.
    This is almost printed as-is, except that references to class names
    would not work, so they are represented as strings and must be modified
    rather than simply passed through `repr()`.

The generator, represented by the `self` object passed between the Python
functions that produce the aforementioned type descriptions, manages
information too:

  * The `cursor_offset` resets to 0 in a few cases.  First, for every reference
    to a named type.  This is not because a named type cannot be part of a
    larger whole, but because a new value for `_offset` can be supplied to a
    constructor, so that the offsets generated inside the type-named class
    can start from 0 and its code can be reused.  The second case for resetting
    the `cursor_offset` to 0 is for the creation of a sub-packer, such as is
    the case inside `SEQUENCE OF` and `SET OF` generation.  In these cases,
    there is a nested generation process which leads to an (anonymous or
    type-named) entry that will be used as the type for each repeated data
    element.  The complete binary code for the `SEQUENCE OF` or `SET OF`
    element is stored in one `dercursor` element by the outside packer, so
    after the sub-packer has been generated the old value of `cursor_offset`
    is used to assign an offset to the overall `dercursor` and the
    `cursor_offset` is incremented as it would have for an `INTEGER` or any
    of the `STRING` forms.

  * `nested_typerefs` and `nested_typecuts` are used to avoid infinite
    recursion while traversing type definitions.  This is possible because
    only a limited depth is required.  The `nested_typerefs` variable counts
    how many type-name references have been followed and this increments
    while diving deeper and decrements when returning.  Similarly,
    `nested_typecuts` may increase as `SEQUENCE OF` or `SET OF` elements
    are being nested.  Both of these discard some information that may be
    of use to the outer type that is being sought; when both nestings occur
    there is no added value for the outermost type that initiated the type
    traversal, and so infinite recursion can be halted as soon as both
    these variables become non-zero.  Note that this means that not all
    recursive structures can be mapped; this is a general restriction of
    Quick DER and may be remedied with explicit recursion markers in the
    future.

    One detail not immediately obvious to this scheme (at least to us) is
    that there is a sub-packer for elements of `SEQEUENCE OF` and `SET OF`
    structures, and this sub-packer requires full unwinding of even type
    references.  This means that `nested_typecuts` are only incremented
    when `nested_typerefs` has been.  We can do this easily by incrementing
    and decrementing the `nested_typecuts` value with `nested_typerefs`
    instead of `1`.  The two values are still needed, however: any nesting
    of `SEQUENCE OF` and `SET OF` can occur, and must have a complete
    sub-packer description, until one is encountered in a referenced type,
    which will be assumed to do its own unwinding.

    TODO: Given packer recipes in the sub-packer, we can just follow typerefs!

    TODO: Could generate a recipe everywhere, and fixate it in the compiler

When type descriptors are being generated, functions are called with a few
parameters.  These allow the recursive passing-down of information along
the semantical tree structures.  The functions behaving as described above
are called `pytypeXXX` and they are invoked thusly:

    (packer,recipe) = pytypeXXXX (self, node, impl_tag)

Where the parameters have the following meaning:

  * `self` is the generator object itself.  It contains some household methods
    and attributes, such as file names and generic output generation routines.
    It also contains the aforementioned generator variables.

  * `node` is a node in the semantical tree (which is the tree from `asn1ate`
    with some extensions made to facilitate `asn2quickder`).

  * `impl_tag` is optional; it is used to overrule a tag when `IMPLICIT TAGS`
    are in force, such as  `[0] SEQUENCE xxx` where the tag of `SEQUENCE`
    is replaced with the `[0]` tag.  This construct is used in grammars such
    as LDAP, but not by others like Kerberos.  When not set, all tags in the
    syntax are included.  When set, its value should be a string with the name
    of a `DER_TAG_xxx` constant, for example `DER_TAG_APPLICATION(0)` but not
    any associated `DER_PACK_ENTER` or `DER_PACK_STORE`, since that is the
    prerogative of the called method.


## Moving Towards a Framework

The Python code generator is the one with the best structure up to now.  The
framework for C was chiefly a code generator.  It is of considerable interest
to test the idea that the Python framework, with much more design and
explicit structure, might represent what is generally needed to generate
code for any language.

At some point, we hope to lift out the generic portions of a framework and
produce much smaller and simpler language-specific generators.  By that time,
it should be possible to support many more languages, because everything is
then far less ad-hoc.


