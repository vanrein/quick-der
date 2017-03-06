# Conversion of ASN.1 specs to convenient header files
include(MacroASN1Header)

set_asn2quickder_options(-I ${CMAKE_SOURCE_DIR}/rfc)

add_custom_target(rfc-headers ALL)
add_asn1_headers(rfc-headers
	rfc1422
	rfc2315
	rfc2578
	rfc2898
	rfc3062
	rfc3280
	rfc3909
	rfc4120
	rfc4178
	rfc4373
	rfc4511
	rfc4531
	rfc5208
	rfc5280
	rfc5805
	# rfc6960
	rfc7292)
