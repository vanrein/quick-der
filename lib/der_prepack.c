#include <quick-der/api.h>


/* Pre-package the given DER array into the dercursor that is also provided.
 * This operation modifies the information stored in the destination field,
 * in a way that stops it from being interpreted properly in the usualy
 * manner, but it _does_ prepare it for der_pack() in a way that will include
 * the array of dercursor as a consecutive sequence, without any additional
 * headers, markers or other frills.
 */
void der_prepack (dercursor *derray, size_t arraycount, derarray *target) {
	target->derray = derray;
	target->dercnt = arraycount;
}

