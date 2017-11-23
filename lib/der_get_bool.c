/* Data-unpacking function.
 *
 * From: Rick van Rein <rick@openfortress.nl>
 */


#include <stdint.h>

#include <quick-der/api.h>


/* 
 * Unpack a BOOLEAN and set its value to 0 for FALSE, or 1 for TRUE.
 *
 * Do accept all BER encodings of BOOLEAN, meaning, any non-zero byte is
 * interpreted as TRUE, even though DER is more explicit with 0xff.
 *
 * Upon encountering an error, return -1; success decoding as BER is 0.
 * Even when an error is reported, the value is updated, so it is safe
 * to ignore the error in order to facilitate a more lenient parser
 * even than BER.  Even when excessive in size, the value is set to
 * FALSE only when all bytes (possibly zero bytes) are 0x00.
 */
int der_get_bool (dercursor crs, int *valp) {
    int i;
    *valp = 0;
    for (i=0; i<crs.derlen; i++) {
        if (crs.derptr [i]) {
            *valp = 1;
            break;
        }
    }
    return (crs.derlen == 1)? 0: -1;
}

