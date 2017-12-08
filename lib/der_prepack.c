#include <quick-der/api.h>


/* Pre-package the given DER array into the dercursor that is also provided.
 * This operation modifies the information stored in the destination field,
 * in a way that stops it from being interpreted properly in the usualy
 * manner, but it _does_ prepare it for der_pack() in a way that will include
 * the array of dercursor as a consecutive sequence, without any additional
 * headers, markers or other frills.
 *
 * This routine sets a special marker bit DER_DERLEN_FLAG_CONSTRUCTED in the
 * length field, so it can be recognised later on as an array reference.
 */
void der_prepack (const dercursor *derray, const size_t arraycount,
					derarray *prepacked_array) {
	prepacked_array->derray = (dernode *)derray;
	prepacked_array->dercnt = arraycount | DER_DERLEN_FLAG_CONSTRUCTED;
}

