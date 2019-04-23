/*
 * Test the data-packing and unpacking functions.
 */

/*
 *  Copyright 2017, Adriaan de Groot <groot@kde.org>
 *
 *  See LICENSE.MD for license details.
 *
 *  Redistribution and use is allowed according to the terms of the two-clause BSD license.
 *     https://opensource.org/licenses/BSD-2-Clause
 *     SPDX short identifier: BSD-2-Clause
 */

#include <arpa2/quick-der.h>

#include <stdio.h>

int test_unpack_int()
{
	uint8_t buffer[8];
	dercursor crs;
	int32_t t;
	int r;

	unsigned int len;
	for (len = 0; len < 8; ++len)
	{
		/* For various lengths, construct a buffer of (len-1)*0x00 0x01 */
		memset(buffer, 0, sizeof(buffer));
		buffer[len > 0 ? len - 1 : len] = 0x01;

		crs.derptr = buffer;
		crs.derlen = len;

		t = 16;
		r = der_get_int32(crs, &t);
		if (r != der_get_int32(crs, NULL))
		{
			fprintf(stderr, "! Length %d storing vs not-storing discrepancy.", len);
			return -1;
		}

		if ((len < 5) && r)
		{
			fprintf(stderr,"! Length %d failed.\n", len);
			return -1;
		}
		if ((len == 0) && !r && (t != 0))
		{
			fprintf(stderr,"! Length %d set unexpected t=%d.\n", len, t);
			return -1;
		}
		if ((len > 0) && !r && (t != 1))
		{
			fprintf(stderr,"! Length %d returned ok but value %d.\n", len, t);
			return -1;
		}
		if (r && (t != 16))
		{
			fprintf(stderr, "! Length %d failed but changed value to %d.\n", len, t);
			return -1;
		}
	}

	return 0;
}

int main(int argc, char **argv)
{
	return test_unpack_int();
}
