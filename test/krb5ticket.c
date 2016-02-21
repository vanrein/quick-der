
#include <stdlib.h>


#include <quick-der/api.h>



/*
 * Ticket          ::= [APPLICATION 1] SEQUENCE {
 *         tkt-vno         [0] INTEGER (5),
 *         realm           [1] Realm,
 *         sname           [2] PrincipalName,
 *         enc-part        [3] EncryptedData -- EncTicketPart
 * }
 *
 * Realm           ::= KerberosString
 *
 * PrincipalName   ::= SEQUENCE {
 *         name-type       [0] Int32,
 *         name-string     [1] SEQUENCE OF KerberosString
 * }
 *
 * EncryptedData   ::= SEQUENCE {
 *         etype   [0] Int32 -- EncryptionType --,
 *         kvno    [1] UInt32 OPTIONAL,
 *         cipher  [2] OCTET STRING -- ciphertext
 * }
 *
 * EncTicketPart   ::= [APPLICATION 3] SEQUENCE {
 *         flags                   [0] TicketFlags,
 *         key                     [1] EncryptionKey,
 *         crealm                  [2] Realm,
 *         cname                   [3] PrincipalName,
 *         transited               [4] TransitedEncoding,
 *         authtime                [5] KerberosTime,
 *         starttime               [6] KerberosTime OPTIONAL,
 *         endtime                 [7] KerberosTime,
 *         renew-till              [8] KerberosTime OPTIONAL,
 *         caddr                   [9] HostAddresses OPTIONAL,
 *         authorization-data      [10] AuthorizationData OPTIONAL
 * }
 *
 * TicketFlags     ::= KerberosFlags
 *
 * EncryptionKey   ::= SEQUENCE {
 *         keytype         [0] Int32 -- actually encryption type --,
 *         keyvalue        [1] OCTET STRING
 * }
 *
 * TransitedEncoding       ::= SEQUENCE {
 *         tr-type         [0] Int32 -- must be registered --,
 *         contents        [1] OCTET STRING
 * }
 *
 * KerberosTime    ::= GeneralizedTime -- with no fractional seconds
 *
 * AuthorizationData       ::= SEQUENCE OF SEQUENCE {
 *         ad-type         [0] Int32,
 *         ad-data         [1] OCTET STRING
 * }
 *
 */

derwalk pack_Ticket [] = {
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// Ticket
	DER_PACK_ENTER | DER_TAG_CONTEXT (0),		// [0] tkt-vno
	DER_PACK_STORE | DER_TAG_INTEGER,		// tkt-vno (5)
	DER_PACK_LEAVE,					// [0] tkt-vno
	DER_PACK_ENTER | DER_TAG_CONTEXT (1),		// [1] realm
	DER_PACK_STORE | DER_TAG_GENERALSTRING,		// realm
	DER_PACK_LEAVE,					// [1] realm
	DER_PACK_ENTER | DER_TAG_CONTEXT (2),		// [2] sname
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// sname
	DER_PACK_ENTER | DER_TAG_CONTEXT (0),		// [0] name-type
	DER_PACK_STORE | DER_TAG_INTEGER,		// name-type Int32
	DER_PACK_STORE | DER_TAG_SEQUENCE,		// SEQUENCE OF GeneralString
	DER_PACK_LEAVE,					// [0] name-type
	DER_PACK_LEAVE,					// sname
	DER_PACK_LEAVE,					// [2] sname
	DER_PACK_ENTER | DER_TAG_CONTEXT (3),		// [3] enc-part
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// enc-part
	DER_PACK_ENTER | DER_TAG_CONTEXT (0),		// [0] etype
	DER_PACK_STORE | DER_TAG_INTEGER,		// etype Int32
	DER_PACK_LEAVE,					// [0] etype
	DER_PACK_OPTIONAL,				// kvno OPTIONAL
	DER_PACK_ENTER | DER_TAG_CONTEXT (1),		// [1] kvno
	DER_PACK_STORE | DER_TAG_INTEGER,		// kvno Uint32
	DER_PACK_LEAVE,					// [1] kvno
	DER_PACK_ENTER | DER_TAG_CONTEXT (2),		// [2] cipher
	DER_PACK_STORE | DER_TAG_OCTETSTRING,		// cipher [2] OCTETSTRING
	DER_PACK_LEAVE,					// [2] cipher
	DER_PACK_LEAVE,					// enc-part
	DER_PACK_LEAVE,					// [3] enc-part
	DER_PACK_LEAVE,					// Ticket
	DER_PACK_END
};


derwalk pack_EncTicketPart [] = {
	DER_PACK_ENTER | DER_TAG_APPLICATION (3),	// EncTicketPart [APPL 3]
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// [APPL 3] SEQUENCE {
	DER_PACK_ENTER | DER_TAG_CONTEXT (0),		// [0] TicketFlags
	DER_PACK_STORE | DER_TAG_INTEGER,		// TicketFlags
	DER_PACK_LEAVE,					// [0] TicketFlags
	DER_PACK_ENTER | DER_TAG_CONTEXT (1),		// [1] EncryptionKey
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// SEQUENCE {
	DER_PACK_STORE | DER_TAG_INTEGER,		// keytype
	DER_PACK_STORE | DER_TAG_OCTETSTRING,		// keyvalue
	DER_PACK_LEAVE,					// SEQUENCE }
	DER_PACK_LEAVE,					// [1] EncryptionKey
	DER_PACK_ENTER | DER_TAG_CONTEXT (2),		// [2] Realm
	DER_PACK_STORE | DER_TAG_GENERALSTRING,		// Realm ::= GeneralString
	DER_PACK_LEAVE,					// [2] Realm
	DER_PACK_ENTER | DER_TAG_CONTEXT (3),		// [3] PrincipalName
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// PrincipalName SEQUENCE {
	DER_PACK_STORE | DER_TAG_INTEGER,		// name-type
	DER_PACK_STORE | DER_TAG_SEQUENCE,		// SEQUENCE OF GeneralString
	DER_PACK_LEAVE,					// SEQUENCE } PrincipalName
	DER_PACK_LEAVE,					// [3] PrincipalName
	DER_PACK_ENTER | DER_TAG_CONTEXT (4),		// [4] TransitedEncoding
	DER_PACK_ENTER | DER_TAG_SEQUENCE,		// TransEnc ::= SEQUENCE {
	DER_PACK_ENTER | DER_TAG_CONTEXT (0),		// [0] tr-type
	DER_PACK_STORE | DER_TAG_INTEGER,		// tr-type
	DER_PACK_LEAVE,					// [0] tr-type
	DER_PACK_ENTER | DER_TAG_CONTEXT (1),		// [1] contents
	DER_PACK_STORE | DER_TAG_OCTETSTRING,		// contents
	DER_PACK_LEAVE,					// [1] contents
	DER_PACK_LEAVE,					// SEQUENCE } TrancEnc
	DER_PACK_LEAVE,					// [4] TransitedEncoding
	DER_PACK_ENTER | DER_TAG_CONTEXT (5),		// [5] authtime
	DER_PACK_STORE | DER_TAG_GENERALIZEDTIME,	// KerberosTime
	DER_PACK_LEAVE,					// [5] authtime
	DER_PACK_OPTIONAL,				// [6] starttime OPTIONAL
	DER_PACK_ENTER | DER_TAG_CONTEXT (6),		// [6] starttime
	DER_PACK_STORE | DER_TAG_GENERALIZEDTIME,	// KerberosTime
	DER_PACK_LEAVE,					// [6] starttime
	DER_PACK_ENTER | DER_TAG_CONTEXT (7),		// [7] endtime
	DER_PACK_STORE | DER_TAG_GENERALIZEDTIME,	// KerberosTime
	DER_PACK_LEAVE,					// [7] endtime
	DER_PACK_OPTIONAL,				// [8] renew-till OPTIONAL
	DER_PACK_ENTER | DER_TAG_CONTEXT (8),		// [8] renew-till
	DER_PACK_STORE | DER_TAG_GENERALIZEDTIME,	// KerberosTime
	DER_PACK_LEAVE,					// [8] renew-till
	DER_PACK_OPTIONAL,				// [9] caddr OPTIONAL
	DER_PACK_ENTER | DER_TAG_CONTEXT (9),		// [9] caddr
	DER_PACK_STORE | DER_TAG_SEQUENCE,		// SEQUENCE OF HostAddress
	DER_PACK_LEAVE,					// [9] caddr
	DER_PACK_OPTIONAL,				// [10] authz-data OPTIONAL
	DER_PACK_ENTER | DER_TAG_CONTEXT (10),		// [10] authz-data
	DER_PACK_STORE | DER_TAG_SEQUENCE,		// SEQUENCE OF SEQUENCE...
	DER_PACK_LEAVE,					// [10] authz-data
	DER_PACK_LEAVE,					// SEQUENCE }
	DER_PACK_LEAVE,					// EncTicketPart [APPL 3]
	DER_PACK_END
};


struct ovly_PrincipalName {
	dercursor name_type;
	dercursor name_string;
};

struct ovly_EncryptedData {
	dercursor etype;
	dercursor kvno;
	dercursor cipher;
};

struct ovly_Ticket {
	dercursor tkt_vno;
	dercursor realm;
	struct ovly_PrincipalName sname;
	struct ovly_EncryptedData enc_part;
};


struct ovly_EncryptionKey {
	dercursor keytype;
	dercursor keyvalue;
};

struct ovly_TransitedEncoding {
	dercursor tr_type;
	dercursor contents;
};

struct ovly_EncTicketPart {
	dercursor flags;
	struct ovly_EncryptionKey key;
	dercursor crealm;
	struct ovly_TransitedEncoding transited;
	dercursor authtime;
	dercursor starttime;
	dercursor endtime;
	dercursor renew_till;
	dercursor caddr;
	dercursor authorization_data;
};


int main (int argc, char *argv []) {
	exit (1);	// To be implemented
}

