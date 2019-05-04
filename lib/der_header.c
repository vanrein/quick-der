#include <arpa2/quick-der.h>

#include <errno.h>

#include "qd-int.h"


/* Analyse the header of a DER structure.  Pass back its tag, len and the
 * total header length.  Analysis starts at crs, which will move past the
 * header by updating both its derptr and derlen components.  This function
 * returns 0 on success, or -1 on error (in which case it sets errno).
 *
 * It is not an error if crs->derlen spans less than *lenp + *hlenp; the
 * caller should check this condition.  It is an error if the crs->derlen
 * spans less than the DER header, so *lenp.
 *
 * For BIT STRINGS, this routine validates that remainder bits are cleared.
 * Note that this is a difference between BER and DER; DER requires that
 * the bits are 0 whereas BER welcomes arbitrary values.  In the interest
 * of security (bit buffer overflows) and reproducability of signatures on
 * data, this routine rejects non-zero remainder bits with an error.  For
 * your program, this may mean that the number of remainder bits do not
 * need to be checked if zero bits are acceptable without overflow risk.
 */
int der_header (dercursor *crs, uint8_t *tagp, size_t *lenp, uint8_t *hlenp) {
	uint8_t tag;
	uint8_t lenlen;
	uint8_t rembits;
	uint8_t rembyte;
	size_t len;
	if (crs->derlen == 0) {
		*tagp = DER_PACK_LEAVE;
		*lenp = 0;
		*hlenp = 0;
		return 0;
	} else if (crs->derlen < 2) {
		errno = EBADMSG;
		return -1;
	}
	*tagp = tag = *crs->derptr++;
	crs->derlen--;
	if ((tag & 0x1f) == 0x1f) {
		// No support for long tags
		errno = ERANGE;
		return -1;
	}
	len = *crs->derptr++;
	crs->derlen--;
	if (len & 0x80) {
		lenlen = len & 0x7f;
		if (lenlen == 0) {
			// Indefinite length form (unsupported BER)
			errno = EBADMSG;
			return -1;
		}
		*hlenp = 2 + lenlen;
		if (lenlen > crs->derlen) {
			errno = EBADMSG;
			return -1;
		}
		if (lenlen > sizeof (size_t)) {
			// No support for such long sizes
			errno = ERANGE;
			return -1;
		}
		crs->derlen -= lenlen;
		len = 0;
		while (lenlen-- > 0) {
			len <<= 8;
			len |= *crs->derptr++;
		}
	} else {
		*hlenp = 2;
	}
	if (len & DER_DERLEN_FLAG_CONSTRUCTED) {
		errno = ERANGE;
		return -1;
	}
#if 0
/* Do not require the entire message yet */
	if (len > crs->derlen) {
		errno = EBADMSG;
		return -1;
	}
#endif
	// Special treatment for BIT STRING (one additional header byte)
	if (tag == DER_TAG_BITSTRING) {
		rembits = *crs->derptr;
		rembyte = crs->derptr [len-1] & (0xff >> (8 - rembits));
		if ((len == 0) || (*crs->derptr > 7) || (rembyte != 0x00)) {
			errno = EBADMSG;
			return -1;
		}
	}
	*lenp = len;
DPRINTF ("DEBUG: Header analysis: tag 0x%02x, hdrlen %d, len %d, rest %d\n", *tagp, *hlenp, (int)*lenp, (int)crs->derlen);
	return 0;
}
