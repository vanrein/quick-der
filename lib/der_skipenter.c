#include <arpa2/quick-der.h>


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
	if (der_header (crs, &tag, &len, &hlen) == 0) {
		crs->derlen = len;
		if (tag == DER_TAG_BITSTRING) {
			//UNUSED// hlen++;
			crs->derlen--;
			crs->derptr++;
		}
		if (len != (size_t) -1) {
			return 0;
		} else {
			errno = EBADMSG;
		}
	}
	// we ran into an error
	crs->derptr = NULL;
	crs->derlen = 0;
	return -1;
}

/* Assuming that we are looking at a concatenation of DER elements, focus on
 * the first one.  That is, chop off anything beyond the first element.
 *
 * This function returns -1 on error and sets errno; 0 on success.
 */
int der_focus (dercursor *crs) {
	uint8_t tag;
	uint8_t hlen;
	size_t len;
	dercursor crs2 = *crs;
	if (der_header2 (crs2, &tag, &len, &hlen)) {
		crs->derptr = NULL;
		crs->derlen = 0;
		return -1;
	}
	crs->derlen = hlen + len;
	return 0;
}
