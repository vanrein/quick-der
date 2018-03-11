/* bitstring_putget.c -- Test der_put_bitstring_* followed by der_get_bitstring_*
 *
 * From: Rick van Rein <rick@openfortress.nl>
 */


#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>

#include <quick-der/api.h>


/*
 * The tests send an increasingly large portion of a 32-bit word.  These are
 * created and tested in both ways, per bit and per byte, where both unpackers
 * validate the output from each of the packers.  Attempts are made to access
 * flags at unwarranted offsets, namely -32, -8, -1, +1, +2, +8, +32 bits out of
 * range, and it is tested that these fail.  Tests always precede the actual
 * writes.  We use internal knowledge to clear out the contents of each word
 * before testing, by setting it to 0xAA values.
 *
 * All test functions return 0 on success, -1 on failure.
 */


#define VALID 0
#define INVAL 1
#define WRONG 2

int clearbuf (dercursor *bsbuf, size_t numbits) {
	//DEBUG// fprintf (stderr, "Setting derlen to %zd for numbits %zd\n", 1 + ((numbits+7)>>3), numbits);
	bsbuf->derlen = 1 + ((numbits + 7) >> 3);
	//DEBUG// fprintf (stderr, "Setting first byte to 0x%02x\n", (int) (numbits & 0x07));
	bsbuf->derptr [0] = ((~numbits) + 1) & 0x07;
	//DEBUG// fprintf (stderr, "Setting %zd bytes to 0xAA\n", bsbuf->derlen-1);
	if (bsbuf->derlen-1 > 0) {
		memset (bsbuf->derptr+1, 0xAA, bsbuf->derlen-1);
	}
	return 0;
}

#define TESTBYTES 4
#define TESTBITS (TESTBYTES*8)
uint8_t testbytes [TESTBYTES] = { 0x3C, 0xFB, 0x01, 0xB0 };

uint8_t byte2test (size_t bytenr) {
	return testbytes [bytenr];
}

bool bit2test (size_t bitnr) {
	return (testbytes [bitnr >> 3] >> (7 - (bitnr & 0x07)) ) & 0x01;
}

int setbyte (int validity, dercursor bsbuf, size_t numbits, ssize_t bytenr, uint8_t value) {
	// bool invalid = (bytenr < 0) || (bytenr * 8 - 7 > numbits) ||
	// 	( (bytenr - 1 == (numbits >> 3)) && ( 0 != (value & (0x7f >> (7 - (numbits & 0x07))))));
	int test = der_put_bitstring_by_eight (bsbuf, bytenr, value);
	if ((test == 0) && (validity==INVAL)) {
		fprintf (stderr, "Write should have been invalid: bytenr %zd, numbits %zd, value 0x%02x\n",
				bytenr, numbits, value);
		return -1;
	}
	if ((test != 0) && (validity!=INVAL)) {
		fprintf (stderr, "Write should have been valid: bytenr %zd, numbits %zd, value 0x%02x\n",
				bytenr, numbits, value);
		return -1;
	}
	return 0;
}

int getbyte (int validity, dercursor bsbuf, size_t numbits, ssize_t bytenr, uint8_t expected) {
	// bool invalid = (bytenr < 0) || (bytenr * 8 - 7 > numbits);
	int test = der_get_bitstring_by_eight (bsbuf, bytenr, NULL);
	if ((test == 0) && (validity==INVAL)) {
		fprintf (stderr, "Read should have been invalid: bytenr %zd, numbits %zd, expected 0x%02x\n",
				bytenr, numbits, expected);
		return -1;
	}
	if ((test != 0) && (validity!=INVAL)) {
		fprintf (stderr, "Read should have been valid: bytenr %zd, numbits %zd, expected 0x%02x\n",
				bytenr, numbits, expected);
		return -1;
	}
	uint8_t gotten = 0x00;
	int done = der_get_bitstring_by_eight (bsbuf, bytenr, &gotten);
	if (test != done) {
		fprintf (stderr, "Read validity inconsistent: bytenr %zd, numbits %zd, expected 0x%02x\n",
				bytenr, numbits, expected);
		return -1;
	}
	if ((gotten != expected) && (validity==VALID)) {
		fprintf (stderr, "Read back surprise: bytenr %zd, expected 0x%02x, gotten 0x%02x\n",
				bytenr, expected, gotten);
		return -1;
	}
	if ((gotten == expected) && (validity==WRONG)) {
		fprintf (stderr, "Read back too good: bytenr %zd, expected 0x%02x, gotten 0x%02x\n",
				bytenr, expected, gotten);
		return -1;
	}
	return 0;
}

int setbit (int validity, dercursor bsbuf, size_t numbits, ssize_t bitnr, bool value) {
	// bool invalid = (bitnr < 0) || (bitnr >= numbits);
	int test = der_put_bitstring_flag (bsbuf, bitnr, value);
	if ((test == 0) && (validity==INVAL)) {
		fprintf (stderr, "Write should have been invalid: bitnr %zd, numbits %zd, value %s\n",
				bitnr, numbits, value?"TRUE":"FALSE");
		return -1;
	}
	if ((test != 0) && (validity!=INVAL)) {
		fprintf (stderr, "Write should have been valid: bitnr %zd, numbits %zd, value %s\n",
				bitnr, numbits, value?"TRUE":"FALSE");
		return -1;
	}
	return 0;
}

int getbit (int validity, dercursor bsbuf, size_t numbits, ssize_t bitnr, bool expected) {
	// bool invalid = (bitnr < 0) || (bitnr >= numbits);
	int test = der_get_bitstring_flag (bsbuf, bitnr, NULL);
	if ((test == 0) && (validity==INVAL)) {
		fprintf (stderr, "Read should have been invalid: bitnr %zd, numbits %zd, expected %s\n",
				bitnr, numbits, expected?"TRUE":"FALSE");
		return -1;
	}
	if ((test != 0) && (validity!=INVAL)) {
		fprintf (stderr, "Read should have been valid: bitnr %zd, numbits %zd, expected %s\n",
				bitnr, numbits, expected?"TRUE":"FALSE");
		return -1;
	}
	bool gotten = !expected;
	int done = der_get_bitstring_flag (bsbuf, bitnr, &gotten);
	if (test != done) {
		fprintf (stderr, "Read validity inconsistent: bitnr %zd, numbits %zd, expected %s\n",
				bitnr, numbits, expected?"TRUE":"FALSE");
		return -1;
	}
	if ((gotten != expected) && (validity==VALID)) {
		fprintf (stderr, "Read back surprise: bitnr %zd, expected %s, gotten %s\n",
				bitnr, expected?"TRUE":"FALSE", gotten?"TRUE":"FALSE");
		return -1;
	}
	if ((gotten == expected) && (validity!=VALID)) {
		fprintf (stderr, "Read back too good: bitnr %zd, expected %s, gotten %s\n",
				bitnr, expected?"TRUE":"FALSE", gotten?"TRUE":"FALSE");
		return -1;
	}
	return 0;
}


int rangeset_bits (dercursor bsbuf, size_t numbits) {
	fprintf (stderr, ">>> rangeset_bits (bs,%zd);\n", numbits);
	int trouble = 0;
	// Try known-bad offsets
	trouble += setbit (INVAL, bsbuf, numbits, -32,0);
	trouble += setbit (INVAL, bsbuf, numbits, -8, 0);
	trouble += setbit (INVAL, bsbuf, numbits, -1, 0);
	// Now set all those good values
	size_t i;
	for (i=0; i<numbits; i++) {
		bool b = bit2test (i);
		trouble += setbit (VALID, bsbuf, numbits, i, b);
	}
	// Try known-bad offsets
	trouble += setbit (INVAL, bsbuf, numbits, numbits+0, 0);
	trouble += setbit (INVAL, bsbuf, numbits, numbits+1, 0);
	trouble += setbit (INVAL, bsbuf, numbits, numbits+7, 0);
	trouble += setbit (INVAL, bsbuf, numbits, numbits+32,0);
	// Return collective trouble
	return trouble;
}

int rangeget_bits (dercursor bsbuf, size_t numbits) {
	fprintf (stderr, ">>> rangeget_bits (bs,%zd);\n", numbits);
	int trouble = 0;
	// Try known-bad offsets
	trouble += getbit (INVAL, bsbuf, numbits, -32,0);
	trouble += getbit (INVAL, bsbuf, numbits, -8, 0);
	trouble += getbit (INVAL, bsbuf, numbits, -1, 0);
	// Now get all those good values
	size_t i;
	for (i=0; i<numbits; i++) {
		uint8_t b = bit2test (i);
		fprintf (stderr, "Expecting value %s at %zd\n", b?"TRUE":"FALSE", i);
		trouble += getbit (WRONG, bsbuf, numbits, i, !b);
		trouble += getbit (VALID, bsbuf, numbits, i,  b);
	}
	// Try known-bad offsets
	trouble += getbit (INVAL, bsbuf, numbits, numbits+0, 0);
	trouble += getbit (INVAL, bsbuf, numbits, numbits+1, 0);
	trouble += getbit (INVAL, bsbuf, numbits, numbits+7, 0);
	trouble += getbit (INVAL, bsbuf, numbits, numbits+32,0);
	// Return collective trouble
	return trouble;
}


int rangeset_bytes (dercursor bsbuf, size_t numbits) {
	fprintf (stderr, ">>> rangeset_bytes (bs,%zd);\n", numbits);
	int trouble = 0;
	size_t numbytes = (numbits+7) >> 3;
	// Try known-bad offsets
	trouble += setbyte (INVAL, bsbuf, numbits, -4, 0);
	trouble += setbyte (INVAL, bsbuf, numbits, -1, 0);
	// Now set all those good values (whole bytes)
	size_t i;
	uint8_t b;
	if (numbytes > 0) {
		for (i=0; i<numbytes-1; i++) {
			b = byte2test (i);
			trouble += setbyte (VALID, bsbuf, numbits, i, b);
		}
	}
	// More good and bad values (partial bytes)
	if (numbits > 0) {
		b = byte2test (numbytes-1) & 0xff & (0xff << (((~numbits) + 1) & 0x07));
		fprintf (stderr, "Reduced 0x%02x to 0x%02x for %zd bits in %zd bytes\n", byte2test (numbytes-1), b, numbits, numbytes);
		trouble += setbyte (VALID, bsbuf, numbits, numbytes-1, b);
		for (i=0; i < (((~numbits) + 1) & 0x07); i++) {
			uint8_t extravaganza = 0x01 << i;
			fprintf (stderr, "Extravaganza for %zd extra bits is 0x%02x over 0x%02x\n", i+1, extravaganza, b);
			trouble += setbyte (INVAL, bsbuf, numbits, numbytes-1, b | extravaganza);
		}
	}
	// Try known-bad offsets
	trouble += setbyte (INVAL, bsbuf, numbits, numbytes+0, 0);
	trouble += setbyte (INVAL, bsbuf, numbits, numbytes+1, 0);
	trouble += setbyte (INVAL, bsbuf, numbits, numbytes+7, 0);
	trouble += setbyte (INVAL, bsbuf, numbits, numbytes+32, 0);
	// Return collective trouble
	return trouble;
}

int rangeget_bytes (dercursor bsbuf, size_t numbits) {
	fprintf (stderr, ">>> rangeget_bytes (bs,%zd);\n", numbits);
	int trouble = 0;
	size_t numbytes = (numbits+7) >> 3;
	// Try known-bad offsets
	trouble += getbyte (INVAL, bsbuf, numbits, -4, 0);
	trouble += getbyte (INVAL, bsbuf, numbits, -1, 0);
	// Now get all those good values (whole bytes)
	size_t i;
	uint8_t b;
	if (numbytes > 0) {
		for (i=0; i<numbytes-1; i++) {
			b = byte2test (i);
			fprintf (stderr, "Testing byte 0x%02x at byte offset %zd\n", b, i);
			trouble += getbyte (VALID, bsbuf, numbits, i, b);
		}
	}
	// More good and bad values (partial bytes)
	if (numbits > 0) {
		b = byte2test (numbytes-1) & 0xff & (0xff << (((~numbits) + 1) & 0x07));
		fprintf (stderr, "Reduced 0x%02x to 0x%02x for %zd bits in %zd bytes\n", byte2test (numbytes-1), b, numbits, numbytes);
		trouble += getbyte (VALID, bsbuf, numbits, numbytes-1, b);
		//DEBUG// fprintf (stderr, "Gotten reduced outcome against 0x%02x\n", b);
		for (i=0; i < (((~numbits) + 1) & 0x07); i++) {
			uint8_t extravaganza = 0x01 << i;
			fprintf (stderr, "Extravaganza for %zd extra bits is 0x%02x over 0x%02x\n", i+1, extravaganza, b);
			trouble += getbyte (WRONG, bsbuf, numbits, numbytes-1, b | extravaganza);
		}
	}
	// Try known-bad offsets
	trouble += getbyte (INVAL, bsbuf, numbits, numbytes+0, 0);
	trouble += getbyte (INVAL, bsbuf, numbits, numbytes+1, 0);
	trouble += getbyte (INVAL, bsbuf, numbits, numbytes+7, 0);
	trouble += getbyte (INVAL, bsbuf, numbits, numbytes+32,0);
	// Return collective trouble
	return trouble;
}


int bitstring_tests (void) {
	int trouble = 0;
	size_t numbits;
	uint8_t bsplayground [TESTBYTES+2];
	dercursor bs = { .derptr = bsplayground, .derlen = TESTBYTES+1 };
	for (numbits=0; numbits <= TESTBITS; numbits++) {
		fprintf (stderr, "Running tests on %zd bits\n", numbits);
		// Build up structure with bits
		trouble += clearbuf      (&bs, numbits);
		trouble += rangeset_bits  (bs, numbits);
		trouble += rangeget_bits  (bs, numbits);
		trouble += rangeget_bytes (bs, numbits);
		// Build up structure with bytes
		trouble += clearbuf      (&bs, numbits);
		trouble += rangeset_bytes (bs, numbits);
		trouble += rangeget_bytes (bs, numbits);
		trouble += rangeget_bits  (bs, numbits);
	}
	// Return collective trouble
	return trouble;
}


int main (int argc, char *argv []) {

	int ok = 1;

	if (bitstring_tests() != 0) ok = 0;

	return ok? 0: 1;
}

