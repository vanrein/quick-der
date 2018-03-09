/*
 * Data-packing and unpacking functions.
 */

/*
 *  Copyright 2018, Rick van Rein <rick@openfortress.nl>
 *
 *  See LICENSE.MD for license details.
 *
 *  Redistribution and use is allowed according to the terms of the two-clause BSD license.
 *     https://opensource.org/licenses/BSD-2-Clause
 *     SPDX short identifier: BSD-2-Clause
 */

#include <quick-der/api.h>


/*
 * Get a block of 8 bits, numbering from the beginning of the
 * BIT STRING.  This can be used to retrieve byte sequences in a
 * BIT STRING, as is often done for signatures and key material.
 *
 * Note that the last byte can give special treatment to the
 * last significant few bits, but only when the BIT STRING was
 * created for a number of bits that is not a multiple of 8.
 * Since Quick DER will silently overlook incoming BER habits,
 * it will wipe such bits to zero, regardless of their transport
 * format.  This should not invalidate any digital signatures,
 * since nobody will be signing BER anyway (DER and CER are used
 * for that, which is what this function basically delivers).
 *
 * The return value is -1 for out-of-ranger errors, or zero on
 * success, in which case it has set the value.  Only when value
 * is NULL, it will not be set and the return value can be used
 * to see if this operation would have been possible.
 */
int der_get_bitstring_by_eight (dercursor der_buf_bitstring, size_t bytenr, uint8_t *value) {
	uint8_t mask = 0xff;
	if (bytenr >= der_buf_bitstring.derlen - 1) {
		return -1;
	}
	if (value != NULL) {
		if ((*der_buf_bitstring.derptr > 0) && (bytenr == der_buf_bitstring.derlen - 2)) {
			mask = 0xff & (mask << *der_buf_bitstring.derptr);
			//DEBUG// fprintf (stderr, "der_get_bitstring_by_eight(): Mask 0x%02x drops %d bits from 0x%02x\n",mask, (int) *der_buf_bitstring.derptr, der_buf_bitstring.derptr [1+bytenr]);
		}
		*value = der_buf_bitstring.derptr [1 + bytenr] & mask;
	}
	return 0;
}

