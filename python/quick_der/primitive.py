# primitive.py -- der_format_TYPE and der_parse_TYPE for primitive content
#
# Terminology:
#   * der_pack() and der_unpack() work against a _der_packer syntax
#   * der_format() and der_parse() only look at the body (and needs hints)
#
# For more complex operations, such as on classes, see format.py


import _quickder
import time

from six.moves import intern


#
# Utility functions
#


# Prefix a DER header (tag and length) to a body
# This is a currying function, used as: _der_prefix_head_fn (tag) (body)
def der_prefixhead(tag, body):
    blen = len(body)
    if blen == 0:
        lenh = chr(0)
    elif blen <= 127:
        lenh = chr(blen)
    else:
        lenh = ''
        while blen > 0:
            lenh = chr(blen % 256) + lenh
            blen >>= 8
        lenh = chr(0x80 + len(lenh))
    return chr(tag) + lenh + body


#
# Mappings for primitive DER elements that map to native Python objects
#


def der_format_STRING(sval):
    return sval


def der_parse_STRING(derblob):
    return derblob


def der_format_OID(oidstr, hdr=False):
    oidvals = list(map(int, oidstr.split('.')))
    oidvals[1] += 40 * oidvals[0]
    enc = ''
    for oidx in range(len(oidvals) - 1, 0, -1):
        oidval = oidvals[oidx]
        enc = chr(oidval & 0x7f) + enc
        while oidval > 127:
            oidval >>= 7
            enc = chr(0x80 | (oidval & 0x7f)) + enc
    if hdr:
        enc = _quickder.der_pack('\x06\x00', [enc])
    return enc


def der_parse_OID(derblob):
    oidvals = [0]
    for byte in map(ord, derblob):
        if byte & 0x80 != 0x00:
            oidvals[-1] = (oidvals[-1] << 7) | (byte & 0x7f)
        else:
            oidvals[-1] = (oidvals[-1] << 7) | byte
            oidvals.append(0)
    fst = oidvals[0] // 40
    snd = oidvals[0] % 40
    oidvals = [fst, snd] + oidvals[1:-1]
    retval = '.'.join(map(str, oidvals))
    return intern(retval)


def der_format_RELATIVE_OID(oidstr):
    raise NotImplementedError('der_format_RELATIVE_OID')


def der_parse_RELATIVE_OID(oidstr):
    raise NotImplementedError('der_parse_RELATIVE_OID')


def der_format_BITSTRING(bitint):
    return chr(0) + der_format_INTEGER(bitint)


def der_parse_BITSTRING(derblob):
    assert len(derblob) > 0, 'BITSTRING elements cannot be empty'
    if ord(derblob[0]) != 0:
        raise NotImplementedError('BISTRING with more than 0 trailing bits are not implemented')
    return der_parse_INTEGER(derblob[1:])


def der_format_UTCTIME(tstamp):
    return time.strftime('%y%m%d%H%M%SZ', tstamp)


def der_parse_UTCTIME(derblob):
    return time.strptime(derblob, '%y%m%d%H%M%SZ')


def der_format_GENERALIZEDTIME(tstamp):
    # TODO# No support for fractional seconds
    return time.strftime('%Y%m%d%H%M%SZ', tstamp)


def der_parse_GENERALIZEDTIME(derblob):
    # TODO# No support for fractional seconds
    return time.strptime(derblob, '%Y%m%d%H%M%SZ')


def der_format_BOOLEAN(bval):
    return '\xff' if bval else '\x00'


def der_parse_BOOLEAN(derblob):
    return derblob != '\x00' * len(derblob)


def der_format_INTEGER(ival, hdr=False):
    retval = ''
    byt = ival & 0xff
    while ival not in [0, -1]:
        byt = ival & 0xff
        ival = ival >> 8
        retval = chr(byt) + retval
    if ival == 0:
        if len(retval) > 0 and byt & 0x80 == 0x80:
            retval = chr(0x00) + retval
    else:
        if len(retval) == 0 or byt & 0x80 == 0x00:
            retval = chr(0xff) + retval
    if hdr:
        retval = _quickder.der_pack('\x02\x00', [retval])
    return retval


def der_parse_INTEGER(derblob):
    if derblob == '':
        return 0
    retval = 0
    if ord(derblob[0]) & 0x80:
        retval = -1
    for byt in map(ord, derblob):
        retval = (retval << 8) + byt
    return retval


def der_format_REAL(rval):
    raise NotImplementedError('der_format_REAL -- too many variations')
    # See X.690 section 8.5 -- base2, base10, ... yikes!
    # if rval == 0.0:
    #    return ''
    # else:
    #   pass


def der_parse_REAL():
    raise NotImplementedError('der_parse_REAL -- too many variations')
    # See X.690 section 8.5 -- base2, base10, ... yikes!
