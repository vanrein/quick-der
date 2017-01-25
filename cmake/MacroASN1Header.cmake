# Generation of C header files from ASN.1 sources
# via the asn2quickder tool. The macro add_asn1_headers()
# is the main API entry: give it a target name (e.g.
# a custom target added to the default build target
# through add_custom_target(group-of-asn-headers ALL) )
# and a list of names. Each name must name a .asn1 file
# (without the extension).
#
#
#    add_custom_target(my-headers ALL)
#    add_asn1_headers(my-headers rfc1 rfc2)
#
# This snipper requires files rfc1.asn1 and rfc2.asn1 to exist.

macro(add_asn1_header _headername)
	add_custom_target (${_headername}.h
		${CMAKE_SOURCE_DIR}/tool/asn2quickder.py ${CMAKE_CURRENT_SOURCE_DIR}/${_headername}.asn1
		COMMENT "Build include file ${_headername}.h from ASN.1 spec"
		SOURCES ${_headername}.asn1)
	install(FILES ${_headername}.h DESTINATION include/quick-der)
endmacro()

macro(add_asn1_headers _groupname)
	foreach (_header ${ARGN})
		add_asn1_header(${_header})
		add_dependencies(${_groupname} ${_header}.h)
	endforeach()
endmacro()

