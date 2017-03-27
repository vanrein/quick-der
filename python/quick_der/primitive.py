# primitive.py -- der_pack_TYPE and der_unpack_TYPE for primitive content


import _quickder

import time


if not 'intern' in dir (globals () ['__builtins__']):
	try:
		from sys import intern
	except:
		intern = lambda s: s


#
# Mappings for primitive DER elements that map to native Python objects
#


def der_pack_STRING (sval):
	return sval


def der_unpack_STRING (derblob):
	return derblob


def der_pack_OID (oidstr, hdr=False):
	oidvals = map (int, oidstr.split ('.'))
	oidvals [1] += 40 * oidvals [0]
	enc = ''
	for oidx in range (len (oidvals)-1, 0, -1):
		oidval = oidvals [oidx]
		enc = chr (oidval & 0x7f) + enc
		while oidval > 127:
			oidval >>= 7
			enc = chr (0x80 | (oidval & 0x7f)) + enc
	if hdr:
		enc = _quickder.der_pack ('\x06\x00', [enc])
	return enc


def der_unpack_OID (derblob):
	oidvals = [0]
	for byte in map (ord, derblob):
		if byte & 0x80 != 0x00:
			oidvals [-1] = (oidvals [-1] << 7) | (byte & 0x7f)
		else:
			oidvals [-1] = (oidvals [-1] << 7) |  byte
			oidvals.append (0)
	fst = oidvals [0] / 40
	snd = oidvals [0] % 40
	oidvals = [fst, snd] + oidvals [1:-1]
	retval = '.'.join (map (str, oidvals))
	return intern (retval)


def der_pack_RELATIVE_OID (oidstr):
	raise NotImplementedError ('der_pack_RELATIVE_OID')


def der_unpack_RELATIVE_OID (oidstr):
	raise NotImplementedError ('der_unpack_RELATIVE_OID')


def der_pack_BITSTRING (bitset):
	bits = [0]
	for bit in bitset:
		byte = 1 + (bit >> 3)
		if len (bits) < byte + 1:
			bits = bits + [0] * (byte + 1 - len (bits))
		bits [byte] |= (1 << (bit & 0x07))
	return ''.join (map (chr,bits))


def der_unpack_BITSTRING (derblob):
	#TODO# Consider support of constructed BIT STRING types
	assert len (derblob) >= 1, 'Empty BIT STRING values cannot occur in DER'
	assert ord (derblob [0]) <= 7, 'BIT STRING values must have a first byte up to 7'
	bitnum = 8 * len (derblob) - 8 - ord (derblob [0])
	bitset = set ()
	for bit in range (bitnum):
		if ord (derblob [(bit >> 3) + 1]) & (1 << (bit & 0x07)) != 0:
			bitset.add (bit)
	return bitset


def der_pack_UTCTIME (tstamp):
	return time.strftime (pstamp, '%y%m%d%H%M%SZ')


def der_unpack_UTCTIME (derblob):
	return time.strptime (derblob, '%y%m%d%H%M%SZ')


def der_pack_GENERALIZEDTIME (tstamp):
	#TODO# No support for fractional seconds
	return time.strftime (tstamp, '%Y%m%d%H%M%SZ')


def der_unpack_GENERALIZEDTIME (derblob):
	#TODO# No support for fractional seconds
	return time.strptime (derblob, '%Y%m%d%H%M%SZ')


def der_pack_BOOLEAN (bval):
	return '\xff' if bval else '\x00'


def der_unpack_BOOLEAN (derblob):
	return derblob != '\x00' * len (derblob)


def der_pack_INTEGER (ival, hdr=False):
	retval = ''
	while ival not in [0,-1]:
		byt = ival & 0xff
		ival = ival >> 8
		retval = chr (byt) + retval
	if ival == 0:
		if len (retval) > 0 and byt & 0x80 == 0x80:
			retval = chr (0x00) + retval
	else:
		if len (retval) == 0 or byt & 0x80 == 0x00:
			retval = chr (0xff) + retval
	if hdr:
		retval = _quickder.der_pack ('\x02\x00', [retval])
	return retval


def der_unpack_INTEGER (derblob):
	if derblob == '':
		return 0
	retval = 0
	if ord (derblob [0]) & 0x80:
		retval = -1
	for byt in map (ord, derblob):
		retval = (retval << 8) + byt
	return retval


def der_pack_REAL (rval):
	raise NotImplementedError ('der_pack_REAL -- too many variations')
	# See X.690 section 8.5 -- base2, base10, ... yikes!
	if rval == 0.0:
		return ''
	else:
		pass

def der_unpack_REAL ():
	raise NotImplementedError ('der_pack_REAL -- too many variations')
	# See X.690 section 8.5 -- base2, base10, ... yikes!


