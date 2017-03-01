# Conversion of ASN.1 specs to convenient header files
include(MacroASN1Header)

add_custom_target(arpa2-headers ALL)
add_asn1_headers(arpa2-headers
	kxover
	RemotePKCS11
	)

