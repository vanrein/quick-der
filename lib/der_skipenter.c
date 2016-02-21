#include <quick-der/api.h>


/* Skip the current value under the cursor.  Return an empty cursor value
 * if nothing more is to be had.
 * This function returns -1 on error and sets errno; 0 on success.
 */
int der_skip (dercursor *crs) {
	uint8_t tag;
	uint8_t hlen;
	size_t len;
	if (der_header (crs, &tag, &len, &hlen)) {
		crs->derptr = NULL;
		crs->derlen = 0;
		return -1;
	} else {
		crs->derptr += len;
		crs->derlen -= len;
		return 0;
	}
}

/* Enter the current value under the cursor.  Return an empty cursor value
 * if nothing more is to be had.  Some special handling is done for BIT STRING
 * entrance; for them, the number of remainder bits is required to be 0 and
 * that initial byte is skipped.
 *
 * This function returns -1 on error and sets errno; 0 on success.
 */
int der_enter (dercursor *crs) {
	uint8_t tag;
	uint8_t hlen;
	size_t len;
	if (der_header (crs, &tag, &len, &hlen)) {
		crs->derptr = NULL;
		crs->derlen = 0;
		return -1;
	} else {
		crs->derlen = len;
		return 0;
	}
	if (tag == DER_TAG_BITSTRING) {
		crs->derlen--;
		crs->derptr++;
	}
}
