/* Test the DER parser by finding the certificates in PKINIT or KXOVER */

#include <stdlib.h>
#include <stdio.h>

#include <unistd.h>
#include <fcntl.h>

#include <quick-der/api.h>


/********** RFC 4556:

       PA-PK-AS-REQ ::= SEQUENCE {
          signedAuthPack          [0] IMPLICIT OCTET STRING,
                   -- Contains a CMS type ContentInfo encoded
                   -- according to [RFC3852].
                   -- The contentType field of the type ContentInfo
                   -- is id-signedData (1.2.840.113549.1.7.2),
                   -- and the content field is a SignedData.
                   -- The eContentType field for the type SignedData is
                   -- id-pkinit-authData (1.3.6.1.5.2.3.1), and the
                   -- eContent field contains the DER encoding of the
                   -- type AuthPack.
                   -- AuthPack is defined below.
          trustedCertifiers       [1] SEQUENCE OF
                      ExternalPrincipalIdentifier OPTIONAL,
                   -- Contains a list of CAs, trusted by the client,
                   -- that can be used to certify the KDC.
                   -- Each ExternalPrincipalIdentifier identifies a CA
                   -- or a CA certificate (thereby its public key).
                   -- The information contained in the
                   -- trustedCertifiers SHOULD be used by the KDC as
                   -- hints to guide its selection of an appropriate
                   -- certificate chain to return to the client.
          kdcPkId                 [2] IMPLICIT OCTET STRING
                                      OPTIONAL,
                   -- Contains a CMS type SignerIdentifier encoded
                   -- according to [RFC3852].
                   -- Identifies, if present, a particular KDC
                   -- public key that the client already has.
          ...
       }

*/


/********** RFC 3852:

      ContentInfo ::= SEQUENCE {
        contentType ContentType,
        content [0] EXPLICIT ANY DEFINED BY contentType }

      ContentType ::= OBJECT IDENTIFIER

      id-signedData OBJECT IDENTIFIER ::= { iso(1) member-body(2)
         us(840) rsadsi(113549) pkcs(1) pkcs7(7) 2 }

      SignedData ::= SEQUENCE {
        version CMSVersion,
        digestAlgorithms DigestAlgorithmIdentifiers,
        encapContentInfo EncapsulatedContentInfo,
        certificates [0] IMPLICIT CertificateSet OPTIONAL,
        crls [1] IMPLICIT RevocationInfoChoices OPTIONAL,
        signerInfos SignerInfos }

      CertificateSet ::= SET OF CertificateChoices

      CertificateChoices ::= CHOICE {
       certificate Certificate,
       extendedCertificate [0] IMPLICIT ExtendedCertificate, -- Obsolete
       v1AttrCert [1] IMPLICIT AttributeCertificateV1,       -- Obsolete
       v2AttrCert [2] IMPLICIT AttributeCertificateV2,
       other [3] IMPLICIT OtherCertificateFormat }

      OtherCertificateFormat ::= SEQUENCE {
       otherCertFormat OBJECT IDENTIFIER,
       otherCert ANY DEFINED BY otherCertFormat }

*/



derwalk path_KXoverASreq2certificateChoices [] = {
	DER_WALK_ENTER | DER_TAG_SEQUENCE,	// PA-PK-AS-REQ ::= SEQUENCE {...}
	DER_WALK_ENTER | DER_TAG_CONTEXT (0),	// signedAuthPack [0] IMPLICIT
	DER_WALK_ENTER | DER_TAG_SEQUENCE,	// ContentInfo ::= SEQUENCE {...}
	DER_WALK_SKIP  | DER_TAG_OID,		// contentType OBJECT IDENTIFIER
	DER_WALK_ENTER | DER_TAG_CONTEXT (0),	// content [0] EXPLICIT ANY ...
	DER_WALK_ENTER | DER_TAG_SEQUENCE,	// SignedData ::= SEQUENCE {...}
	DER_WALK_SKIP  | DER_TAG_INTEGER,	// version CMSVersion
	DER_WALK_SKIP  | DER_TAG_SET,		// digestAlgorithms SET OF ...
	DER_WALK_SKIP  | DER_TAG_SEQUENCE,	// encapContentInfo SEQUENCE {...}
	DER_WALK_END				// certificates [0] IMPLICIT
						//   SET OF CertificateChoices (!)
};

int main (int argc, char *argv []) {
	int inf;
	uint8_t buf [65537];
	size_t buflen;
	dercursor crs;
	dercursor iter;
	int prsok;
	int outfn = 2;
	if (argc < 2) {
		fprintf (stderr, "Usage: %s kxover-as-req.der [outcert0.der outcert1.der ...]\n", argv [0]);
		exit (1);
	}
	inf = open (argv [1], O_RDONLY);
	if (inf < 0) {
		fprintf (stderr, "Failed to open %s\n", argv [1]);
		exit (1);
	}
	buflen = read (inf, buf, sizeof (buf));
	close (inf);
	if ((buflen == -1) || (buflen == 0)) {
		fprintf (stderr, "Failed to read from %s\n", argv [1]);
		exit (1);
	}
	if (buflen == sizeof (buf)) {
		fprintf (stderr, "Certificate in %s too large\n", argv [1]);
		exit (1);
	}
	printf ("Parsing %zu bytes from %s\n", buflen, argv [1]);
	crs.derptr = buf;
	crs.derlen = buflen;
	prsok = der_walk (&crs, path_KXoverASreq2certificateChoices);
	switch (prsok) {
	case -1:
		perror ("Failed to find certificate set in KXOVER AS-Request");
		exit (1);
	case 0:
		printf ("Parsing OK, found %zu bytes worth of certificate set data at %p\n", crs.derlen, (void *) crs.derptr);
		break;
	default:
		printf ("Parsing ended with %d bytes left in pattern\n", prsok);
		exit (1);
	}
	printf ("Cursor is now at %p spanning %zu\n", (void *) crs.derptr, crs.derlen);
	if (der_iterate_first (&crs, &iter)) do {
		printf ("Iterator now at %p spanning %zu\n", (void *) iter.derptr, iter.derlen);
		printf ("Iterator tag,len is 0x%02x,0x%02x\n", iter.derptr [0], iter.derptr [1]);
		switch (iter.derptr [0] & 0xdf) {
		case DER_TAG_SEQUENCE:
			printf ("This is a certificate\n");
			if (outfn < argc) {
				int fout = open (argv [outfn], O_WRONLY);
				if (fout < 0) {
					fprintf (stderr, "Failed to open %s for writing, skipping it\n", argv [outfn]);
				} else if (write (fout, iter.derptr, iter.derlen) != iter.derlen) {
					fprintf (stderr, "Tried to save to %s, but not all bytes may have arrived\n", argv [outfn]);
					close (fout);
				} else {
					close (fout);
					printf ("Wrote this certificate to %s\n", argv [outfn]);
				}
				outfn++;
			} else {
				printf ("Provide an extra filename if you want me to save the certificate's DER format\n");
			}
			break;
		case DER_TAG_CONTEXT (0):
			printf ("This is an extendedCertificate (OBSOLETE)\n");
			break;
		case DER_TAG_CONTEXT (1):
			printf ("This is a v1AttrCert (OBSOLETE)\n");
			break;
		case DER_TAG_CONTEXT (2):
			printf ("This is a v2AttrCert\n");
			break;
		case DER_TAG_CONTEXT (3):
			printf ("This follows an OID-specified OtherCertificateFormat\n");
			break;
		}
	} while (der_iterate_next (&iter));
	return 0;
}

