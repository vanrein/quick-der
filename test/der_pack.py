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
	(BIT, set([1,5,7])),
	(BIT, set()),
	(BIT, set([22])),
	(BIT, set([100, 101])),
	(STR, "cow"),
	(STR, ""),
	(STR, chr(0) + "cow"),
	(STR, None),  # TODO: is a non-string distinguishable from an empty one?
	(OID, "1.2.3.4"),
	(OID, "3.14.159.2653.58979.323812"),
	):
	pack_func = getattr(qd, "der_pack_" + typename)
	unpack_func = getattr(qd, "der_unpack_" + typename)

	assert pack_func is not None
	assert unpack_func is not None
	assert callable(pack_func)
	assert callable(unpack_func)

	assert unpack_func(pack_func(value)) == value
