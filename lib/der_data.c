/*
 * Data-packing and unpacking functions.
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

#include <quick-der/api.h>

/* Extract an int from a cursor. Based heavily on tlspool's qder2b_unpack_int32. */

int der_get_int32(dercursor crs, int32_t *valp)
{
	int32_t retval = 0;
	if (crs.derlen > 4)
	{
		/* It won't fit in 32 bits */
		return -1;
	}

	if ((crs.derlen > 0) && (0x80 & *crs.derptr))
	{
		/* Flip the sign. */
		retval = -1;
	}

	for (unsigned int i=0; i < crs.derlen; ++i)
	{
		retval <<= 8;
		retval += crs.derptr[i];
	}

	if (valp)
	{
		*valp = retval;
	}
	return 0;
}

/* Extract an unsigned int from a cursor.
 *
 * Because DER uses signed 2s complement storage, a value > 0x7fffffff needs
 * to be stored in 5 bytes: the first (big-endian) byte is then 0x00,
 * followed by the 4 byes of the value. In 40-bit signed, that's 0x00????????.
 */
int der_get_uint32(dercursor crs, uint32_t *valp)
{
	uint32_t retval = 0;
	if (crs.derlen > 5)
	{
		/* It won't fit. */
		return -1;
	}

	if (crs.derlen == 5)
	{
		if (*crs.derptr)
		{
			return -1;
		}
		crs.derlen--;
		crs.derptr++;
	}

	for (unsigned int i=0; i < crs.derlen; ++i)
	{
		retval <<= 8;
		retval += crs.derptr[i];
	}

	if (valp)
	{
		*valp = retval;
	}
	return 0;
}
