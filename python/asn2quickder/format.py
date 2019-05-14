# formapackstx.py -- Taking the turn from DER to native, format as DER
#
# Terminology:
#   * der_pack() and der_unpack() work against a _der_packer syntax
#   * der_format() and der_parse() only look at the body (and needs hints)
#
# For primitive operations, such as on INTEGER and BOOLEAN, see primitive.py


import _quickder
import time

from asn2quickder import classes
from asn2quickder import packstx
from asn2quickder import primitive


#
# Various mappings from hint names (with some aliases) to a packer function
#

# Report an error, stating that a hint is required for the map at hand
def _hintmap_needs_hint(value):
    raise Exception('To pack ' + str(type(value)) + ', please provide a hint')


_hintmap_int = {
    'no_hint': (packstx.DER_TAG_INTEGER, primitive.der_format_INTEGER),
    'INTEGER': (packstx.DER_TAG_INTEGER, primitive.der_format_INTEGER),
    'BITSTRING': (packstx.DER_TAG_BITSTRING, primitive.der_format_BITSTRING),
}

_hintmap_unicode = {
    'no_hint': (None, _hintmap_needs_hint),
    'UTF8': (packstx.DER_TAG_UTF8STRING, primitive.der_format_STRING),
    'OCTET': (packstx.DER_TAG_OCTETSTRING, primitive.der_format_STRING),
    'GENERALIZED': (packstx.DER_TAG_GENERALSTRING, primitive.der_format_STRING),
    'GENERAL': (packstx.DER_TAG_GENERALSTRING, primitive.der_format_STRING),
}

_hintmap_str = {
    'no_hint': (None, _hintmap_needs_hint),
    'IA5': (packstx.DER_TAG_IA5STRING, primitive.der_format_STRING),
    'ASCII': (packstx.DER_TAG_IA5STRING, primitive.der_format_STRING),
    'OCTET': (packstx.DER_TAG_OCTETSTRING, primitive.der_format_STRING),
    'GENERALIZED': (packstx.DER_TAG_GENERALSTRING, primitive.der_format_STRING),
    'GENERAL': (packstx.DER_TAG_GENERALSTRING, primitive.der_format_STRING),
    'PRINTABLE': (packstx.DER_TAG_PRINTABLESTRING, primitive.der_format_STRING),
    'OID': (packstx.DER_TAG_OID, primitive.der_format_OID),
    'RELATIVE_OID': (packstx.DER_TAG_RELATIVEOID, primitive.der_format_RELATIVE_OID),
    'RELATIVEOID': (packstx.DER_TAG_RELATIVEOID, primitive.der_format_RELATIVE_OID),
}

_hintmap_time = {
    'no_hint': (packstx.DER_TAG_GENERALIZEDTIME, primitive.der_format_GENERALIZEDTIME),
    'GENERAL': (packstx.DER_TAG_GENERALIZEDTIME, primitive.der_format_GENERALIZEDTIME),
    'GENERALIZED': (packstx.DER_TAG_GENERALIZEDTIME, primitive.der_format_GENERALIZEDTIME),
    'UTC': (packstx.DER_TAG_UTCTIME, primitive.der_format_UTCTIME),
    'GMT': (packstx.DER_TAG_UTCTIME, primitive.der_format_UTCTIME),
}


# ##TODO### hintmaps' (a,b) have tag a implies formatter b, use b = a2b [a] ???
# ##TODO### that also delivers the parser c, through c = a2c [a]


def _der_hintmapping(tp, hint='no_hint'):
    """
    Based on a value's type and a possible added hint, find a pair of
      - a value packing function
      - a suitable tag for a prefixed head

    The tuple found in hints maps or constructed locally is returned as-is.
    """
    if tp == int or tp == long:
        return _hintmap_int[hint]
    elif tp == unicode:
        return _hintmap_unicode[hint]
    elif tp == str:
        return _hintmap_str[hint]
    elif tp == bool:
        return packstx.DER_TAG_BOOLEAN, primitive.der_format_BOOLEAN
    elif tp == time.struct_time:
        return _hintmap_time[hint]
    elif tp == float:
        return packstx.DER_TAG_REAL, primitive.der_format_REAL
    elif issubclass(tp, classes.ASN1Object):
        return tp._der_packer[0], lambda v: v._der_format()
    else:
        raise Exception('Not able to map ' + str(tp) + ' value to DER')


def der_pack(value, hint='no_hint', der_packer=None, cls=None):
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
        if not type(value) == list:
            value = [value]
        if cls is not None:
            raise Exception('der_pack(...,der_packer=...,cls=...) is ambiguous')
        if hint != 'no_hint':
            raise Exception('der_pack(...,der_packer=...,hint=...) is ambiguous')
        return _quickder.der_pack(der_packer, value)
    elif cls is not None:
        if not issubclass(cls, classes.ASN1Object):
            raise Exception('der_pack(value,cls=...) requires cls to be a subclass of ASN1Object')
        if not type(value) == list:
            value = [value]
        if hint != 'no_hint':
            raise Exception('der_pack(...,cls=...,hint=...) is ambiguous')
        return _quickder.der_pack(cls._der_packer, value)
    elif isinstance(value, classes.ASN1Object):
        return value._der_pack()
    else:
        (tag, packfun) = _der_hintmapping(type(value), hint)
        return primitive.der_prefixhead(tag, packfun(value))


# TODO# der_unpack() -- is useful


def der_format(value, hint='no_hint'):
    """Pack a Python value into a binary string holding the contents of
       a DER blob, but not the surrounding DER header.  See der_pack().
       Since native types may have been produced from a variety of
       ASN.1 types, the hint can be used to signal the type name
       (though any STRING trailer is stripped).
    """
    (_, packfun) = _der_hintmapping(type(value), hint)
    return packfun(value)

# TODO# der_parse() -- would it be useful ???
