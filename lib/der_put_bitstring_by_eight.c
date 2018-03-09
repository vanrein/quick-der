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
 * Set a block of 8 bits, numbering from the beginning of the
 * BIT STRING.  This can be used to store byte sequences in a
 * BIT STRING, as is often done for signatures and key material.
 *
 * Note that the last byte can give special treatment to the
 * least significant few bits, but only when the BIT STRING was
 * created for a number of bits that is not a multiple of 8.
 * Since Quick DER is always sending DER, it will enforce zero
 * in such bits, and otherwise report error, as it will do for
 * any other out-of-bounds bits.
 *
 * The return value is -1 for error, or 0 for success.
 */
int der_put_bitstring_by_eight (dercursor der_buf_bitstring, size_t bytenr, uint8_t value) {
	if (bytenr >= der_buf_bitstring.derlen - 1) {
		return -1;
	}
	if ((*der_buf_bitstring.derptr > 0) && (bytenr == der_buf_bitstring.derlen - 2)) {
		uint8_t mask = 0xff >> (8 - *der_buf_bitstring.derptr);
		//DEBUG// fprintf (stderr, "der_put_bitstring_by_eight(): bytenr=%zd, value=0x%02x, mask=0x%02x\n", bytenr, value, mask);
		if ((value & mask) != 0) {
			return -1;
		}
	}
	der_buf_bitstring.derptr [1 + bytenr] = value;
	return 0;
}

