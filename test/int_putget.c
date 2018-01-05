/* int_putget.c -- Test der_put_[u]int32 followed by der_get_[u]int32 for identity.
 *
 * From: Rick van Rein <rick@openfortress.nl>
 */


#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>

#include <quick-der/api.h>


int unsigned_tests (void) {
	uint32_t tests [] = {
		0, 1, 255, 256, 32767, 32768, 65535, 65536,
		0x7fffffff, 0x80000000, 0xc0000000, 0xf0000000, 0xffffffff
	};
	int numtests = sizeof (tests) / sizeof (tests [0]);
	int ok = 1;
	int i;
	for (i=0; i<numtests; i++) {
		der_buf_uint32_t buf;
		uint32_t val;
		dercursor crs = der_put_uint32 (buf, tests [i]);
		int fit = (der_get_uint32 (crs, &val) == 0);  /* success return is 0, so turn that around */
		int match = (val == tests [i]);
		ok = ok && fit && match;
		if (!fit) {
			fprintf (stderr, "Unsigned integer %u took %zu bytes %02x %02x... and does not fit in 32 bits anymore\n", tests [i], crs.derlen, crs.derptr [0], crs.derptr [1]);
		} else if (!match) {
			fprintf (stderr, "Unsigned integer %u took %zu bytes and came back as %u\n", tests [i], crs.derlen, val);
		}
	}
	return ok;
}


int signed_tests (void) {
	int32_t tests [] = {
		0, 1, 255, 256, 32767, 32768, 65535, 65536,
		-1, -255, -256, -257, -32767, -32768, -32769,
		0x7fffffff, 0x7fffffff,
		-0x7fffffff, -0x80000000, -0x40000000
	};
	int numtests = sizeof (tests) / sizeof (tests [0]);
	int ok = 1;
	int i;
	for (i=0; i<numtests; i++) {
		der_buf_int32_t buf;
		int32_t val;
		dercursor crs = der_put_int32 (buf, tests [i]);
		int fit = (der_get_int32 (crs, &val) == 0);
		int match = (val == tests [i]);
		ok = ok && fit && match;
		if (fit != 0) {
			fprintf (stderr, "Signed integer %d took %zu bytes %02x %02x... and does not fit in 32 bits anymore\n", tests [i], crs.derlen, crs.derptr [0], crs.derptr [1]);
		} else if (match != 0) {
			fprintf (stderr, "Signed integer %d took %zu bytes and came back as %d\n", tests [i], crs.derlen, val);
		}
	}
	return ok;
}


int main (int argc, char *argv []) {

	int ok = 1;

	ok = ok && unsigned_tests ();
	ok = ok && signed_tests ();

	exit (ok? 0: 1);

}
