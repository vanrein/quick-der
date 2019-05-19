
#include <arpa2/quick-der.h>

/* Test if the appointed optional equals the default.  If so, set it
 * to the default/absent entry, .derptr==NULL and .derlen==0
 * This is useful prior to sending.
 */
void der_unput_default (dercursor *optional, dercursor default_value) {
	if (der_cmp (*optional, default_value) == 0) {
		memset (optional, 0, sizeof (dercursor));
	}
}
