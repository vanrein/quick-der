#include <arpa2/quick-der.h>


/* Compare two DER encoded INTEGERS, returning a negative integer for a<b,
 * 0 for a==b and a positive integer for a>b.
 *
 * DER is as-compact-as-possible, and it is canonical, so we can assume that two
 * INTEGERs of the same size only needs a signed byte-by-byte comparison.
 *
 * Only values of the same size can return value 0; all others return -1 or +1.
 *
 * When the sizes differ, the sign of the longest value determines the outcome.
 * This is easy to see when the signs differ.  When the signs are the same it is
 * also true, because the bigger range covered by the longer value.
 *
 * When sizes differ, a long negative a or long positive b lead to -1 and the
 * opposite to +1.  This is also true when the sizes are the same but the signs
 * differ; this can be used to complement an unsigned byte-by-byte comparison.
 *
 * This function should probably move into Quick DER.
 */
int der_cmp_int (dercursor a, dercursor b) {
	uint8_t signbyte;
	if (a.derlen == b.derlen) {
		if (((*a.derptr ^ *b.derptr) & 0x80) == 0x00) {
		// Same size, same sign: unsigned byte comparison
			return memcmp (a.derptr, b.derptr, a.derlen);
		}
		// Same size, different sign: sign of a decides
		signbyte = *a.derptr;
	} else if (a.derlen > b.derlen) {
		// Size of a longer: sign of a decides
		signbyte = *a.derptr;
	} else {
		// Size of b longer: sign of b decides, but inverted
		signbyte = ~ *b.derptr;
	}
	return ((0x80 & signbyte) == 0x80) ? -1 : +1;
}
