/* Data-packing function.
 *
 * From: Rick van Rein <rick@openfortress.nl>
 */


#include <stdint.h>

#include <arpa2/quick-der.h>


/* 
 * Pack an Int32 and return the number of bytes.  Do not pack a header
 * around it.  The function returns the number of bytes taken, even 0 is valid.
 */
dercursor der_put_int32 (uint8_t *der_buf_int32, int32_t value) {
    dercursor retval;
    int shift = 24;
    retval.derptr = der_buf_int32;
    retval.derlen = 0;
    while (shift >= 0) {
        if ((retval.derlen == 0) && (shift > 0)) {
            // Skip sign-extending initial bytes
            uint32_t neutro = (value >> (shift - 1) ) & 0x000001ff;
            if ((neutro == 0x000001ff) || (neutro == 0x00000000)) {
                shift -= 8;
                continue;
            }
        }
        der_buf_int32 [retval.derlen] = (value >> shift) & 0xff;
        retval.derlen++;
        shift -= 8;
    }
    return retval;
}

