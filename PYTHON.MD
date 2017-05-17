# Embedding Quick DER into Python

<img alt="Quick DER logo" src="quick-der-logo.png" style="float: right;"/>

> *This description explains how Quick DER is mapped into Python.
> The design is made to facilitate similar structural traversals in
> Python as in C, albeit through a different mechanism.  Much like
> the C headers, the structures are generated and placed into modules
> that are delivered along with Quick DER for Python.*


## General Description

The implementation of Quick DER in Python centers around classes that
encapsulate the logic of various ASN.1 objects.  Constructed types such
as `CHOICE`, `SEQUENCE` and `SET` have named fields, which map to attributes
that can be addressed directly by adding `.fielfname` to the instance.

Although in C we need to explicitly traverse `SEQUENCE OF` and `SET OF`
on account of their variable-sized structures, this has been encapsulated
into the Python API, and such structures show up as either a list or a
set that can be manipulated as is normal under Python.

ASN.1 objects typed by `ANY` are left as they are, and provided as a
(binary) Python string, holding the header and contents.  You can use
it in any way you like, but if you know the class, you can instantiate
it as though you received the data over a protocol.

It is possible to create custom classes, by setting up the right internal
variables in a subclass or instance of `ASN1Object`, but this is not for
the faint of heart; there are ways of crashing the program in the current
system.  The same risk does not occur with generated include files.  So,
the best way to create handlers for custom structures is by mapping a
custom ASN.1 specification through the `asn2quickder` compiler.

Building DER is the reverse process, and it can follow the same process.


## Using the Generated Classes

The package for Quick DER is `quick_der`.  It provides a function
`der_unpack()` which expects a class (that must be a subclass of `ASN1Object`)
and a Python string holding the byte sequence to decode.  It will return
an instance of the given class, with all the pleasantries of using it.

Given such an instance, entries in it can be manipulated as expected.  It
should be noted that the data in each output of `der_unpack()` is shared,
meaning that you could traverse to an object within the parsed structure,
change it, and then repack the overall structure, to find the changes made
in the embedded object.  If this is not what you need, you should `clone()`
the respective object.

Any `ASN1Object` may be turned into DER bytes through its `_der_pack()`
method (not an ASN.1 name) or the packages `der_pack()` function.  This
uses the information stored in the object to find the format for packing.
In general, using Quick DER under Python means that you are using classes,
not packer descriptions such as in C.  It marks the differences between
the languages.

In case you are wondering why the package `quick_der` explicitly mentions
DER again in `der_pack()` and `der_unpack()` functions: we can see ways
of expanding this approach with encodings for BER, XER, one of the JER
encodings, PER, CER and so on.  This might work through multiple inheritance
of the objects, that could incorporate a possible future Quick XER module,
and so on.  Factories may do this appropriately for your platform.  One day,
who knows!


## Example Code

Kerberos is completely defined in terms of ASN.1, so it serves as a good
example.  Instead of the binary transmission format that defies manipulation
and perhaps even reading of parts, we can turn it into a Python object, work
on it and generate the binary transmission format when the need arises.

The `asn2quickder` compiler produces Python packages for many specifications,
ready to be loaded as modules.  For example, a Kerberos Ticket is defined
by the name `Ticket` in RFC 4120, so it can be reached under
`quick_der.rfc4120.Ticket` and used just like a custom class that would
implement a Kerberos Ticket:

    from quick_der.rfc4120 import Ticket

    def show_ticket (der):
            """Access individual parts of the Ticket, and print them.
               Then compose the owner's name from its constituent parts.
            """
            tkt = Ticket (der)
            print 'Ticket for Realm', tkt.realm
            print '       has name-type', tkt.sname.name_type
            for nm in tkt.sname.name_string:
                    print '       has name-string component', nm
            owner = '/'.join (tkt.sname.name_string) + '@' + tkt.realm
            print 'In short, it is for', owner

    def rebase_ticket (der, newrealm):
            """This violates RFC 4120, but is still a nice demo of modifying
               DER data in Python.  The violation is caused by the mismatch
               of the realm with the encrypted copy in tkt.enc_part
            """
            tkt = Ticket (der)
            tkt.realm = newrealm
            return tkt._der_pack ()

