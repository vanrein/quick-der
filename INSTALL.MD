# Installing Quick DER

<img alt="Quick DER logo" src="quick-der-logo.png" style="float: right;"/>

The basic installation that provides you with the library:

    ./configure
    #OPTIONAL# make mount
    make all
    make install

Other customary build targets include `clean`, `uninstall`.

There is an additional build target `mount` that will incorporate two
other GIT repositories, and use them during building and installing.
The result will be additional resources:

  * A utility `derdump` that is dumps even *wrongly formatted* DER-encoded
    data.  This is extremely useful to ASN.1 developers, and there does not
    seem to be a comparable tool anywhere else (?)

  * Include files based on standards, such as RFCs.  The intention is to have
    a growing set of standards-based include files that can readily be included
    into a DER project for analysis with Quick-DER.

Note that after `make mount` you may need extra facilities to be able to run
the [asn2quickder](https://github.com/vanrein/asn2quickder) submodule.
Specifically, it relies on [pyparsing](https://pypi.python.org/pypi/pyparsing).

