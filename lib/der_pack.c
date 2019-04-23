#include <arpa2/quick-der.h>

#include "qd-int.h"


/* Backward-insert the bytes for the individual entries of the given derprep
 * structure; the entry is assumed to be setup with prepack, and so to contain
 * a derray pointing to an array of dercursor, and the derlen_msb is supposed
 * to be the element count with the highest bit set for the
 * DER_DERLEN_FLAG_CONSTRUCTED flagging.
 *
 * This function does not return failure under the assumption that a
 * properly-sized buffer is available for it.  The return value is
 * still the size, because it is needed when processing the data.
 *
 * If bufend is NULL, this function can be used to measure the size of the
 * total insertion.  In this case, the function may return DER_DERLEN_ERROR
 * to indicate an error.
 */
static size_t der_pack_prepack (const derprep *derp, uint8_t **bufend) {
	size_t totlen = 0;
	size_t elmlen;
	size_t cnt = derp->derlen_msb & ~DER_DERLEN_FLAG_CONSTRUCTED;
	dercursor *crs = derp->derray + cnt;
	uint8_t *buf;
	while (crs--, cnt-- > 0) {
		if (crs->derlen & DER_DERLEN_FLAG_CONSTRUCTED) {
			elmlen = der_pack_prepack ((const derprep *) crs, bufend);
			if (elmlen == DER_DERLEN_ERROR) {
				return DER_DERLEN_ERROR;
			}
		} else {
			elmlen = crs->derlen;
			if (bufend) {
				buf = *bufend;
				buf -= elmlen;
				memcpy (buf, crs->derptr, elmlen);
DPRINTF ("DEBUG: Wrote %4d bytes to %p\n", (int)elmlen, (void *)buf);
				*bufend = buf;
			}
		}
		totlen += elmlen;
		if ((totlen | elmlen) & DER_DERLEN_FLAG_CONSTRUCTED) {
			return DER_DERLEN_ERROR;
		}
	}
	return totlen;
}


/* Backward-insert the bytes for der_pack() for the given syntax, using the
 * DER array for elementary values.  Special handling is provided when a
 * BIT STRING is entered; this encapsulates byte-aligned DER codes into a
 * bit-aligned BIT STRING, so we can insert the remainder bits set to 0.
 * Also handled specially is DER_PACK_ANY, which causes the entire structure
 * to be stored or returned, including its DER header.
 *
 * The routine returns 0 if it encounters an error, or otherwise the number
 * of bytes filled.  When it is called with a non-NULL bufend and an output
 * buffer of the right size, it will not return an error.
 */
static size_t der_pack_rec (const derwalk *syntax, int *stxlen,
				uint8_t **bufend,
				const dercursor *derray, size_t *offsetp) {
	size_t totlen = 0;
	size_t elmlen = 0;
	size_t tmplen;
	bool addhdr;
	bool bitstr;
	uint8_t cmd;
	uint8_t tag;
	uint8_t *buf;
	uint8_t lenlen;
	const dercursor *dernext;
DPRINTF ("DEBUG: Entered recursive call der_pack_rec() with bufend=%p\n", (void *)(bufend? *bufend: 0));
	do {
		// deref stxend; decrease the stored pointer; deref that pointer:
		tag = cmd = syntax [-- *stxlen];
		bitstr = (cmd == (DER_PACK_ENTER | DER_TAG_BITSTRING));
DPRINTF ("DEBUG: Command to pack_rec() is 0x%02x, collected length is %zd, offset is %zd\n", cmd, totlen, *offsetp);
		// Note: DER_PACK_ANY ends up under DER_PACK_STORE below
		if ((cmd == DER_PACK_CHOICE_BEGIN)
					|| (cmd == DER_PACK_CHOICE_END)
					|| (cmd == DER_PACK_OPTIONAL)) {
			// Skip, and rely on consistent NULL dercursor entries
DPRINTF ("DEBUG: Choice|Optional command has no data\n");
			cmd = 0x00;  // Avoid falling out (OPTIONAL & ENTER)
			continue;
		} else if (cmd & DER_PACK_ENTER) {
			// Ends current (recursive) der_pack_rec() for sub-part
			// Continue below, where the <tag,elmlen> header is added
			addhdr = (totlen > 0) ?1 :0;
			elmlen = totlen;
			totlen = bitstr? 1: 0;
DPRINTF ("DEBUG: Post-enter element, moved totlen %zd to element length\n", elmlen);
		} else if (cmd == DER_PACK_LEAVE) {
			// Make a recursive call for what precedes DER_PACK_LEAVE
			elmlen = der_pack_rec (syntax, stxlen, bufend, derray, offsetp);
			if (elmlen == DER_DERLEN_ERROR) {
				return DER_DERLEN_ERROR;
			}
			addhdr = 0;
DPRINTF ("DEBUG: Recursive element length set to %zd\n", elmlen);
		} else {
			// We have hit upon a DER_PACK_STORE value (includes ANY)
			addhdr = (cmd != DER_PACK_ANY);
			// Consume one array element, even if it will be NULL
			(*offsetp)--;
			dernext = derray + *offsetp;	// offset may have changed
DPRINTF ("DEBUG: Updated offset to %zd, pointer is %p\n", *offsetp, (void *)dernext);
			if (der_isnull (dernext)) {
				// Do not pack this entry, DEFAULT or CHOICE
				elmlen = 0;
				addhdr = 0;
DPRINTF ("DEBUG: Consumed NULL entry at %zd, so elmlen set to 0\n", *offsetp);
			} else if (dernext->derlen & DER_DERLEN_FLAG_CONSTRUCTED) {
				// Prepacked Constructed, non-NULL entry
				elmlen = der_pack_prepack ((const derprep *) dernext, bufend);
				if (elmlen == DER_DERLEN_ERROR) {
					return DER_DERLEN_ERROR;
				}
DPRINTF ("DEBUG: Fetched length from constructed, recursive element\n");
			} else {
				// Primitive, non-NULL entry
				elmlen = dernext->derlen;
				if ((elmlen > 0) && (bufend != NULL)) {
					buf = *bufend;
					buf -= elmlen;
					memcpy (buf, dernext->derptr, elmlen);
DPRINTF ("DEBUG: Wrote %4d bytes to %p\n", (int)elmlen, (void *)buf);
					*bufend = buf;
				}
DPRINTF ("DEBUG: Fetched length from primitive element\n");
			}
			if ((tag == 0x08) || (tag == 0x0b)
					|| (tag == 0x10) || (tag == 0x11)) {
				tag |= 0x20;	// Constructed, even STORED
			}
DPRINTF ("DEBUG: Stored element length set to %zd at offset %zd\n", elmlen, *offsetp);
		}
		if (addhdr) {
			if (bufend) {
				buf = *bufend;
				if (bitstr) {
					* --buf = 0x00;
				}
			}
			lenlen = 0;
			if (elmlen >= 0x80) {
				tmplen = elmlen;
				while (tmplen > 0) {
					if (bufend) {
						* -- buf = (tmplen & 0xff);
					}
					tmplen >>= 8;
					lenlen++;
				}
			}
			if (bufend) {
				* -- buf = (elmlen >= 0x80)? (lenlen|0x80): elmlen;
				* -- buf = tag;
				* bufend = buf;
DPRINTF ("DEBUG: Wrote %4d bytes to %p\n", 2 + lenlen, (void *)buf);
			}
			elmlen += 2 + lenlen;
		}
DPRINTF ("DEBUG: Adding %zd to length %zd, collected length is %zd\n", elmlen, totlen, elmlen + totlen);
		totlen += elmlen;
		if ((elmlen | totlen) & DER_DERLEN_FLAG_CONSTRUCTED) {
			return DER_DERLEN_ERROR;
		}
	// Special cases: DER_PACK_OPTIONAL has had the cmd value reset to 0x00
	// Note: The while loop terminates *after* processing the ENTER cmd
	} while (((cmd & DER_PACK_ENTER) == 0x00) && (*stxlen > 0));
DPRINTF ("DEBUG: Leaving recursive call der_pack_rec() with bufend=%p\n", (void *)(bufend? *bufend: 0));
	return totlen;
}


/* Pack a memory buffer following the indicated syntax, and using the elements
 * stored in the derray.  Enough memory is assumed to be available _before_
 * outbuf_end_opt; to find how large this buffer needs to be, it is possible to
 * call this function with outbuf_end_opt set to NULL.
 *
 * The return value is the same, regardless of outbuf_end_opt being NULL or not;
 * it is the length of the required output buffer.  When an error occurs, the
 * value 0 is returned, but that cannot happen on a second run on the same data
 * with only the outbuf_end_opt set to non-NULL.
 *
 * Please note once more that outbuf_end_opt, when non-NULL, points to the
 * first byte that is _not_ filled with the output DER data.  The value will
 * be decremented in this function for the bytes written.  This is quite
 * simply a more optimal strategy for DER production than anything else.
 * And yes, this is funny in an API, but you have the information and we would
 * otherwise ask you to pass it in, need to check it, you would then need to
 * check for extra error returns, ... so this is in fact simpler.
 *
 * Any parts of this structure that need to be prepacked are assumed to have
 * been prepared with der_prepack().  If your packaged structures show up as
 * Primitive where they should have been Constructed, then this is where to
 * look.
 */
size_t der_pack (const derwalk *syntax, const dercursor *derray,
					uint8_t *outbuf_end_opt) {
	int entered = 0;
	uint8_t cmd;
	int stxlen = 0;
	size_t derraylen = 0;
	size_t totlen = 0;
	while (cmd = syntax [stxlen], (entered > 0) || (cmd != DER_PACK_END)) {
		stxlen++;
		if (cmd & DER_PACK_ENTER) {
			if (cmd != DER_PACK_OPTIONAL) {
				entered++;
			}
		} else {
			if (cmd == DER_PACK_LEAVE) {
				entered--;
			} else if ((cmd != DER_PACK_CHOICE_BEGIN) && (cmd != DER_PACK_CHOICE_END)) {
				// Remaining commands store data (including ANY)
				derraylen++;
			}
		}
	}
DPRINTF ("DEBUG: Skipping %d syntax bytes, ending in %02x %02x %02x %02x | %02x\n", stxlen, syntax [-4], syntax [-3], syntax [-2], syntax [-1], syntax [0]);
	while (stxlen > 0) {
		totlen += der_pack_rec (syntax, &stxlen,
				outbuf_end_opt? &outbuf_end_opt: NULL,
				derray, &derraylen);
	}
	// One could assert() on derraylen == NULL, and syntax back to initial
	return totlen;
}
