# Conversion of ASN.1 specs to convenient C header files and Python packages
include(MacroASN1Module)

add_custom_target(itu-modules ALL)
add_asn1_modules(itu-modules
	)
