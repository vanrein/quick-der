#include <arpa2/quick-der.h>

#include <errno.h>

#include "qd-int.h"


/* Unpack a DER structure based on its ASN.1 description, mapped to DER_PACK_
 * instructions.  This includes handling of OPTIONAL/DEFAULT and CHOICE syntax.
 * It also includes a DER_PACK_ENTER flag and DER_PACK_LEAVE instruction to
 * dive into a structure, as well as a DER_PACK_STORE flag to store the outcome
 * of a construct.
 *
 * When an error is encountered, this function returns NULL and sets errno to
 * a suitable error code.  In case of success, the return value gives the
 * new position from which the walk should continue.  It also updates the
 * number of elements in the output array in outctr.
 *
 * This routine takes a dercursor that it will move forward, up to a point
 * where parsing failed or was simply done.  In addition, it uses an
 * outarray and an outctr that is incremented while entries (NULL or other)
 * are filled in.
 *
 * This recursive routine processes a number of flags that modify its action:
 *  - choice implements a CHOICE of alternatives (possibly OPTIONAL) and
 *    will normally require precisely one of these alternatives to match;
 *  - optional indicates that the first DER element does not need to match
 *    because the syntax marks the *walk as OPTIONAL or having a DEFAULT;
 *  - optout indicates that the entries should be parsed and skipped, but
 *    only produce NULL entries due to CHOICE or OPTIONAL semantics.
 * Note that optout applies to any length of DER elements.  It is used to
 * support incrementing outctr while setting NULL values where otherwise
 * there might have been actual values, but the syntax context blocks that.
 */
static const derwalk *der_unpack_rec (dercursor *crs, const derwalk *walk,
				dercursor *outarray,
				int *outctr,
				bool choice,
				bool optional,
				bool optout) {
	uint8_t tag;
	uint8_t hlen;
	uint8_t terminal;
	uint8_t cmd;
	size_t len;
	dercursor newcrs;
	dercursor hdrcrs;
	bool chosen = false;
	bool optoutsub = optout;
DPRINTF ("DEBUG: Entering der_unpack_rec() at 0x%08lx\n", (intptr_t) walk);
	//
	// Decide on the terminal code and parse until that value
	if (choice) {
		terminal = DER_PACK_CHOICE_END;
	} else {
		terminal = DER_PACK_LEAVE;
	}
DPRINTF ("DEBUG: Start looping around for 0x%02x\n", terminal);
	while (*walk != terminal) {
DPRINTF ("DEBUG: Entering loop with choice=%d, optional=%d, optout=%d\n", choice, optional, optout);
		//
		// First detect the more complex structures for CHOICE and OPTIONAL
		if (*walk == DER_PACK_OPTIONAL) {
			//
			// Parse the prefix command for OPTION / DEFAULT
DPRINTF ("DEBUG: Encountered OPTIONAL\n");
			if (optional || choice) {
				// Nested OPTION, that can't be good
				// OPTION within CHOICE also signifies trouble
				errno = EBADMSG;
				return NULL;
			}
			optional = 1; // for the one next entry (may be ENTER)
			walk++;
		}
		if (*walk == DER_PACK_CHOICE_BEGIN) {
			//
			// Parse for a choice, leaving the OPTIONAL flag as is
DPRINTF ("DEBUG: Encountered CHOICE\n");
			if (choice) {
				// Nested CHOICE, that can't be good
				errno = EBADMSG;
				return NULL;
			}
DPRINTF ("DEBUG: Making recursive call because of CHOICE_BEGIN\n");
			walk = der_unpack_rec (crs, walk + 1,
					outarray, outctr,
					1, optional, optout);
			if (walk == NULL) {
				// Pass on inner error
				return NULL;
			}
DPRINTF ("DEBUG: Ended recursive call because of CHOICE_END\n");
			optional = false; // any 1 was used up by recursive CHOICE
DPRINTF ("DEBUG: Next command up is 0x%02x with %zd left\n", *walk, crs->derlen);
			continue;
		}
		//
		// Check if we have anything left to process at the DER cursor
		if (crs->derlen < 2) {
			if ((crs->derlen == 0) && (optional || optout)) {
				// Empty value is acceptable, skip ahead
				if ((*walk & DER_PACK_MATCHBITS) == DER_PACK_STORE) {
					memset (outarray + (*outctr)++,
							0,
							sizeof (dercursor));
					walk++;
					continue;
				}
			} else {
DPRINTF ("ERROR: Message size is only %zd and optional=%d, optout=%d\n", crs->derlen, optional, optout);
				errno = EBADMSG;
				return NULL;
			}
		}
		//
		// Pickup the tag and check its sanity
		hdrcrs = newcrs = *crs;
		if (der_header (&hdrcrs, &tag, &len, &hlen)) {
			return NULL;
		}
		//
		// Now decide how to handle the element.  If the OPTIONAL flag
		// is active, then a mismatch in the first attempted match is
		// accepted, but that will clear the OPTIONAL flag.  If the
		// OPTOUT flag is active, then everything happes as it would
		// normally happen, except that _STORE always stores NULL
		// values.  If the CHOICE flag is active, then a match is
		// processed and OPTOUT parsing is applied to all remaining
		// elements in the CHOICE (and the preceding OPTIONAL flag
		// applies to the whole CHOICE instead of a single element).
		// This assumes OPTION cannot occur immediately inside CHOICE.
		cmd = *walk++;
DPRINTF ("DEBUG: Instruction 0x%02x decodes 0x%02x size %zd of %zd\n", cmd, tag, len, hlen + len);
		if (chosen || optout) {
DPRINTF ("DEBUG: CHOICE was already made, or OPTIONAL was activated into opt-out\n");
			// Already matched CHOICE, or OPT-OUT is active,
			// so don't try matching anymore;
			// we chase on with optoutsub
			optoutsub = 1;
		} else if ((cmd == DER_PACK_ANY) || ((tag ^ cmd) & DER_PACK_MATCHBITS) == 0x00) {
DPRINTF ("DEBUG: Found a match\n");
			// We found a match
			optoutsub = optout;     // Hopefully store the value
			newcrs.derptr += hlen + len;	// Skip over match
			newcrs.derlen -= hlen + len;
			if (cmd == (DER_PACK_ENTER | DER_TAG_BITSTRING)) {
				// Check the remainder bits
				if (*hdrcrs.derptr != 0x00) {
					errno = EBADMSG;
					return NULL;
				}
				// Skip the remainder bits
				hdrcrs.derptr++;
				hdrcrs.derlen--;
			}
			if (choice) {
				// We matched a choice, so skip other choices
DPRINTF ("DEBUG: Moreover, found a matching choice\n");
				optoutsub = optout; // For the current element
				optout = 1;         // For   following elements
				chosen = 1;         // Bypass match of following
			}
		} else if (choice) {
DPRINTF ("DEBUG: Found a non-matching choice\n");
			// No match, but CHOICE flag permits that while choosing
			optoutsub = 1;	// suppress value copy for current elem
		} else if (optional) {
DPRINTF ("DEBUG: Mismatch forgiven because we're doing optional or optout recognition\n");
			// No match, but OPTIONAL flag permits that once
			optoutsub = 1;	// suppress value copy for current elem
		} else {
DPRINTF ("ERROR: Mismatch in either CHOICE nor OPTIONAL decoding parts\n");
			// No match and nothing helped to make that acceptable
			errno = EBADMSG;
			return NULL;
		}
		//
		// Now see if we need to ENTER a substructure.  If so, we will
		// use optoutsub for optout.  We never pass CHOICE because we
		// are past the choosing tag, and we also do not pass OPTIONAL
		// because that applied to the present tag.  The cursor passed
		// is newcrs, which is then also updated and later copied to crs.
		if (cmd & DER_PACK_ENTER) {
			if (!optoutsub) {
				newcrs = hdrcrs;
			}
			if (cmd == (DER_PACK_ENTER | DER_TAG_BITSTRING)) {
				if (*newcrs.derptr++ != 0x00) {
					errno = EBADMSG;
					return NULL;
				}
				newcrs.derlen--;
			}
DPRINTF ("DEBUG: Making recursive call because of ENTER bit with rest %zd\n", newcrs.derlen);
			walk = der_unpack_rec (&newcrs, walk,
					outarray, outctr,
					false, false, optoutsub);
			if (walk == NULL) {
				return NULL;
			}
DPRINTF ("DEBUG: Ended recursive call because of ENTER bit\n");
		//
		// The alternative to _ENTER is to _STORE the current value.
		// Whether we actually do that, or store a NULL value instead,
		// is determined by the opt-out choice for the current element,
		// so by optoutsub.
		//
		// Even when we retry the same DER code to another walking step,
		// then we want to store the walk-guided syntax component.
		} else if (optoutsub) {
			// We opt out on this elem, so we store a NULL cursor
DPRINTF ("DEBUG: Opting out of output value #%d, setting it to NULL cursor\n", *outctr);
			memset (outarray + (*outctr)++,
					0,
					sizeof (dercursor));
		} else {
			// We store the DER value found
DPRINTF ("DEBUG: Storing output value #%d with %zd bytes 0x%02x, 0x%02x, 0x%02x, ...\n", *outctr, crs->derlen, crs->derptr [0], crs->derptr [1], crs->derptr [2]);
			//TODO:COUNTDOWNLENGTHS// outarray [ (*outctr)++ ] = *crs;
			if (cmd == DER_PACK_ANY) {
				outarray [ (*outctr) ].derptr = crs->derptr;
				outarray [ (*outctr) ].derlen = hlen + len;
			} else {
				outarray [ (*outctr) ].derptr = hdrcrs.derptr;
				outarray [ (*outctr) ].derlen = len;
			}
			(*outctr)++;
		}
		//
		// If this is not a CHOICE, then any OPTIONAL flag is cleared;
		// the prefix serves at most one element, although that can be
		// extended with the _ENTER flag to a range of elements.  But
		// at this point, the use of the OPTIONAL bit has played out.
		if (!choice) {
			optional = 0;
		}
		//
		// Update the visible DER cursor, making it either go back to
		// what we just tried to match or advance to the next DER element
		*crs = newcrs;
DPRINTF ("DEBUG: Considering another loop-around for 0x%02x on 0x%02x with %zd left\n", terminal, *walk, crs->derlen);
	}
DPRINTF ("DEBUG: Ended looping around for 0x%02x with %zd left\n", terminal, crs->derlen);
	//
	// Skip past the detected terminal on the walk
	walk++;
	//
	// If this is a CHOICE and it is not OPTIONAL, then failure if all
	// attempted matches failed.  Note that OPTOUT is another matter; it
	// details surrounding OPTIONALs, which are not of influence on
	// the CHOICE being subjected to a local OPTIONAL prefix.
	// Note that the choice flag is cleared as soon as it matches.
	if (choice && (!chosen) && (!optional) && (!optout)) {
DPRINTF ("ERROR: Ended a CHOICE without choosing, even though it is not OPTIONAL\n");
		errno = EBADMSG;
		return NULL;
	}
	//
	// It is also an error if we were looping until DER_PACK_LEAVE but
	// we did not actually run into the end of the DER encoding.
#if 0
	//TODO// This is not working because there may be surroundings continuing
	if ((terminal == DER_PACK_LEAVE) && (crs->derlen != 0)) {
		errno = EBADMSG;
		return NULL;
	}
#endif
	//
	// Properly ended with DER_PACK_LEAVE, so report success
DPRINTF ("DEBUG: Leaving  der_unpack_rec() at 0x%08lx\n", (intptr_t) walk);
	return walk;
}


int der_unpack (dercursor *crs, const derwalk *syntax,
			dercursor *outarray, int repeats) {
	int outctr = 0;
	//TODO:WHY// if ((*syntax & DER_PACK_ENTER) == 0x00) {
		//TODO:WHY// errno = EBADMSG;
		//TODO:WHY// return -1;
	//TODO:WHY// }
	while (repeats-- > 0) {
		if (der_unpack_rec (crs, syntax,
				outarray, &outctr,
				false, false, false) == NULL) {
			return -1;
		}
	}
	return 0;
}
