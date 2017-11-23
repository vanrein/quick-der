/* Data-packing function.
 *
 * From: Rick van Rein <rick@openfortress.nl>
 */


#include <stdint.h>

#include <quick-der/api.h>


/* 
 * Pack a BOOLEAN and return the number of bytes.  Do not pack a header
 * around it.  The function always packs to one byte, and encodes
 * TRUE as 0xff and FALSE as 0x00, as required by DER.  It interprets
 * the provided boolean value as TRUE when it is non-zero, as common
 * in C.
 *
 * Use the der_buf_bool_t as a pre-sized buffer for the encoded value.
 * This function always returns successfully.
 */
dercursor der_put_bool (uint8_t *der_buf_bool, int value) {
    dercursor retval;
    retval.derptr = der_buf_bool;
    retval.derlen = 1;
    *der_buf_bool = (value? 0xff: 0x00);
    return retval;
}

