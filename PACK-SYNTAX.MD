# Syntax for Packing Paths

![Quick DER logo](quick-der-logo.png)

This specification describes the path format used by `der_unpack()` and
`der_pack()` to pass through a DER binary and map it to (or from) an array
of `dercursor` values.

A simpler variation of a similar idea is the
[WALK SYNTAX](WALK-SYNTAX.MD),
which limits itself to finding a single element, but also based on a
(different) walking path expression.

## Declaring and Using a Walking Path

The walk path is described as a sequence of values that ends in `DER_PACK_END`:

    #include <quick-der/api.h>

    derwalk path_demo [] = {
            ...,
            DER_PACK_END
    }

which is then used to unpack the DER binary data under a `dercursor crs` with

    int prsok;
    prsok = der_unpack (&crs, path_demo, outputs, 1);

The `outputs` is an array of `dercursor` that will be filled with information
found in the `path_demo`.  Explicit storage instructions will put the information
there, so the required size of the array is equal to the fixed number of such
instructions in `path_demo`.

## Diving in Head-First

The path described by `path_demo` should be a depth-first traversal of a
*static* structure.  That means that `SEQUENCE OF` and `SET OF`, the two ways
of expressing dynamically sized structures in ASN.1, require special handling.

To dive in, use a flag `DER_PACK_ENTER` and to leave a nested structure, use
the `DER_PACK_LEAVE` flag.  To store intermediate values, use `DER_PACK_STORE`
as a flag, as in

    derwalk path_demo [] = {
            DER_PACK_ENTER | ...,
            DER_PACK_STORE | ...,
            ...,
            DER_PACK_LEAVE,
            DER_PACK_END
    }

Note that `DER_PACK_LEAVE` is an instruction on its own.  The other two
forms are extended with a tag that is verified to match, for instance

    derwalk path_demo [] = {
            DER_PACK_ENTER | DER_TAG_SEQUENCE,
            DER_PACK_ENTER | DER_TAG_CONTEXT (0),
            DER_PACK_STORE | DER_TAG_INTEGER,
            DER_PACK_LEAVE,
            DER_PACK_STORE | DER_TAG_OCTETSTRING,
            DER_PACK_LEAVE,
            DER_PACK_END
    }

An example ASN.1 structure that could be traversed by this would be

    demoStruct ::= SEQUENCE {
            demoCounter [0] INTEGER,
            demoName OCTET STRING
    }

After invoking `der_unpack()` on this path, there are two values in the `output`
array of `dercursor`, namely for the two `DER_PACK_STORE` instructions.  From the
following input data

    30 16                                -- tag SEQUENCE, length 16
       a0 03                             -- tag a0 for [0], length 3
          02 01 07                       -- tag INTEGER, length 1, value 7
       04 09 51 75 69 63 6b 20 44 45 52  -- tag 4, length 9, "Quick DER"

this would make `output[0]` point to the `INTEGER` value 7, with 1 byte length,
and `output[1]` would point to the `OCTETSTRING` contents "Quick DER", with a
length of 9 bytes.

Note how nothing remains of the DER tags or lengths.  This is what you should
expect from a Quick and Easy DER parser.

## Dealing with Variable Structures

It is possible to not store everything we encounter.  In the previous situation
we might have used

    derwalk path_demo [] = {
            DER_PACK_ENTER | DER_TAG_SEQUENCE,
            DER_PACK_STORE | DER_TAG_CONTEXT (0),
            DER_PACK_STORE | DER_TAG_OCTETSTRING,
            DER_PACK_LEAVE,
            DER_PACK_END
    }

to find `output[0]` set to the DER sequence *contained in* `[0] INTEGER`,
which means the `INTEGER` in DER coding, so in hex
the bytes `02 01 07` instead of just to `07`.  This can be useful at
some times.

Imagine the ASN.1 structure

    aFewPrimes ::= SET OF INTEGER

which is a `SET OF` and can thus contain as many `INTEGER` values as desired.
An example hexdump of a DER value listing the first 5 primes would be

    31 0f        -- SET, containing 15 bytes
       02 01 02  -- INTEGER 2
       02 01 03  -- INTEGER 3
       02 01 05  -- INTEGER 5
       02 01 07  -- INTEGER 7
       02 01 0b  -- INTEGER 11

If we had to store each `INTEGER` in a separate `output[]` entry, we would need
a variable-sized output array.  What `der_unpack()` does in these cases is the
same as demonstrated for `[0] INTEGER` above; it stores the entire structure
*contained inside* the `SET OF` and leaves it for further processing.

The path expression to store this set would be

    derwalk path_primes [] = {
            DER_PACK_STORE | DER_TAG_SET_OF,
            DER_PACK_END
    }

The result would be stored in `output[0]` as the sequence `02 01 02` and so on,
of length 15.  It is now possible to do a few things:

  * use `der_iterate_first()` and `der_iterate_next()` to find the individual
    values in the set;
  * manually skip through the list with `der_skip()` until it hits the end of
    the set;
  * counting the entries with `der_countelements()` and then allocate an array
    `dercursor primal[4]`, in the heap or on the stack, and pass it into
    `der_unpack ()` with the last parameter set to the count of 4.


## Optionals, Choices and the ANYs

Not everything declared in ASN.1 is included in the binary DER format.
Some parts are `OPTIONAL` (and may have a `DEFAULT`, which Quick DER does not
capture) and others are a `CHOICE` from variants.

To encode an option, prefix `DER_PACK_OPTIONAL,` to the optional part.  If the
optional part is flagged wth `DER_PACK_ENTER`, then the optionality will
continue to the corresponding `DER_PACK_LEAVE`.  Note that ASN.1 ensures that
the DER format can always be parsed based on a singly tag lookahead, which we
exploit in this case.

A somewhat similar structure is the `CHOICE` which permits choosing a syntax
variety from among alternatives.  Again, ASN.1 ensures that parsing can be done
based on the first tag.  We use this once more, for paths between
`DER_PACK_CHOICE_BEGIN` and `DER_PACK_CHOICE_END`.  Note that the programmer
of the walking path is responsible for proper nesting, also with respect to
`ENTER`/`LEAVE` structure.

Finally, the forms `ANY` and `ANY DEFINED BY` are used in ASN.1 to describe
wildcard typing.  These have no representation in DER either, but at the
point where it comes across the `DER_PACK_STORE | DER_PACK_ANY` instruction,
it will match anything, and store the result in the output array of
`dercursor`.  The stored result is special however, in that it includes the
entire DER structure including tag and length bytes.  This is because you
will have to do further processing.


## Overlay structures

The idea of static structure is a great benefit to us as programmers, because
we can create overlay structures that consist solely of `dercursor` and other
overlay structures.  These give us a way to navigate through the data using
ASN.1 labels.

The first ASN.1 structure

    demoStruct ::= SEQUENCE {
            demoCounter [0] INTEGER,
            demoName OCTET STRING
    }

could be overlaid with the C structure

    typedef struct {
            dercursor demoCounter;
            dercursor demoName;
    } ovly_demoStruct;

and the program could declare

    ovly_demoStruct output;

and pass that to `der_unpack()` as `(dercursor *) &output` for type correctness.

The datafields could then be addressed with something like

    printf ("Found \"%.*s\"\n", output.demoName.derlen, output.demoName.derptr);


## Repacking

There is a function `der_pack()` that does the exact opposite of `der_unpack()`,
using the same walking paths.

*Something to ignore until you run into trouble:*
You may need to `der_prepack()` first if you have nested elements that are not
a `SET (OF)` or `SEQUENCE (OF)` or other form that is always Constructed.
Without `der_prepack()` your DER representation may end up being Primitive.


## ASN.1 Compiler and RFC Library

The intention is to generate this syntax automatically from ASN.1 files, including
the overlay structures.  The result would be a headerfile that provides macros
that can fill paths, and structures that capture the structure of ASN.1 and
specifically the labels used.

Once we have a compiler, it is our intent to collect the RFCs and perhaps
other specifications that use ASN.1 syntax, and to derive their header files
for distribution in the developer version of Quick and Easy DER.

These things combined should enable you to specify things like

    #include <quick-der/api.h>
    #include <quick-der/rfc5280.h>

    typedef rfc5280_Certificate_ovly Certificate;
    derwalk path_cert [] = { rfc5280_Certificate_PACK, DER_PACK_END };

    void print (dercursor *input) {
            Certificate crt;
            if (der_unpack (&input, path_cert, (dercursor *) &crt, 1) == 0) {
                    ...crt.tbsCertificate.issuer...
            }
    }

In short, you will be up and running with DER-encoded PKIX Certificates.

And it will be

Quick... and Easy!
