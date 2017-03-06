# Conversion of ASN.1 specs to convenient header files
include(MacroASN1Header)

include_directories(${CMAKE_BINARY_DIR}/rfc)

set_asn2quickder_options(-I ${CMAKE_SOURCE_DIR}/rfc)

add_custom_target(arpa2-headers ALL)
add_asn1_headers(arpa2-headers
	kxover
	RemotePKCS11
	)

add_dependencies(arpa2-headers rfc-headers)
add_custom_target(arpa2-docs ALL)
add_asn1_documents(arpa2-docs
	kxover
	RemotePKCS11
	)
  
