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


/* Extract an unsigned int from a cursor.
 *
 * Because DER uses signed 2s complement storage, a value > 0x7fffffff needs
 * to be stored in 5 bytes: the first (big-endian) byte is then 0x00,
 * followed by the 4 byes of the value. In 40-bit signed, that's 0x00????????.
 */
int der_get_uint(dercursor crs, unsigned int *valp)
{
	unsigned int retval = 0;
	if (crs.derlen > 1 + sizeof (retval))
	{
		/* It won't fit. */
		return -1;
	}

	if (crs.derlen == 1 + sizeof (retval))
	{
		if (*crs.derptr)
		{
			return -1;
		}
		crs.derlen--;
		crs.derptr++;
	}

	unsigned int i;
	for (i=0; i < crs.derlen; ++i)
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
