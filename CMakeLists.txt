#
# DECLARATIONS
#
project ("Quick_DER" C)

cmake_minimum_required (VERSION 2.6 FATAL_ERROR)

set (CMAKE_MACOSX_RPATH 0)  # Don't use rpaths (but we don't build executables anyway)
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CMAKE_SOURCE_DIR}/cmake)

include(MacroEnsureOutOfSourceBuild)

macro_ensure_out_of_source_build("Do not build Quick-DER in the source directory.")

#
# OPTIONS / BUILD SETTINGS
#
option (DEBUG
	"Produce verbose output while unpcaking and packing DER"
	ON)
option (SPEC_RFC
	"Build include files from ASN.1 fragments of RFCs"
	ON)
option (SPEC_ITU
	"Build include files from ASN.1 fragments of ITU specs"
	ON)
option (SPEC_ARPA2
	"Build inlucde files from ASN.1 specs for ARPA2 projects"
	ON)


#
# DEPENDENCIES
#

if (SPEC_RFC OR SPEC_ITU OR SPEC_ARPA2)
	#TODO# depend on asn2quickder's "asn1ate" python package
endif()


#
# BUILDING
#

include_directories (include)

add_library (quickderShared SHARED
	lib/der_header.c
	lib/der_iterate.c
	lib/der_pack.c
	lib/der_prepack.c
	lib/der_skipenter.c
	lib/der_unpack.c
	lib/der_walk.c)
set_target_properties (quickderShared
	PROPERTIES OUTPUT_NAME quickder)

add_library (quickderStatic STATIC
	lib/der_header.c
	lib/der_iterate.c
	lib/der_pack.c
	lib/der_prepack.c
	lib/der_skipenter.c
	lib/der_unpack.c
	lib/der_walk.c)
set_target_properties (quickderStatic
	PROPERTIES OUTPUT_NAME quickder)


if (SPEC_RFC)
	list (APPEND specs "rfc/rfc2315")
	list (APPEND specs "rfc/rfc2578")
	list (APPEND specs "rfc/rfc2898")
	list (APPEND specs "rfc/rfc3062")
	list (APPEND specs "rfc/rfc3280")
	list (APPEND specs "rfc/rfc3909")
	list (APPEND specs "rfc/rfc4120")
	list (APPEND specs "rfc/rfc4178")
	list (APPEND specs "rfc/rfc4373")
	list (APPEND specs "rfc/rfc4511")
	list (APPEND specs "rfc/rfc4531")
	list (APPEND specs "rfc/rfc5208")
	list (APPEND specs "rfc/rfc5280")
	list (APPEND specs "rfc/rfc5805")
	list (APPEND specs "rfc/rfc6960")
	list (APPEND specs "rfc/rfc7292")
endif ()

if (SPEC_ITU)
	#TODO# list (APPEND specs "itu/xxx")
endif ()

if (SPEC_ARPA2)
	#TODO# list (APPEND specs "arpa2/xxx")
endif ()

foreach (spec ${specs})
	get_filename_component (specdir  ${spec} DIRECTORY)
	get_filename_component (specname ${spec} NAME)
	add_custom_target (${specname}.h
		${CMAKE_SOURCE_DIR}/tool/asn2quickder.py ${CMAKE_SOURCE_DIR}/${spec}.asn1
		COMMENT "Build include file ${spec}.h from ASN.1 spec"
		SOURCES ${spec}.asn1)
	add_custom_command (OUTPUT ${specname}.h
		DEPENDS ${spec}.asn1
		POST_BUILD
		COMMAND ${CMAKE_SOURCE_DIR}/tool/asn2quickder.py ${CMAKE_SOURCE_DIR}/${specdir}/${specname}.asn1
		COMMENT "Build specification ${spec}"
		VERBATIM)
	include_directories (${specdir})
	add_custom_command (OUTPUT ${specname}.c
		POST_BUILD
		COMMAND echo >"${specname}.c" "#include \"${specname}.h\""
		COMMENT "Source that tests by including the generated ${specname}.h")
		# not.VERBATIM --> we need the > in the COMMAND
	#TODO:WHYNOT# add_dependencies (${spec}.h quickder)
	list (APPEND header_files ${specname}.h)
endforeach()


#
# TESTS
#
enable_testing ()

add_executable (certio.test
	EXCLUDE_FROM_ALL
	test/certio.c)
target_link_libraries (certio.test
	quickder)
add_test (certio.ok
	certio.test verisign.der)
#TODO:WHYNOT# add_dependencies (certio.test certio.ok)
#TODO:WHYNOT# add_dependencies (certio.ok certio.test)


foreach (spec ${specs})
	get_filename_component (specdir  ${spec} DIRECTORY)
	get_filename_component (specname ${spec} NAME)
	add_test (${specname}
		COMMAND ${CMAKE_C_COMPILER} ${specname})
endforeach()


#
# INSTALLING
#

install (TARGETS quickderShared
	LIBRARY DESTINATION lib
	PUBLIC_HEADER DESTINATION include/quick-der)

#TODO:WHYNOT# install (TARGETS quickderStatic ${header_files}
#TODO:WHYNOT# 	ARCHIVE DESTINATION lib
#TODO:WHYNOT# 	PUBLIC_HEADER DESTINATION include/quick-der
#TODO:WHYNOT# 	COMPONENT dev)


#
# PACKAGING
#

set (CPACK_BUNDLE_NAME, "Quick_DER")

include (CPack)


#
# FUNCTION LIBRARY
#


