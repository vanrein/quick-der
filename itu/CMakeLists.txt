# Conversion of ASN.1 specs to convenient header files
include(MacroASN1Header)

add_custom_target(itu-headers ALL)
add_asn1_headers(itu-headers
	)
