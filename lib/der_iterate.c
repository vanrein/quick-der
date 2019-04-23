#include <arpa2/quick-der.h>


/* Given a dercursor, setup an iterator to run over its contained components.
 * While iterating, the initial iterator must continue to be supplied, without
 * modification to it.
 *
 * NOTE THE DIFFERENT CALLING CONVENTION FOR THIS FUNCTION!
 *
 * This function returns 1 upon success.  In case of failure such as no
 * elements found, it returns 0.
 *
 * To be sensitive to empty lists, use this as follows:
 *
 *	if (der_iterate_first (cnt, &iter)) do {
 *		...process entry...
 *	} while (der_iterate_next (&iter));
 *
 */
int der_iterate_first (const dercursor *container, dercursor *iterator) {
#if 0	/* Old code */
	*iterator = *container;
	der_enter (iterator);
	if (!der_isnonempty (iterator)) {
		return 0;
	}
	if (der_isconstructed (container)) {
		return 1;
	} else {
		return 0;
	}
#else
	*iterator = *container;
	return (iterator->derlen >= 2);
#endif
}

/* Step forward with an iterator.  This assumes an iterator that was
 * setup by der_iterate_first() and has since then not been modified.
 *
 * NOTE THE DIFFERENT CALLING CONVENTION FOR THIS FUNCTION!
 *
 * This function returns 1 upon success.  In case of failure, it
 * returns 0; in addition, it sets the nested iterator for zero
 * iterations.  A special case of error is when the container cursor is
 * not pointing to a Constructed element; in this case an error is returned
 * but the cursor will run over the contained elements when using the iterator.
 *
 * To be sensitive to errors, use this as follows:
 *
 *	if (der_iterate_first (cnt, &iter)) do {
 *		...process entry...
 *	} while (der_iterate_next (&iter));
 *
 */
int der_iterate_next (dercursor *iterator) {
	der_skip (iterator);
	return (iterator->derlen >= 2);
}


/* Count the number of elements available after entering the component
 * under the cursor.  This is useful to know how many elements exist inside
 * a SEQUENCE OF or SET OF, but may be used for other purposes as well.
 */
int der_countelements (dercursor *container) {
	int retval = 0;
	dercursor iter;
	if (der_iterate_first (container, &iter)) do {
		retval++;
	} while (der_iterate_next (&iter));
	return retval;
}
