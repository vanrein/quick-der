
#include <arpa2/quick-der.h>

/* When the optional is absent, set its value to the default.
 * Since Quick DER does not process default values, this must be
 * done manually.  The work can help to simplify programs, by
 * reducing the number of code paths and improve coverage.
 *
 * This function is not directly usable for CHOICE, which is
 * unrolled into a sequence of dercursor values that may or may
 * not have a value, but the multiplicity of the values is not
 * taken care of below.
 */
void der_put_default (dercursor *optional, dercursor default_value) {
	if (optional->derptr == NULL) {
		*optional = default_value;
	}
}
