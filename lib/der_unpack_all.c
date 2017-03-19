#include <quick-der/api.h>

#include <errno.h>


/* Unpack a structure, including any substructures that take the repetitive
 * forms SEQUENCE OF and SET OF.  These structures are not analysed by
 * standard der_unpack() because they lead to arrays, not structures, so
 * an overlay is difficult to make.  We use the union dernode, that is
 * initially filled with the .wire format with a standard .derptr and .derlen
 * combination covering the entire contents of the SEQUENCE/SET OF.  Then we
 * continue by figuring out how much memory is needed to unpack it for the
 * number of elements in the concrete data, we allocate it and unpack the
 * array, delivering the elements in the the .info variant of the union.
 * The .wire format is rendered unusable by that operation.
 *
 * The function is applied recursively, so anything in the repeating structure
 * that repeats will be treated in the same manner.  Note that although this
 * practice is unrestricted when looking at the grammar, it will always be
 * bounded in time due to the actual data that is bounded -- normal practice
 * for a parser with a cyclic grammar.
 *
 * This routine may be used, or you may instead prefer to use your own
 * routines to reach the same result.  It is up to you!  Note that the
 * routine starts with a plain der_unpack(), so you do not have to call
 * that initially.  The outarray will be used for that, but unlike what
 * der_unpack() does, it will point to arrays from any SEQUENCE/SET OF,
 * with .derray pointing to the first structure, and .dercnt holding the
 * number of such structures.  You are expected to know the structure to
 * expect, and cast the .derray pointer to that (der_structure *) and not
 * index more than .dercnt-1 elements of der_structure.
 *
 * The mpalloc() callback is used to allocate memory; the first argument
 * is set to the mpool parameter, and may represent a memory pool or any
 * other state/context that is of interest to mpalloc().  It is assumed
 * tht the state/context is used to cause all allocations to be freed at
 * once, even when der_unpack_all() fails it will not care for this!
 *
 * This routine returns 0 on success, or -1 on failure; in the latter
 * case, errno has been set to an indication of the detected problem.
 */
int der_unpack_all (dercursor *crs, const derwalk *syntax,
			dercursor *outarray,
			der_subparser_action *psub,
			int repeat, int cursors_per_repeat,
			void *mpool,
			void *mpalloc (void *mpool, size_t sz)) {
	if (der_unpack (crs, syntax, outarray, repeat) < 0) {
		return -1;
	}
	int r;
	for (r=0; r<repeat; r++) {
		while (psub->pck != NULL) {
			dernode *node = (dernode *) &outarray [psub->idx];
			int numelt = der_countelements (&node->wire);
			size_t needsz = psub->esz * numelt;
			psub++;
			dernode *subnodes = mpalloc (mpool, needsz * sizeof (dercursor));
			if (subnodes == NULL) {
				errno = ENOMEM;
				return -1;
			}
			if (der_unpack_all (&node->wire, psub->pck, (struct dercursor *) subnodes, psub->psub, numelt, psub->esz, mpool, mpalloc) < 0) {
				return -1;
			}
			node->info.dercnt = numelt;
			node->info.derray = subnodes;
		}
		outarray += cursors_per_repeat;
	}
	return 0;
}
