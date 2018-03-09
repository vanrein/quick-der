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
 * Sample a single flag, numbered from 0 onward.  We don't follow the
 * suggestion of X.690 to count from the MSB of the first word, but
 * will instead assign number 0 to the lowest bit.  Do note however,
 * that this bit may not be the LSB of the last byte; there may be
 * "empty" bits when the number of bits stored is not a multiple of 8
 * and they end up at what could be considered negative bit numbers
 * in our style of counting.
 *
 * The return value is -1 for error, or 0 for success, in which case
 * the value has been set; only when value is NULL, the return will
 * indicate whether the bit is available.
 */
int der_get_bitstring_flag (dercursor der_buf_bitstring, size_t bitnr, bool *value) {
	size_t bits = 8 * (der_buf_bitstring.derlen - 1) - *der_buf_bitstring.derptr;
	//DEBUG// fprintf (stderr, "der_get_bitstring_flag(): bits=%zd, bitnr=%zd\n", bits, bitnr);
	if (bitnr >= bits) {
		return -1;
	}
	if (value != NULL) {
		bits -= bitnr+1;
		*value = (der_buf_bitstring.derptr [1 + (bits >> 3)] >> ((~bits) & 0x07)) & 0x01;
		//DEBUG// fprintf (stderr, "der_get_bitstring_flag(): Read %d from offset %zd, value 0x%02x, shift %zd\n", *value, bits>>3, der_buf_bitstring.derptr [1 + (bits>>3)], (int) ((~bits) & 0x07));
	}
	return 0;
}

