/* Test the DER parser by exploring a certificate */

#include <stdlib.h>
#include <stdio.h>

#include <unistd.h>
#include <fcntl.h>

#include <quick-der/api.h>


// Certificate  ::=  SEQUENCE  {
// 	tbsCertificate       TBSCertificate,
// 	signatureAlgorithm   AlgorithmIdentifier,
// 	signatureValue       BIT STRING  }
//
// TBSCertificate  ::=  SEQUENCE  {
// 	version         [0]  EXPLICIT Version DEFAULT v1,
// 	serialNumber         CertificateSerialNumber,
// 	signature            AlgorithmIdentifier,
// 	issuer               Name,
// 	validity             Validity,
// 	subject              Name,
// 	subjectPublicKeyInfo SubjectPublicKeyInfo,
// 	issuerUniqueID  [1]  IMPLICIT UniqueIdentifier OPTIONAL,
// 	-- If present, version MUST be v2 or v3
// 	subjectUniqueID [2]  IMPLICIT UniqueIdentifier OPTIONAL,
// 	-- If present, version MUST be v2 or v3
// 	extensions      [3]  EXPLICIT Extensions OPTIONAL
// 	-- If present, version MUST be v3
// }
//
// Extensions  ::=  SEQUENCE SIZE (1..MAX) OF Extension
//
// Extension  ::=  SEQUENCE  {
//      extnID      OBJECT IDENTIFIER,
//      critical    BOOLEAN DEFAULT FALSE,
//      extnValue   OCTET STRING
//                  -- contains the DER encoding of an ASN.1 value
//                  -- corresponding to the extension type identified
//                  -- by extnID
//      }




/* The syntax parser, as it should be auto-generated one day.
 *
 * The parser enters as much of the structure as it can, basically taking
 * away anything that contains DER structure.  This stops ANY or ANY DEFINED BY
 * is used to describe a field's contents in a variable manner; you would have
 * to continue parsing yourself.  Similarly, when an OCTET STRING or BIT STRING
 * has DER-formatted contents that might vary.  When there is no variation,
 * you might actually ENTER these structures; note that special processing for
 * the BIT STRING then demands 0 remainder bits, after which it will enter one;
 * position after the head to skip the remainder bit count.
 */

derwalk pack_Certificate[] = {
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// Certificate SEQUENCE
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// TBSCertificate SEQUENCE
	DER_PACK_OPTIONAL,				// version is optional
	DER_PACK_ENTER | DER_TAG_CONTEXT (0),		// [0] EXPLICIT
	DER_PACK_STORE | DER_TAG_INTEGER,		// version
	DER_PACK_LEAVE,					// [0] EXPLICIT
	DER_PACK_STORE | DER_TAG_INTEGER,		// serialNumber
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// signature AlgIdentif
	DER_PACK_STORE | DER_TAG_OID,			// algorithm OID
	DER_PACK_ANY,					// parameters ANY DEFINED BY
	DER_PACK_LEAVE,					// signature AlgIdentif
	DER_PACK_STORE | DER_TAG_SEQUENCE,		// issuer Name (varsized)
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// validity SEQUENCE
	DER_PACK_CHOICE_BEGIN,				// utctime | genlztime
	DER_PACK_STORE | DER_TAG_UTCTIME,		// alt :- UTCtime
	DER_PACK_STORE | DER_TAG_GENERALIZEDTIME,	// alt :- GeneralizedTime
	DER_PACK_CHOICE_END,				// validity Validity
	DER_PACK_CHOICE_BEGIN,				// utctime | genlztime
	DER_PACK_STORE | DER_TAG_UTCTIME,		// alt :- UTCtime
	DER_PACK_STORE | DER_TAG_GENERALIZEDTIME,	// alt :- GeneralizedTime
	DER_PACK_CHOICE_END,				// Validity
	DER_PACK_LEAVE,					// validity SEQUENCE
	DER_PACK_STORE | DER_TAG_SEQUENCE,		// subject Name (varsized)
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// subjectPublicKeyInfo
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// algorithmIdentifier
	DER_PACK_STORE | DER_TAG_OID,			// algorithm
	DER_PACK_ANY,					// parameters ANY DEFINED BY
	DER_PACK_LEAVE,					// algorithmIdentifier
	DER_PACK_STORE | DER_TAG_BITSTRING,		// subjectPublicKey
	DER_PACK_LEAVE,					// subjectPublicKeyInfo
	DER_PACK_OPTIONAL,				// issuerUniqueID [1]
	DER_PACK_STORE | DER_TAG_CONTEXT (1),		// [1] IMPLICIT BITSTRING
	DER_PACK_OPTIONAL,				// subjectUniqueID [2]
	DER_PACK_STORE | DER_TAG_CONTEXT (2),		// [2] IMPLICIT BITSTRING
	DER_PACK_OPTIONAL,				// extensions [3]
	DER_PACK_ENTER | DER_TAG_CONTEXT (3),		// [3] EXPLICIT
	DER_PACK_STORE | DER_TAG_SEQUENCE,		// SEQUENCE OF Extension
	DER_PACK_LEAVE,					// [3] EXPLICIT
	DER_PACK_LEAVE,					// TBSCertificate SEQUENCE
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// sigAlg AlgIdentifier
	DER_PACK_STORE | DER_TAG_OID,			// algorithm
	DER_PACK_ANY,					// parameters ANY DEFINED BY
	DER_PACK_LEAVE,					// sigAlg AlgIdentifier
	DER_PACK_STORE | DER_TAG_BITSTRING,		// signatureValue BITSTR
	DER_PACK_LEAVE,					// Certificate SEQUENCE
	DER_PACK_END					// stop after SEQUENCE
};

derwalk pack_Extension [] = {
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// Extension ::= SEQUENCE {
	DER_PACK_STORE | DER_TAG_OID,			// extnID
	DER_PACK_OPTIONAL,
	DER_PACK_STORE | DER_TAG_BOOLEAN,		// critical
	DER_PACK_STORE | DER_TAG_OCTETSTRING,		// extnValue
	DER_PACK_LEAVE,					// }
	DER_PACK_END
};

/* Overlay structures, as they should be auto-generated some day */
struct ovly_Time {
	dercursor utcTime;
	dercursor generalTime;
};

struct ovly_Validity {
	struct ovly_Time notBefore;
	struct ovly_Time notAfter;
};

struct ovly_AlgorithmIdentifier {
	dercursor algorithm;
	dercursor parameters;
};

struct ovly_SubjectPublicKeyInfo {
	struct ovly_AlgorithmIdentifier algorithm;
	dercursor subjectPublicKey;
};

struct ovly_TBSCertificate {
	dercursor version;
	dercursor serialNumber;
	struct ovly_AlgorithmIdentifier signature;
	dercursor issuer;
	struct ovly_Validity validity;
	dercursor subject;
	struct ovly_SubjectPublicKeyInfo subjectPublicKeyInfo;
	dercursor issuerUniqueID;
	dercursor subjectUniqueID;
	dercursor extensions;
};

struct ovly_Certificate {
	struct ovly_TBSCertificate tbsCertificate;
	struct ovly_AlgorithmIdentifier signatureAlgorithm;
	dercursor signatureValue;
};

struct ovly_Extension {
	dercursor extnID;
	dercursor critical;
	dercursor extnValue;
};

derwalk path_rdn2type[] = {
	DER_WALK_ENTER | DER_TAG_SET,		// SET OF AttributeTypeAndValue
	DER_WALK_ENTER | DER_TAG_SEQUENCE,	// SEQUENCE { type, value }
	DER_WALK_ENTER | DER_TAG_OID,		// type OBJECT IDENTIFIER
	DER_WALK_END
};

derwalk path_rdn2value[] = {
	DER_WALK_ENTER | DER_TAG_SET,		// SET OF AttributeTypeAndValue
	DER_WALK_ENTER | DER_TAG_SEQUENCE,	// SEQUENCE { type, value }
	DER_WALK_SKIP  | DER_TAG_OID,		// type OBJECT IDENTIFIER
						// value ANY DEFINED BY type
	DER_WALK_END
};

/* Given the canonical data-representation for an OID, declare
 * a dercursor @p name that points to that data; used to declare
 * "constant cursors" for comparison purposes.
 */
#define OID_CURSOR(name, ...) \
        const uint8_t name##_derdata[] = { __VA_ARGS__ }; \
        const dercursor name = { (uint8_t *)name##_derdata, sizeof(name##_derdata) };

/* These are all OIDs under 1.2.840.113549.1.1., which name signature algorithms */
OID_CURSOR(rsa_with_nothing,
           0x2A, 0x86, 0x48, 0x86, 0xF7, 0x0D, 0x01, 0x01, 0x01)

OID_CURSOR(rsa_with_md5,
           0x2A, 0x86, 0x48, 0x86, 0xF7, 0x0D, 0x01, 0x01, 0x04)

OID_CURSOR(rsa_with_sha1,
           0x2A, 0x86, 0x48, 0x86, 0xF7, 0x0D, 0x01, 0x01, 0x05)

OID_CURSOR(rsa_with_sha224,
           0x2A, 0x86, 0x48, 0x86, 0xF7, 0x0D, 0x01, 0x01, 0x0e)

OID_CURSOR(rsa_with_sha256,
           0x2A, 0x86, 0x48, 0x86, 0xF7, 0x0D, 0x01, 0x01, 0x0b)

OID_CURSOR(rsa_with_sha384,
           0x2A, 0x86, 0x48, 0x86, 0xF7, 0x0D, 0x01, 0x01, 0x0c)

OID_CURSOR(rsa_with_sha512,
           0x2A, 0x86, 0x48, 0x86, 0xF7, 0x0D, 0x01, 0x01, 0x0d)

typedef struct { const dercursor *cursor; const char *label; } oid_label_assoc;
oid_label_assoc oid_labels[] = {
	{ &rsa_with_nothing, "RSA (no digest specified)" },
	{ &rsa_with_md5, "RSA with MD5 (unsafe)" },
	{ &rsa_with_sha1, "RSA with SHA1 (unsafe)" },
	{ &rsa_with_sha224, "RSA with SHA224" },
	{ &rsa_with_sha256, "RSA with SHA256" },
	{ &rsa_with_sha384, "RSA with SHA384" },
	{ &rsa_with_sha512, "RSA with SHA512" },
	{ NULL, NULL }
};

void print_oid (dercursor *oid) {
	/* Look up a named OID */
	const char *label = NULL;
	const oid_label_assoc *ola;
	for (ola = oid_labels; ola->label != NULL; ola++) {
		if (der_cmp(*oid, *(ola->cursor)) == 0)
		{
			label = ola->label;
			break;
		}
	}

	size_t oidlen = oid->derlen;
	uint8_t *oidptr = oid->derptr;
	uint32_t nextoid = 0;
	if (oidlen < 1) {
		printf ("BAD_OID");
		return;
	} else {
		uint8_t x = (*oidptr) / 40;
		uint8_t y = (*oidptr) % 40;
		if (x>2) {
			/* Special case: there are only initial arcs 0,1,2
			 * and initial arcs 0,1 have a constrained space
			 * underneath. Arc 2 has values from 0..51 and
			 * 999 (example), which can be confused (e.g. 2.40)
			 * with "initial arcs" > 2.
			 *
			 * Disambiguate those higher-numbered sub-arcs.
			 *
			 * Still doesn't handle 2.999, though.
			 */
			y += (x-2) * 40;
			x = 2;
		}
		printf ("%d.%d", x, y);
	}
	oidlen--;
	oidptr++;
	while (oidlen > 0) {
		nextoid <<= 7;
		nextoid |= (*oidptr) & 0x7f;
		if ((*oidptr & 0x80) == 0x00) {
			printf (".%d", nextoid);
			nextoid = 0;
		}
		oidptr++;
		oidlen--;
	}
	if (nextoid != 0x00) {
		printf (".LEFTOVER_%d", nextoid);
	}

	if (label != NULL)
	{
		printf(" (%s)", label);
	}
}

void hexdump (dercursor *crs) {
	dercursor here = *crs;
	while (here.derlen-- > 0) {
		printf (" %02x", *here.derptr++);
	}
}

int main (int argc, char *argv []) {
	int inf, otf;
	uint8_t buf [65537];
	size_t buflen;
	dercursor crs;
	dercursor iter;
	dercursor rdn;
	dercursor ext;
	struct ovly_Certificate certificate;
	struct ovly_Extension extension;
	int prsok;
	size_t rebuildlen;
	int i;

	memset (&certificate, 0x5A, sizeof (certificate));
	memset (&extension, 0x5A, sizeof (extension));
	if ((argc < 2) || (argc > 3)) {
		printf ("Usage: %s certfile.der [rebuildfile.der]\n", argv [0]);
		exit (1);
	}
	inf = open (argv [1], O_RDONLY);
	if (inf < 0) {
		fprintf (stderr, "Failed to open %s\n", argv [1]);
		close (inf);
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
	prsok = der_unpack (&crs, pack_Certificate, (dercursor *) &certificate, 1);
	switch (prsok) {
	case -1:
		perror ("Failed to unpack certificate");
		exit (1);
	case 0:
		// printf ("Parsing OK, found %zu bytes worth of subject data at 0x%016llx\n", crs.derlen, (uint64_t) crs.derptr);
		printf ("Detailed parsing OK for this Certificate\n");
		break;
	}

	if (der_isnull (&certificate.tbsCertificate.version)) {
		printf ("No version set (defaults to v1)\n");
	} else {
		printf ("Version is set to v%d\n", 1 + *certificate.tbsCertificate.version.derptr);
	}

	printf ("Serial number: ");
	hexdump (&certificate.tbsCertificate.serialNumber);
	printf ("\n");

	crs = certificate.tbsCertificate.issuer;
	printf ("There are %d RDNs in the issuer:\n", der_countelements (&crs));
	if (der_iterate_first (&crs, &iter)) do {
		// printf ("Iterator now at 0x%016llx spanning %zu\n", (uint64_t) iter.derptr, iter.derlen);
		// printf ("Iterator tag,len is 0x%02x,0x%02x\n", iter.derptr [0], iter.derptr [1]);
		rdn = iter;
		der_walk (&rdn, path_rdn2type);
		// printf ("RDNcursor #1 tag,len is 0x%02x,0x%02x,0x%02x\n", rdn.derptr [0], rdn.derptr [1],rdn.derptr [2]);
		print_oid (&rdn);
		rdn = iter;
		der_walk (&rdn, path_rdn2value);
		der_enter (&rdn); // Enter whatever DirectoryString it is
		// printf ("RDNcursor #2 tag,len is 0x%02x,0x%02x", rdn.derptr [0], rdn.derptr [1]);
		printf (" = \"%.*s\"\n", (int)rdn.derlen, rdn.derptr);
	} while (der_iterate_next (&iter));

	crs = der_isnull (&certificate.tbsCertificate.validity.notBefore.utcTime)?
		certificate.tbsCertificate.validity.notBefore.generalTime:
		certificate.tbsCertificate.validity.notBefore.utcTime;
	printf ("Validity.notBefore: %.*s\n", (int)crs.derlen, crs.derptr);
	crs = der_isnull (&certificate.tbsCertificate.validity.notAfter.utcTime)?
		certificate.tbsCertificate.validity.notAfter.generalTime:
		certificate.tbsCertificate.validity.notAfter.utcTime;
	printf ("Validity.notAfter:  %.*s\n", (int)crs.derlen, crs.derptr);

	crs = certificate.tbsCertificate.subject;
	printf ("There are %d RDNs in the subject:\n", der_countelements (&crs));
	if (der_iterate_first (&crs, &iter)) do {
		// printf ("Iterator now at 0x%016llx spanning %zu\n", (uint64_t) iter.derptr, iter.derlen);
		// printf ("Iterator tag,len is 0x%02x,0x%02x\n", iter.derptr [0], iter.derptr [1]);
		rdn = iter;
		der_walk (&rdn, path_rdn2type);
		// printf ("RDNcursor #1 tag,len is 0x%02x,0x%02x,0x%02x\n", rdn.derptr [0], rdn.derptr [1],rdn.derptr [2]);
		print_oid (&rdn);
		rdn = iter;
		der_walk (&rdn, path_rdn2value);
		der_enter (&rdn); // Enter whatever DirectoryString it is
		// printf ("RDNcursor #2 tag,len is 0x%02x,0x%02x", rdn.derptr [0], rdn.derptr [1]);
		printf (" = \"%.*s\"\n", (int)rdn.derlen, rdn.derptr);
	} while (der_iterate_next (&iter));

	printf ("Subject Public Key AlgorithmIdentifier: ");
	crs = certificate.tbsCertificate.subjectPublicKeyInfo.algorithm.algorithm;
	print_oid (&crs);
	printf ("\n                                       ");
	crs = certificate.tbsCertificate.subjectPublicKeyInfo.algorithm.parameters;
	hexdump (&crs);
	printf ("\n                                       ");
	crs = certificate.tbsCertificate.subjectPublicKeyInfo.subjectPublicKey;
	der_enter (&crs);
	hexdump (&crs);
	printf ("\n");

	crs = certificate.tbsCertificate.issuerUniqueID;
	if (!der_isnull (&crs)) {
		printf ("Issuer Unique ID:");
		hexdump (&crs);
		printf ("\n");
	}

	crs = certificate.tbsCertificate.subjectUniqueID;
	if (!der_isnull (&crs)) {
		printf ("Subject Unique ID:");
		hexdump (&crs);
		printf ("\n");
	}

	crs = certificate.tbsCertificate.extensions;
	printf ("There are %d extensions:\n", der_countelements (&crs));
	if (der_iterate_first (&crs, &iter)) do {
		// printf ("Iterator now at 0x%016llx spanning %zu\n", (uint64_t) iter.derptr, iter.derlen);
		// printf ("Iterator tag,len is 0x%02x,0x%02x\n", iter.derptr [0], iter.derptr [1]);
		ext = iter;
printf ("Extension size %zd bytes %02x %02x %02x %02x\n", ext.derlen, ext.derptr[0], ext.derptr[1], ext.derptr[2], ext.derptr[3]);
		prsok = der_unpack (&ext, pack_Extension, (dercursor *) &extension, 1);
		if (prsok != 0) {
			fprintf (stderr, "Failed to parse extension (%d)\n", prsok);
			continue;
		}
		printf ("Extension OID: ");
		print_oid (&extension.extnID);
		printf ("\nExtension critical: ");
		if (der_isnull (&extension.critical)) {
			printf ("FALSE (DEFAULT)\n");
		//TODO// Would be nice to have a DER boolean test macro / function
		} else if ((extension.critical.derlen > 0) && (*extension.critical.derptr)) {
			printf ("TRUE\n");
		} else {
			printf ("FALSE\n");
		}
		printf ("Extension contents:");
		hexdump (&extension.extnValue);
		printf ("\n");
	} while (der_iterate_next (&iter));

	//
	// Print the elemental length of the 16 certificate elements
	for (i=0; i<16; i++) {
		printf ("certificate [%2d].derlen = %zd\n", i, ((dercursor *) &certificate) [i].derlen);
	}

	//
	// Determine the length for re-composition
	rebuildlen = der_pack (pack_Certificate, (dercursor *) &certificate, NULL);
	if (rebuildlen != DER_DERLEN_ERROR) {
		printf ("To rebuild, we would need %zd bytes\n", rebuildlen);
	} else {
		fprintf (stderr, "Unable to determine the rebuild size for this certificate\n");
		exit (1);
	}

	//
	// Recompose the certificate for an output file if argv [2] has been defined
	if (argc == 3) {
		//
		// Construct the output certificate in a new buffer
		uint8_t rebuildbuf [rebuildlen]; // Daring: dynamic stack allocation
		der_pack (pack_Certificate, (dercursor *) &certificate, rebuildbuf + rebuildlen);
		printf ("TOTAL: Wrote %4zd bytes to 0x%016llx\n", rebuildlen, (unsigned long long) rebuildbuf);
		//
		// Save the rebuilt certificate to the named file
		otf = open (argv [2], O_RDWR | O_CREAT | O_TRUNC, 0644);
		if (otf < 0) {
			fprintf (stderr, "Failed to create output file %s\n", argv [2]);
			exit (1);
		}
		if (write (otf, rebuildbuf, rebuildlen) != rebuildlen) {
			fprintf (stderr, "Not all of the %zd bytes have been written to %s\n", rebuildlen, argv [2]);
			close (otf);
			exit (1);
		}
		close (otf);
		//
		// Compare the new certificate to the original one
		if (rebuildlen != buflen) {
			fprintf (stderr, "The rebuilt certificate is of a different size than the input\n");
			exit (1);
		}
		if (memcmp (buf, rebuildbuf, buflen) != 0) {
			fprintf (stderr, "The rebuilt certificate differs from the one input\n");
			exit (1);
		}
	}

	return 0;
}

