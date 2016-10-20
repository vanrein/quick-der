# Installing Quick DER

<img alt="Quick DER logo" src="quick-der-logo.png" style="float: right;"/>

The basic installation that provides you with the library:

    ./configure
    make all
    make install

Other customary build targets include `clean`, `uninstall`.

There a few additional utilities that you may need to use alongside
Quick DER.

  * Include files based on standards, such as RFCs.  The intention is to have
    a growing set of standards-based include files that can readily be included
    into a DER project for analysis with Quick-DER.  To build those, there
    is a need to have the library `asn1ate` installed while building
    Quick DER.
    You can find the tool in the
    [asn1ate](https://github.com/kimgr/asn1ate)
    webpage.
    This tool relies on [pyparsing](https://pypi.python.org/pypi/pyparsing).
    Note that `asn2quickder` is "good enough" for the mapping of at least
    an important part of the RFCs, but it is work that can still be improved.

  * A utility `derdump` that is dumps even *wrongly formatted* DER-encoded
    data.  This is extremely useful to ASN.1 developers, and there does not
    seem to be a comparable tool anywhere else (?)
    You can find the tool in the [hexio](https://github.com/vanrein/hexio)
    which is suggested as a co-install for Quick DER.


