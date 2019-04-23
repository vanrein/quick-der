/* This used to be the default include file for Quick DER.
 * The directory however, is better reserved just for output
 * from ASN.1 specifications.
 *
 * Instead, include <arpa2/quick-der.h> as we do below, after
 * having sent a compiler warning.
 */

#warning "DEPRECATED -- please include <arpa2/quick-der.h> instead of <quick-der/api.h>"
#include <arpa2/quick-der.h>
