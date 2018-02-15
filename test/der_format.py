# Testing the packing and unpacking of primitive types.

import sys
# ../../python is (once this test is being run) the source-dir python,
#    ../python is inside the build-directory
sys.path = [ '../../python/installroot', '../python/installroot' ] + sys.path

from quick_der import api as qd

# Names of types, which have corresponding der_pack_<name> functions
# in the Quick-DER API.
INT = "INTEGER"
BOOL = "BOOLEAN"
BIT = "BITSTRING"
STR = "STRING"
OID = "OID"

for typename, value in (
	(INT, 0),
	(INT, 100),
	(INT, -101),
	(INT, 2**31-1),
	(INT, 2**32+1),
	(BOOL, True),
	(BOOL, False),
	(BOOL, 0),
	(BOOL, 1),
	(BIT, 162),
	(BIT, 0),
	(BIT, 4194304),
	(BIT, 3802951800684688204490109616128),
	(STR, "cow"),
	(STR, ""),
	(STR, chr(0) + "cow"),
	(STR, None),  # TODO: is a non-string distinguishable from an empty one?
	(OID, "1.2.3.4"),
	(OID, "3.14.159.2653.58979.323812"),
	):
    format_func = getattr(qd, "der_format_" + typename)
    parse_func = getattr(qd, "der_parse_" + typename)

    assert format_func is not None, "No der_format_" + typename + " found."
    assert parse_func is not None, "No der_parse_" + typename + " found."
    assert callable(format_func), "No callable der_format_" + typename + " found."
    assert callable(parse_func), "No callable der_parse_" + typename + " found."

    print("T=" + str(typename))
    print("V=" + repr(value))
    f_v = format_func(value)
    pf_v = parse_func(f_v)
    print("f(V)="  + repr(f_v))
    print("pf(V)=" + repr(pf_v))
    assert parse_func(format_func(value)) == value, "Value " + str (value) + " :: " + str (typename) + " is not properly reproduced by parse . format"

    print(" .. OK")
