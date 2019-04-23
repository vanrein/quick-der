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

#include <arpa2/quick-der.h>

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
