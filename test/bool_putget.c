/* bool_putget.c -- Test der_put_bool followed by der_get_bool for identity.
 *
 * From: Rick van Rein <rick@openfortress.nl>
 */


#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>

#include <quick-der/api.h>


int putget_tests (void) {
	int ok = 1;
	int i;
	for (i=0; i<=1; i++) {
		char *itxt = i ? "TRUE": "FALSE";
		uint8_t ival = i ? 0xFF : 0x00;
        
		ok = 0;
		der_buf_bool_t buf;
		dercursor crs = der_put_bool (buf, i);
		if (crs.derlen != 1) {
			fprintf (stderr, "Boolean %s encoded in %zu bytes (should be 1)\n", itxt, crs.derlen);
		} else if (*buf != ival) {
			fprintf (stderr, "Wrong encoding of Boolean %s, as 0x%02x\n", itxt, *buf);
		} else {
			ok = 1;
		}
	}
	return ok;
}

int put_tests (void) {
	der_buf_bool_t buf_false, buf_true1, buf_true2;
	dercursor crs_false = der_put_bool (buf_false, 0);
	dercursor crs_true1 = der_put_bool (buf_true1, 1);
	dercursor crs_true2 = der_put_bool (buf_true2, 255);
	bool out_false, out_true1, out_true2;
	int ok_false = der_get_bool (crs_false, &out_false);
	int ok_true1 = der_get_bool (crs_true1, &out_true1);
	int ok_true2 = der_get_bool (crs_true2, &out_true2);
    
	/* der_get_bool returns 0 on success */
	if (ok_false) {
		fprintf (stderr, "get_bool from false failed.\n");
	}
	if (ok_true1) {
		fprintf (stderr, "get_bool from true (1) failed.\n");
	}
	if (ok_true2) {
		fprintf (stderr, "get_bool from true (255) failed.\n");
	}
        
	return !(ok_false || ok_true1 || ok_true2) &&
		(crs_false.derlen == 1) && (crs_true1.derlen == 1) &&  (crs_true2.derlen == 1) &&
		(*buf_false == 0x00) && (*buf_true1 == 0xff) && (*buf_true2 == 0xff) &&
		(out_false == 0) && (out_true1 == 1) && (out_true2 == 1);
}



int main (int argc, char *argv []) {

	int ok = 1;

	ok = ok && putget_tests ();
	ok = ok && put_tests ();

	exit (ok? 0: 1);

}
