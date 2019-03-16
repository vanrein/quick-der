# Support for the JSON Encoding Rules

> *ITU has released X.697 as the standard encoding of ASN.1 data
> in JSON structures.  This means that the powerful structuring
> facilities of ASN.1 can now be aligned with easy-to-use JSON
> encoding.  We describe how Quick DER adopts this too.*

The specification of the JSON Encoding Rules, or JER for short,
results in intuitive JSON structures.  Where the default mapping
does not seem right, it is possible to annotate the ASN.1 schema
with mapping instructions.

An example output from JER might be:

```
{
   "name" : {
      "givenName"  : "John",
      "initial"    : "P",
      "familyName" : "Smith"
   },
   "title" : "Director",
   "number" : 51,
   "dateOfHire" : "19710917",
   "nameOfSpouse" : {
      "givenName"  : "Mary",
      "initial"    : "T",
      "familyName" : "Smith"
   },
   "children" : [
      {
         "name" : {
            "givenName"  : "Ralph",
            "initial"    : "T",
            "familyName" : "Smith"
         },
         "dateOfBirth" : "19571111"
      }, {
         "name" : {
            "givenName"  : "Susan",
            "initial"    : "B",
            "familyName" : "Jones"
         },
         "dateOfBirth" : "19590717"
      }
   ]
}
```

This could be an instance of the following ASN.1 structure:

```
PersonnelRecord ::= SET {
   name         Name,
   title        VisibleString,
   number       EmployeeNumber,
   dateOfHire   Date,
   nameOfSpouse Name,
   children     SEQUENCE OF ChildInformation DEFAULT {}
}

ChildInformation ::= SET {
   name         Name,
   dateOfBirth  Date
}

Name ::= SEQUENCE {
   givenName    VisibleString,
   initial      VisibleString,
   familyName   VisibleString
}

EmployeeNumber ::= INTEGER

Date ::= VisibleString -- YYYYMMDD
```

The trick of ASN.1 is that it can express the subtleties of many
protocols in a manner that is independent of the encoding, so it
would be just as easy to design binary encodings such as DER as
it is to express for JER.  Each has its own purposes -- JSON is
useful in a web environment, but DER is much easier to sign
digitally.


## About the X.697 encoding

Some constructions can have multiple encodings.  This can be
selected with explicit annotations in the ASN.1 grammar, such
as `[OBJECT]` to represent a `SET OF SomeType` not as an
array, which is the default, but as a JSON object.

The encoding holds a number of subtleties, and these make it
very clear why it is useful to have the schema to learn about
possible variations.  A `REAL` type for instance, may show up
in JSON as `3.14` or as strings for special values, like
`"NaN"` or `"-0"`, both of which are part of the IEEE standards
that are built into most our software.

Among the really powerful ideas of ASN.1 is that it details
what kinds of strings we are using.  An `IA5String` holds just
ASCII characters, a `UTF8String` holds UTF-8 encoding and
an `OCTET STRING` can hold arbitrary binary content.  The
`IA5String` and `UTF8String` formats map directly to a JSON
string, whereas an `OCTET STRING` is encoded to a string that
holds either in hexadecimal or, given a `[BASE64]` annotation,
base-64 notation.  It is very useful that such things follow
directly from the choice of the schema.

DER is canonical, meaning that the same value is always
represented in the same manner, but JER is not.  This is not
a problem; BER is not canonical either.  It leaves more
freedom to the programmer, but canonical forms are really
helpful to keep digital signing simple and secure.  The
classical counter-example is XML DSIG, which is pretty much
a security nightmare and is very, very easy to mess up.

Another difference with DER is that JSON is centered around
the labels that also occur in the ASN.1 syntax, whereas a
DER encoding focusses on tagging.  A good example is this
ASN.1 fragment:

```
Feedback ::= CHOICE {
   friendly   [0] UTF8String,
   bitching   [1] UTF8String
}
```

Had it not been for the contextual tags `[0]` and `[1]` that
end up in the binary encoding of DER, then it would have been
impossible to distinguish two strings that are both encoded
in a `UTF8String`.  In JER, the difference can be made with a
label `friendly` or `bitching`.  A bit more verbose, and a
lot more readable.  It is a good demonstration of the useful
generic nature of ASN.1.


## Quick DER can also be Quick JER

The name Quick DER stems from the original encoding that
was supported, DER.  It contains a lot of generic ASN.1
processing knowledge, and could easily incorporate JSON
as an extension.  This would bring the power of ASN.1 to
the JSON world.

Quick DER considers ASN.1 schema types as a sequence of
variables, some of which may not be filled (if they are
`OPTIONAL`, have a `DEFAULT` or are part of a `CHOICE`
structure that was not selected).  This logic can be
used for parsed JER data.

Parsing JER into a structure comes down to taking apart
the JSON content and interpreting its structure in the
data structures being built.  This is not so different
from what DER does.  JER processes a stream of tokens
such as a left square bracket, a colon or a string;
DER processes a stream of tags with a length to infer
structure.

Quick DER already maps variable names to ones that are
usable in the embedding langauge; that usually means
that dashes in ASN.1 names are mapped to underscores.
This is not specific to DER or JER, but a general
aspect of ASN.1 handling.


## Adding JER to Quick DER for Python

A relatively simple `quick_der.json` module can be added
to the Python implementation.  It would provide iterators
for tokens in the JSON stream, drawn from a file, string or
Python/JSON object.  The iterator would return slices from
the input string where possible, so as to be memory efficient.

The iterator object probably needs to support peeking ahead
at the next token, without consuming it.  And it would be
a useful place to raise syntax errors, as these can then be
annotated with a location in the input and some context.

A parser would be an iterator that creates classes for the
various ASN.1 types and invokes local interpreters for
the token stream drawn from JSON.  This effectively becomes
a distributed parser, or one built into the various
classes produced by Quick DER.  Most of the logic will be
generic however, and varied only by such things as field
names, which are already incorporated into Quick DER
classes.  The recipes already incorporated into each class
should help to know where to store a value.

Numeric values can be interpreted as normal Python values.
They might be mapped to DER notation if so desired, notably
when producing DER out of former JER content.

Escaping in strings must be undone before Python can process
content, and the resulting strings are the actual data, which
happens to be the normal case in DER.  Therefore, it is a
useful idea to remove escapes upon first encountering them
in the JER token stream, and store the result in the same
location and format as would be used for DER.

Complex structures are mapped out to Python already, and
can be done in just the same way for JER as for DER.

To conclude, it seems that:

  * JER is relatively easy to add to Quick DER
  * Quick DER adds sufficient value to JSON to be useful
  * DER plus JER is only a little more than DER or JER alone


## Adding JER to Quick DER for C

When linked statically, the Quick DER lirbary adds only
those functions that are used, and this results in a very
small footprint.  The same principle can be used when
JER is added.  In C, it is easy to ensure that we have no
more than we really need, in service of embedded/small
environments.

The addition needed would be a tokenizer (in the style of
Lex or Ragel) and another byte code format.  This format
however, can follow a similar logic to Quick DER's, where
the composition is through `#define` lines that can be
included without adding to the code.

The byte code cannot as direct a match with the encoded
data as in DER.  The same JER constructions appear in
many data types, and data types such as `REAL` have more
than one JER encoding.  Finally, encoding instructions
diversify the set of mappings between data and byte code.

Another aspect to complicate a parser is that strings,
not single-byte tags lead the analysis.  Some form of
a dictionary must therefore be supplied in the bytecode,
even if it is as simple as a minimal perfect hash (to
avoid string references into a shared symbol table,
perhaps at the expense of complete labelling scrutiny).
Compaction may not seem important for JSON, but it can
be useful for the trend towards an internet of things.

We may find that the simple model of byte code concatenation
that worked for DER does not apply to JER.  We will have
to be creative to solve that while keeping it simple.

