#include <quick-der/api.h>


/* Update a cursor expression by walking into a DER-encoded ASN.1 structure.
 * The return value is -1 on error, and errno will be set accordinly, and the
 * cursor will not have been updated.  Otherwise, the return value is the number
 * of unprocessed bytes on the path, so 0 when the entire path was processed.
 * The count as non-error returns, so the cursor is updated.  Values higher than
 * 0 indicate where in the path a tag could not be found; this may be helpful in
 * learning about the structure that was being parsed, for example that an
 * OPTIONAL or CHOICE part was absent from the DER bytes.
 *
 * Paths are sequence of one-byte choices to be made.  These choices are tags,
 * because these are used by ASN.1 to decide on parsing choices to be made.
 * The one difference is the interpretation of the Primitive/Constructed bit: when
 * this is set to Primitive, the value will be skipped (even if it is Constructed)
 * and when set to Constructed, the value will be entered and interpreted as ASN.1
 * (even when it is setup as Primitive).
 *
 * In all the places where ASN.1 defines choices, such as CHOICE or OPTIONAL,
 * it enforces distinct tags from the various choices.  This can be used in a path
 * to skip such unknown parts in the encoding.
 *
 * When entering a BIT STRING, special treatment is implemented; the remaining
 * bits will have to be zero, and these are then skipped while entering the
 * remainder.  Note that this ensures that the byte-aligned DER structures are
 * properly packed into a bit-aligned BIT STRING container.
 */
int der_walk (dercursor *crs, const derwalk *path) {
	size_t len;
	uint8_t hlen;
	uint8_t tag;
	dercursor intcrs = *crs;
	int retval;
	int optional = 0;
	int choice = 0;
	while (*path != DER_WALK_END) {
		// see if a prefix signals optionality
		if (*path == DER_WALK_OPTIONAL) {
			optional = 1;	// For the duration of processing the following *path
			path++;
			if ((*path == DER_WALK_END) || (*path == DER_WALK_OPTIONAL)) {
				errno = EINVAL;
				return -1;
			}
		}
		// see if the current path element is a choice
		// between unknown elements that should be
		// skipped (except when it is optional, in which
		// case a match should be attempted)
		if (*path == DER_WALK_CHOICE) {
			choice = 1;
			// Special case: we advance beyond the path, so that we can check
			// the following element if the CHOICE is OPTIONAL
			path++;
			if ((*path == DER_WALK_END) || (*path == DER_WALK_CHOICE) || (*path == DER_WALK_OPTIONAL))  {
				errno = EINVAL;
				return -1;
			}
		}
		if (intcrs.derlen < 2) {
			if (intcrs.derlen == 0) {
				// Empty, so the path resolved only partially
				break;
			}
			// Something is wrong with the DER formatting
			errno = EBADMSG;
			return -1;
		}
		if (der_header (&intcrs, &tag, &len, &hlen)) {
			return -1;
		}
		// Now test if the tag matches that of the path;
		// choice and optional flags are processed and
		// make use of the ASN.1 guarantee that the
		// first tag that hits us is decisive on how to
		// proceed.  Although this may look loose, it is
		// in fact very accurate parsing, albeit that the
		// correctness is verified lazily, that is, only
		// inasfar as it is needed for the requested path.
		if (choice && !optional) {
			// this is just something unknown to skip;
			// that would even be true if it matched,
			// because the matching is deferred to
			// the next path element.
			intcrs.derptr += len;
			intcrs.derlen -= len;
			// the choice was matched; we already
			// skipped to next path item for choice==1
		} else if (((tag ^ *path) & DER_WALK_MATCHBITS) == 0x00) {
			// matched: now either enter of skip
			if ((*path) & DER_WALK_ENTER) {
				if (tag == (DER_WALK_ENTER | DER_TAG_BITSTRING)) {
					intcrs.derptr++;
					len--;
				}
				intcrs.derlen = len;
			} else {
				// not DER_WALK_ENTER, so DER_WALK_SKIP
				intcrs.derptr += len;
				intcrs.derlen -= len;
			}
			// matched: skip to next path item
			// if we had choice==1 and optional==1,
			// then we matched the part after the CHOICE
			// and so this applies in that case too.
			path++;
		} else if (optional) {
			// not matched the optional part: skip the data
			// and try the path element after the optional
			intcrs.derptr += len;
			intcrs.derlen -= len;
			// if the optional part was a choice, then we
			// are already at the next part and we are
			// now skipping the choice, for which we
			// already advanced path.  if the optional
			// part was not a choice, then path is at the
			// optional part, and we do need to skip that
			if (!choice) {
				path++;
			}
		} else {
			// not matched and not optional:
			// this is a parsing error
			errno = EBADMSG;
			return -1;
		}
		// Forget any optional flags for the processed *path
		optional = 0;
		choice = 0;
	}
	// Return 0 when done, or >0 with the remaining pathlen otherwise
	*crs = intcrs;
	retval = 0;
	while (path [retval] != DER_WALK_END) {
		retval++;
	}
	return retval;
}
