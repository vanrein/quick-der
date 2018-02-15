/* data_putget.c -- Test der_conversions (see also der_format.py test)
 */


#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>

#include <quick-der/api.h>

int int_tests()
{
	uint8_t buffer[16];
	dercursor crs = der_put_int32(buffer, 2147483647);
	fprintf( stdout, "Length=%zu\nData=", crs.derlen );
	for (unsigned int i = 0; i < crs.derlen; ++i)
		fprintf( stdout, "%02x", crs.derptr[i] );
	fprintf( stdout, "\n");

	if ( crs.derlen != 4) {
		fprintf( stderr, "Bad length %zu\n", crs.derlen );
		return 0;
	}
	if ( crs.derptr != buffer ) {
		fprintf( stderr, "Derptr %p buffer %p\n", (void *)crs.derptr, (void *)buffer );
		return 0;
	}
	if ( crs.derptr[0] != 0x7f ) {
		fprintf( stderr, "Der data %02x != 0x7f\n", crs.derptr[0] );
		return 0;
	}

	return 1;
}

int uint_tests_31()
{
	uint8_t buffer[16];
	dercursor crs = der_put_uint32(buffer, 2147483647U);
	fprintf( stdout, "Length=%zu\nData=", crs.derlen );
	for (unsigned int i = 0; i < crs.derlen; ++i)
		fprintf( stdout, "%02x", crs.derptr[i] );
	fprintf( stdout, "\n");

	if ( crs.derlen != 4) {
		fprintf( stderr, "Bad length %zu\n", crs.derlen );
		return 0;
	}
	if ( crs.derptr != buffer ) {
		fprintf( stderr, "Derptr %p buffer %p\n", (void *)crs.derptr, (void *)buffer );
		return 0;
	}
	if ( crs.derptr[0] != 0x7f ) {
		fprintf( stderr, "Der data %02x != 0x7f\n", crs.derptr[0] );
		return 0;
	}

	return 1;
}

int uint_tests_32()
{
	uint8_t buffer[16];
	dercursor crs = der_put_uint32(buffer, 4294967295U);
	fprintf( stdout, "Length=%zu\nData=", crs.derlen );
	for (unsigned int i = 0; i < crs.derlen; ++i)
		fprintf( stdout, "%02x", crs.derptr[i] );
	fprintf( stdout, "\n");

	if ( crs.derlen != 5) {
		fprintf( stderr, "Bad length %zu\n", crs.derlen );
		return 0;
	}
	if ( crs.derptr != buffer ) {
		fprintf( stderr, "Derptr %p buffer %p\n", (void *)crs.derptr, (void *)buffer );
		return 0;
	}
	if ( crs.derptr[0] != 0x00 ) {
		fprintf( stderr, "Der data %02x != 0x00\n", crs.derptr[0] );
		return 0;
	}
	if ( crs.derptr[1] != 0xff ) {
		fprintf( stderr, "Der data %02x != 0xff\n", crs.derptr[1] );
		return 0;
	}

	return 1;
}

int main (int argc, char *argv []) {
	int ok = 1;

	if (!int_tests()) ok = 0;
	if (!uint_tests_31()) ok = 0;
	if (!uint_tests_32()) ok = 0;

	return ok ? 0: 1;
}
