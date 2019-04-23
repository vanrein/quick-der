/* Test INTEGER comparison.  It's acting like it's pretty
 * clever, let's see if it holds up!
 */


#include <stdlib.h>
#include <stdio.h>


#include <arpa2/quick-der.h>


/* climbers[] represents (derptr,derlen) pairs in what should be
 * monotonically climbing order.  Every possible pair is compaired,
 * even in both directions.  The position in the list is used to
 * decide what would be the proper order.
 */

#define NUM_CLIMBERS 27
dercursor climbers [NUM_CLIMBERS] = {
	{ "\x80\x00\x00\x00\x00\x00", 6 },
	{ "\x80\x00\x00\x00\x00", 5 },
	{ "\x80\x00\x00\x00", 4 },
	{ "\x80\x00\x00", 3 },
	{ "\x80\x00", 2 },
	{ "\xe0\x00", 2 },
	{ "\xe0\xff", 2 },
	{ "\x80", 1 },
	{ "\xe0", 1 },
	{ "\xf0", 1 },
	{ "\xfe", 1 },
	{ "\xff", 1 },
	{ "\x00", 1 },
	{ "\x01", 1 },
	{ "\x40", 1 },
	{ "\x4f", 1 },
	{ "\x70", 1 },
	{ "\x7e", 1 },
	{ "\x7f", 1 },
	{ "\x01\x01", 2 },
	{ "\x01\x7f", 2 },
	{ "\x7f\x01", 2 },
	{ "\x7f\xff", 2 },
	{ "\x7f\xff\xff", 3 },
	{ "\x7f\xff\xff\xff", 4 },
	{ "\x7f\xff\xff\xff\xff", 5 },
	{ "\x7f\xff\xff\xff\xff\xff", 6 },
};


int cpu_cmp_int (int a, int b) {
	return a - b;
}


int sign (int a) {
	if (a < 0) {
		return -1;
	} else if (a > 0) {
		return +1;
	} else {
		return 0;
	}
}


int main (int argc, char *argv []) {
	int exitval = 0;
	int i, j;

	for (i=0; i < NUM_CLIMBERS; i++) {
		for (j=0; j < NUM_CLIMBERS; j++) {
			int soll = sign (cpu_cmp_int (          i ,           j ));
			int ist  = sign (der_cmp_int (climbers [i], climbers [j]));
			if (ist != soll) {
				fprintf (stderr, "Unexpected comparison result %d (expected %d) between #%d and #%d\n", ist, soll, i, j);
				exitval = 1;
			}
		}
	}

	exit (exitval);
}
