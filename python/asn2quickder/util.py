from asn2quickder import packstx as api


class dprint(object):
    """
    Simple debugging-print object; looks like a print statement.
    Instantiate this with a format string and optional arguments,
    like so:
        dprint("foo", bar)
    if the format string does not contain a % (like here, then the
    string and arguments are printed as strings, one after the other,
    joined by spaces. If a % is present, uses %-interpolation to
    format the arguments in the string.

    If dprint.enable is False (by default), nothing is ever printed
    and the objects of this class do nothing.

    Passing option -v (verbose) to this script enables debugging-
    print by setting enable to True.
    """
    enable = False

    def __init__(self, s, *args):
        if self.enable:
            if args:
                if "%" in s:
                    print(s % args)
                else:
                    print(" ".join([s] + map(lambda x: str(x), args)))
            else:
                print(s)


def tosym(name):
    """Replace unsupported characters in ASN.1 symbol names"""
    return str(name).replace(' ', '').replace('-', '_')


api_prefix = '_api'

dertag2atomsubclass = {
    api.DER_TAG_BOOLEAN: 'ASN1Boolean',
    api.DER_TAG_INTEGER: 'ASN1Integer',
    api.DER_TAG_BITSTRING: 'ASN1BitString',
    api.DER_TAG_OCTETSTRING: 'ASN1OctetString',
    api.DER_TAG_NULL: 'ASN1Null',
    api.DER_TAG_OID: 'ASN1OID',
    api.DER_TAG_REAL: 'ASN1Real',
    api.DER_TAG_ENUMERATED: 'ASN1Enumerated',
    api.DER_TAG_UTF8STRING: 'ASN1UTF8String',
    api.DER_TAG_RELATIVEOID: 'ASN1RelativeOID',
    api.DER_TAG_NUMERICSTRING: 'ASN1NumericString',
    api.DER_TAG_PRINTABLESTRING: 'ASN1PrintableString',
    api.DER_TAG_TELETEXSTRING: 'ASN1TeletexString',
    api.DER_TAG_VIDEOTEXSTRING: 'ASN1VideoTexString',
    api.DER_TAG_IA5STRING: 'ASN1IA5String',
    api.DER_TAG_UTCTIME: 'ASN1UTCTime',
    api.DER_TAG_GENERALIZEDTIME: 'ASN1GeneralizedTime',
    api.DER_TAG_GRAPHICSTRING: 'ASN1GraphicString',
    api.DER_TAG_VISIBLESTRING: 'ASN1VisibleString',
    api.DER_TAG_GENERALSTRING: 'ASN1GeneralString',
    api.DER_TAG_UNIVERSALSTRING: 'ASN1UniversalString',
    api.DER_PACK_ANY: 'ASN1Any'
}
