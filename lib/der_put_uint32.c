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
    int ofs = 0;
    if (value & 0x80000000) {
        *der_buf_uint32 = 0x00;
        ofs = 1;
    }
    retval = der_put_int32 (der_buf_uint32 + ofs, (int32_t) value);
    retval.derptr -= ofs;
    retval.derlen += ofs;
    return retval;
}

