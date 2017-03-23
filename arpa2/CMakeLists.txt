# Conversion of ASN.1 specs to convenient C header files and Python packages
include(MacroASN1Module)

include_directories(${CMAKE_BINARY_DIR}/rfc)

set_asn2quickder_options(-I ${CMAKE_SOURCE_DIR}/rfc)

add_custom_target(arpa2-modules ALL)
add_asn1_modules(arpa2-modules
	kxover
	RemotePKCS11
	)

add_dependencies(arpa2-modules rfc-modules)
add_custom_target(arpa2-docs ALL)
add_asn1_documents(arpa2-docs
	kxover
	RemotePKCS11
	)
  
