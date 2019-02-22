# Testing the packing and unpacking of primitive types.

import sys
# ../../python is (once this test is being run) the source-dir python,
#    ../python is inside the build-directory
sys.path = [ '../../python/installroot', '../python/installroot' ] + sys.path

from quick_der import api as qd

def hexily_d(n):
    """
    Support-function, produces one single \\xHH escape from a character.
    """
    s = hex(n).replace("0x", "")
    if len(s) < 2:
        return ("\\x0"+s)
    else:
        return ("\\x"+s)

def hexily(s):
    """
    Produces a repr-like string for @p s, only it uses hex escapes
    everywhere. This avoids some cases like 0xa1 failing on US-ASCII
    output.
    """
    return "".join([hexily_d(ord(x)) for x in f_v])

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
	(INT, 127),
	(INT, 128),  # Crossover from 7 to 8 bits
	(INT, 129),
	(INT, 128 + 32),  # another crossover, 0xa1 gives ascii-encode error
	(INT, 128 + 33),
	(INT, 254),  # Crossover from 8 to 9 bits
	(INT, 255),
	(INT, -255),
	(INT, 256),
	(INT, -256),
	(INT, 1337),
	(INT, -1337),
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
    r_fv = repr(f_v)
    try:
        print("f(V)="  + r_fv)
    except UnicodeEncodeError as e:
        print("f(V)='" + hexily(f_v) +"' (*)")
    print("pf(V)=" + repr(pf_v))
    assert parse_func(format_func(value)) == value, "Value " + str (value) + " :: " + str (typename) + " is not properly reproduced by parse . format"

    print(" .. OK")
