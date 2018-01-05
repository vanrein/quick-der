/* Data-packing function.
 *
 * From: Rick van Rein <rick@openfortress.nl>
 */


#include <stdint.h>

#include <quick-der/api.h>


/* 
 * Pack an UInt32 and return the number of bytes.  Do not pack a header
 * around it.  The function returns the number of bytes taken, even 0 is valid.
 */
dercursor der_put_uint32 (uint8_t *der_buf_uint32, uint32_t value) {
    dercursor retval;
    retval.derptr = der_buf_uint32;
    retval.derlen = 0;

    if (value & 0x80000000U) {
        *der_buf_uint32 = 0x00;
        retval.derlen = 1;
    }

    int shift = 24;
    while (shift >= 0) {
        if ((retval.derlen == 0) && (shift > 0)) {
            // Skip 0-padding on initial bytes
            uint32_t neutro = (value >> (shift - 1) ) & 0x000001ffU;
            if (neutro == 0) {
                shift -= 8;
                continue;
            }
        }
        der_buf_uint32 [retval.derlen] = (value >> shift) & 0xff;
        retval.derlen++;
        shift -= 8;
    }
    return retval;
}

