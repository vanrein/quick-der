/*
 * Data-comparison functions.
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

#define EQUAL (0)
#define LESS (-1)
#define GREATER (1)

int der_cmp(dercursor c1, dercursor c2)
{
	if ((0 == c2.derlen) && (0 == c1.derlen))
	{
		/* Both are zero-length */
		return EQUAL;
	}
	else if (0 == c1.derlen)
	{
		/* c1 is zero-length, c2 isn't */
		return LESS;
	}
	else if (0 == c2.derlen)
	{
		return GREATER;
	}

	/* The strings are both non-zero length. */
	size_t shortest_len = c1.derlen < c2.derlen ? c1.derlen : c2.derlen;

	while (shortest_len--)
	{
		uint8_t d = *(c2.derptr++) - *(c1.derptr++);
		if (d)
		{
			return d;
		}
	}

	/* The strings are equal up to the shortest length */
	if (c1.derlen < c2.derlen)
	{
		return LESS;
	}
	else if (c1.derlen > c2.derlen)
	{
		return GREATER;
	}

	return EQUAL;
}
