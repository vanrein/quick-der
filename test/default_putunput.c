
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>

#include <arpa2/quick-der.h>


dercursor abba = {
	.derptr = "ABBA",
	.derlen = 4
};

dercursor ledz = {
	.derptr = "LED Zeppelin",
	.derlen = 12
};

dercursor ledy = {
	.derptr = "LED Zeppelinny",
	.derlen = 12
};

dercursor null = {
	.derptr = NULL,
	.derlen = 0
};

dercursor band;


int errors = 0;


void maybe (dercursor dflt) {
	der_put_default (&band, dflt);
}


void notbe (dercursor dflt) {
	der_unput_default (&band, dflt);
}


void should (dercursor target) {
	static int testnr = 0;
	if (der_cmp (band, target) != 0) {
		errors++;
		fprintf (stderr, "Test #%d failed; found \"%.*s\", expected \"%.*s\"\n",
			testnr, band.derlen, band.derptr, target.derlen, target.derptr);
	}
	testnr++;
}


int main (int argc, char *argv []) {
	errors = 0;
	band = null;
	should (null);
	maybe (abba);
	should (abba);
	maybe (abba);
	should (abba);
	maybe (ledz);
	should (abba);
	notbe (ledz);
	should (abba);
	notbe (abba);
	should (null);
	maybe (ledz);
	should (ledz);
	should (ledy);
	notbe (ledy);
	should (null);
	maybe (ledy);
	should (ledy);
	should (ledz);
	maybe (abba);
	should (ledy);
	should (ledz);
	maybe (ledz);
	should (ledy);
	should (ledz);
	maybe (null);
	should (ledz);
	should (ledy);
	notbe (ledz);
	should (null);
	exit (errors);
}
