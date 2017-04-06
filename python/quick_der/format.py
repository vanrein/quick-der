# format.py -- Taking the turn from DER to native, format as DER
#
# Terminology:
#   * der_pack() and der_unpack() work against a _der_packer syntax
#   * der_format() and der_parse() only look at the body (and needs hints)
#
# For primitive operations, such as on INTEGER and BOOLEAN, see primitive.py


import time

import classes   as c
import primitive as p
import packstx   as t

import _quickder


#
# Various mappings from hint names (with some aliases) to a packer function
#

# Report an error, stating that a hint is required for the map at hand
def _hintmap_needs_hint (value):
	raise Exception ('To pack ' + str(type(value)) + ', please provide a hint')

_hintmap_int = {
	'no_hint': (t.DER_TAG_INTEGER, p.der_format_INTEGER),
	'INTEGER': (t.DER_TAG_INTEGER, p.der_format_INTEGER),
	'BITSTRING': (t.DER_TAG_BITSTRING, p.der_format_BITSTRING),
}

_hintmap_unicode = {
	'no_hint': (None, _hintmap_needs_hint),
	'UTF8': (t.DER_TAG_UTF8STRING, p.der_format_STRING),
	'OCTET': (t.DER_TAG_OCTETSTRING, p.der_format_STRING),
	'GENERALIZED': (t.DER_TAG_GENERALSTRING, p.der_format_STRING),
	'GENERAL': (t.DER_TAG_GENERALSTRING, p.der_format_STRING),
}

_hintmap_str = {
	'no_hint': (None, _hintmap_needs_hint),
	'IA5': (t.DER_TAG_IA5STRING, p.der_format_STRING),
	'ASCII': (t.DER_TAG_IA5STRING, p.der_format_STRING),
	'OCTET': (t.DER_TAG_OCTETSTRING, p.der_format_STRING),
	'GENERALIZED': (t.DER_TAG_GENERALSTRING, p.der_format_STRING),
	'GENERAL': (t.DER_TAG_GENERALSTRING, p.der_format_STRING),
	'PRINTABLE': (t.DER_TAG_PRINTABLESTRING, p.der_format_STRING),
	'OID': (t.DER_TAG_OID, p.der_format_OID),
	'RELATIVE_OID': (t.DER_TAG_RELATIVEOID, p.der_format_RELATIVE_OID),
	'RELATIVEOID': (t.DER_TAG_RELATIVEOID, p.der_format_RELATIVE_OID),
}

_hintmap_time = {
	'no_hint': (t.DER_TAG_GENERALIZEDTIME, p.der_format_GENERALIZEDTIME),
	'GENERAL': (t.DER_TAG_GENERALIZEDTIME, p.der_format_GENERALIZEDTIME),
	'GENERALIZED': (t.DER_TAG_GENERALIZEDTIME, p.der_format_GENERALIZEDTIME),
	'UTC': (t.DER_TAG_UTCTIME, p.der_format_UTCTIME),
	'GMT': (t.DER_TAG_UTCTIME, p.der_format_UTCTIME),
}


###TODO### hintmaps' (a,b) have tag a implies formatter b, use b = a2b [a] ???
###TODO### that also delivers the parser c, through c = a2c [a]


# Based on a value's type and a possible added hint, find a pair of
#  - a value packing function
#  - a suitable tag for a prefixed head
# The tuple found in hints maps or constructed locally is returned as-is.
def _der_hintmapping (tp, hint='no_hint'):
	if tp == int or tp == long:
		return _hintmap_int [hint]
	elif tp == unicode:
		return _hintmap_unicode [hint]
	elif tp == str:
		return _hintmap_string [hint]
	elif tp == bool:
		return (t.DER_TAG_BOOLEAN, p.der_format_BOOLEAN)
	elif tp == time.struct_time:
		return _hintmap_time [hint]
	elif tp == float:
		return (t.DER_TAG_REAL, p.der_format_REAL)
	elif issubclass (tp, c.ASN1Object):
		return (tp._der_packer [0], lambda v: v._der_format ())
	else:
		raise Exception ('Not able to map ' + str(tp) + ' value to DER')


def der_pack (value, hint='no_hint', der_packer=None, cls=None):
	"""Pack a Python value into a binary string holding a DER blob; see
	   der_format() for a version that does not include the DER header.
	   Since native types may have been produced from a variety of
	   ASN.1 types, the hint can be used to signal the type name
	   (though any STRING trailer is stripped).  Alternatively,
	   use cls to provide an ASN1Object subclass for packing or
	   a der_packer instruction to apply.  The latter could crash
	   if not properly formatted -- at least make sure its DER_ENTER_
	   and DER_LEAVE nest properly and that the der_packer ends in
	   DER_PACK_END.
	"""
	if der_packer is not None:
		if not type (value) == list:
			value = [value]
		if cls is not None:
			raise Exception ('der_pack(...,der_packer=...,cls=...) is ambiguous')
		if hint != 'no_hint':
			raise Exception ('der_pack(...,der_packer=...,hint=...) is ambiguous')
		return _quickder.der_pack (der_packer, value)
	elif cls is not None:
		if not issubclass (cls,c.ASN1Obejct):
			raise Exception ('der_pack(value,cls=...) requires cls to be a subclass of ASN1Object')
		if not type (value) == list:
			value = [value]
		if hint != 'no_hint':
			raise Exception ('der_pack(...,cls=...,hint=...) is ambiguous')
		return _quickder.der_pack (cls._der_packer, value)
	elif isinstance (value, c.ASN1Object):
		return value._der_pack ()
	else:
		(tag,packfun) = _der_hintmapping (type(value), hint)
		return p.der_prefixhead (tag, packfun (value))

#TODO# der_unpack() -- is useful


def der_format (value, hint='no_hint'):
	"""Pack a Python value into a binary string holding the contents of
	   a DER blob, but not the surrounding DER header.  See der_pack().
	   Since native types may have been produced from a variety of
	   ASN.1 types, the hint can be used to signal the type name
	   (though any STRING trailer is stripped).
	"""
	(_,packfun) = _der_hintmapping (type(value), hint)
	return packfun (value)

#TODO# der_parse() -- would it be useful ???


