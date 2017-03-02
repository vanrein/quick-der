# Conversion of ASN.1 specs to convenient header files
include(MacroASN1Header)

add_custom_target(arpa2-headers ALL)
add_asn1_headers(arpa2-headers
	kxover
	RemotePKCS11
	)

add_custom_target(arpa2-docs ALL)
add_asn1_documents(arpa2-docs
	kxover
	RemotePKCS11
	)
