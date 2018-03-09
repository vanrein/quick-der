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
 * Set or reset a single flag, numbered from 0 onward.  We don't
 * follow the suggestion of X.690 to count from the MSB of the first
 * word, but will instead assign number 0 to the lowest bit.  Do note
 * however, that this bit may not be the LSB of the last byte; there
 * may be "empty" bits when the number of bits stored is not a
 * multiple of 8 and they end up at what could be considered negative
 * bit numbers in our style of counting.
 *
 * The return value is -1 for error, or 0 for success.
 *
 * The macro DER_BUF_BITSTRING(NAME,NUMBITS) can be used to declare a
 * variable named NAME and with place for NUMBITS bits.  The value is
 * as initialised as may be expected for the type of declaration; so
 * for static, it would be zero-filled, but not otherwise.  You must
 * make sure that all bits are initialised, as you might otherwise
 * send out invalid content.
 */
int der_put_bitstring_flag (dercursor der_buf_bitstring, size_t bitnr, bool value) {
	size_t bits = 8 * (der_buf_bitstring.derlen - 1) - *der_buf_bitstring.derptr;
	//DEBUG// fprintf (stderr, "der_put_bitstring_flag(): bits=%zd, bitnr=%zd\n", bits, bitnr);
	if (bitnr >= bits) {
		return -1;
	}
	bits -= bitnr+1;
	uint8_t flag = 0x80 >> (bits & 0x07);
	uint8_t mask = ~flag;
	// Special handling for the last byte's trailing bits
	if ((bits >> 3) == der_buf_bitstring.derlen - 2) {
		// Mask out all bits below the flag as well
		mask -= flag-1;
	}
	uint8_t *bitaddr = &der_buf_bitstring.derptr [1 + (bits >> 3)];
	//DEBUG// fprintf (stderr, "der_put_bitstring_flag(): mask=0x%02x, flag=0x%02x, offset=%zd\n", mask, flag, bits>>3);
	*bitaddr = ((*bitaddr) & mask) | (value ? flag : 0x00);
	return 0;
}

