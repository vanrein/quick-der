# Syntax for Walking Paths

<img alt="Quick DER logo" src="quick-der-logo.png" style="float: right;"/>

> This specification describes how to make `der_walk()` traverse the path in DER
> binaries that you intend it to take.

A *walking path* is a sequence of instructions for the function
`der_walk()`, which controls how that functions modifies a cursor
to point to an element within the data that the cursor originally
points to. A walking path may be considered a program in a very small
domain-specific language. See also the
[PACK SYNTAX](PACK-SYNTAX.MD)
for the similar, but somewhat more complex, packing paths.

A single walking path can replace dozens of lines of explicit function calls
to manipulate a cursor.

## Declaring and Using a Walking Path

The walk path is described as a sequence of values that ends in `DER_WALK_END`.
Here, `path_demo` is such a sequence. It is declared `static const` so that it
may be placed in read-only memory, but that is not required.

    #include <quick-der/api.h>

    static const derwalk path_demo [] = {
            ...,
            DER_WALK_END
    }

which is then used to move a `dercursor crs` with

    int prsok;
    prsok = der_walk (&crs, path_demo);

The return value from `der_walk()` is -1 for hard errors, 0 for success,
or a positive integer for partial errors.  If it fails to parse the path at
some point, the return value is a positive  integer, indicating how much of
`path_demo` was left unprocessed before `DER_WALK_END`.

The `crs` value is updated by this call to point to the end of the `path_demo`
walk.

## Entering and Skipping

There are two basic actions that `der_walk()` takes at each position along the
path; it may either enter or skip a DER element.  This is defined in the path
with `DER_WALK_ENTER` and `DER_WALK_SKIP`, respectively, as in

    static const derwalk path_demo [] = {
            DER_WALK_ENTER | ...,
            DER_WALK_SKIP  | ...,
            ...,
            DER_WALK_END
    }

## Matching tags

The tag found in the DER code must be matched, or otherwise a validation error
is raised (and a positive integer returned from `der_walk()` to indicate where
the problem was encountered).

Tags are quite simply matched by mentioning them after the enter-or-skip choice,
as in

    derwalk path_demo [] = {
            DER_WALK_ENTER | DER_TAG_SEQUENCE,
            DER_WALK_SKIP  | DER_TAG_CONTEXT (0),
            DER_WALK_ENTER | DER_TAG_OCTETSTRING,
            DER_WALK_END
    }

The two statements shown could be used to get to the `OCTET STRING` in

    demoStruct ::= SEQUENCE {
            demoCounter [0] INTEGER,
            demoName OCTET STRING
    }

This relates to the DER sequence for this structure; let's say the `INTEGER`
value is `7` and the `OCTET STRING` is `Quick DER`, then the encoding would be

    30 16                                -- tag SEQUENCE, length 16
       a0 03                             -- tag a0 for [0], length 3
          02 01 07                       -- tag INTEGER, length 1, value 7
       04 09 51 75 69 63 6b 20 44 45 52  -- tag 4, length 9, "Quick DER"

From the start of this structure, we need to:

  * Enter the `SEQUENCE`
  * Skip the `[0]` rather then entering it
  * Enter the `OCTET STRING`
  * Stop processing

This is precisely what the path walk describes.  Although *some* understanding
of the mapping to DER is helpful, you can generally derive the path to walk
directly from the ASN.1 structure.

When done, `der_walk()` returns 0, and `crs.derptr` is set so that it
points to the octet string "Quick DER", while `crs.derlen` is set to 9,
and you can continue to process the cursor:

    printf ("Found \"%.*s\"\n", crs.derlen, crs.derptr);


## Optionals, Choices and the ANYs

There is a possibility in ASN.1 to specify an element as `OPTIONAL`, perhaps
even having a `DEFAULT` value (which is ignored by Quick DER).  To mark an
entry as optional, precede it with `DER_WALK_OPTIONAL`.

Choices are barely interesting during a walk; in fact, the only purpose they
serve is as something to skip over (since we obviously have no idea how to get
into a structure if we don't know yet what that structure is like).  So,
specify `DER_WALK_SKIP | DER_WALK_CHOICE` to skip an arbitrary element;
there will be no validation of that particular tag.

The forms `ANY` and `ANY DEFINED BY` receive the same treatment as `CHOICE`,
but can be declared with a separate symbol `DER_WALK_ANY`.


## There is more

Also have a look at the individual steps that can be taken with
`der_enter()` and `der_skip()`.  And take a look at
`der_iterate_first()` and `der_iterate_next()` if you need iterators.

Where `der_walk()` is ideally suited to retrieve a single bit of information
from the repository, the `der_unpack()` routine can unpack a complete DER
structure (only deferring dynamically-sized parts to later calls).  The latter
also has a reverse routine `der_pack()`.  You will want to read the
[PACK SYNTAX](PACK-SYNTAX.MD) for the walking paths used with those routines.

