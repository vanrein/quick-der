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
 * Sample a single flag, numbered from 0 onward.  We follow the
 * suggestion of X.690 to count from the MSB of the first word.
 * Future extensions to the number of bits can be added to the
 * trailing end of the data.
 *
 * In support of this future extensibility, we return an error
 * for bits beyond the end of the data range, and leave the
 * output value untouched in that case.  As long as you setup
 * a default value in the flag in the output value before
 * calling, you can ignore the errors and process the output
 * whether it be that default or something actively supplied
 * in the data.
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
		*value = (der_buf_bitstring.derptr [1 + (bitnr >> 3)] >> ((~bitnr) & 0x07)) & 0x01;
		//DEBUG// fprintf (stderr, "der_get_bitstring_flag(): Read %d from offset %zd, value 0x%02x, shift %zd\n", *value, bitnr>>3, der_buf_bitstring.derptr [1 + (bitnr>>3)], (int) ((~bitnr) & 0x07));
	}
	return 0;
}

