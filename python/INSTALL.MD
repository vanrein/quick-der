# Installation

The Quick DER Python tools can be built using the standard `setup.py`
procedure. These tools must be built and installed **after** the library
is built, and installed to the same prefix. Without the tools. it is
not possible to use the `MacroASN1Module` or to generate Python
bindings for ASN1 descriptions.

Quick DER needs  a recent release of [asn1ate](https://pypi.python.org/pypi/asn1ate/).
You may need to install the Quick DER Python module using pip and forcing it to
process dependency links:

```
$ pip install --process-dependency-links .
```

## Manual Build

Use the same *PREFIX* as used for building and installing the Quick DER library.
Ensure that *PYTHONPATH* is set correctly to allow installing to that prefix.

```
python setup.py build
python setup.py install --prefix=$PREFIX
```

