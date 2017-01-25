#
# CMAKE SETUP (version, build style)
#
cmake_minimum_required (VERSION 2.8 FATAL_ERROR)
project ("Quick-DER" C)

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

set(Quick-DER_MAJOR_VERSION 0)
set(Quick-DER_MINOR_VERSION 1)
set(Quick-DER_PATCH_VERSION 5)  # RC5, will move to 0.2 for release
set(Quick-DER_VERSION
	${Quick-DER_MAJOR_VERSION}.${Quick-DER_MINOR_VERSION}.${Quick-DER_PATCH_VERSION})


#
# DEPENDENCIES
#

if (SPEC_RFC OR SPEC_ITU OR SPEC_ARPA2)
	#TODO# depend on asn2quickder's "asn1ate" python package
endif()


#
# BUILDING
#
add_subdirectory(lib)
if (SPEC_RFC)
	add_subdirectory(rfc)
endif()

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
# CMAKE CONFIGURATION FILES
#
# These make it simple to use find_package(Quick-DER) in other
# projects, because Quick-DER can be found (and version information
# obtained) automatically.
#
export(PACKAGE Quick-DER)
# The CMake configuration files are written to different locations
# depending on the host platform, since different conventions apply.
if(WIN32 AND NOT CYGWIN)
	set(DEF_INSTALL_CMAKE_DIR CMake)
else()
	set(DEF_INSTALL_CMAKE_DIR lib/cmake/Quick-DER)
endif()
set(INSTALL_CMAKE_DIR ${DEF_INSTALL_CMAKE_DIR} CACHE PATH
	"Installation directory for CMake files")

# Calculate include/ relative to the installed place of the config file.
file(RELATIVE_PATH REL_INCLUDE_DIR "${CMAKE_INSTALL_PREFIX}/${INSTALL_CMAKE_DIR}"
	"${CMAKE_INSTALL_PREFIX}/include")
set(CONF_INCLUDE_DIRS "\${Quick-DER_CMAKE_DIR}/${REL_INCLUDE_DIR}")
# Substitute in real values for the placeholders in the .in files,
# create the files in the build tree, and install them.
configure_file(Quick-DERConfig.cmake.in
  "${PROJECT_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/Quick-DERConfig.cmake" @ONLY)
configure_file(Quick-DERConfigVersion.cmake.in
  "${PROJECT_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/Quick-DERConfigVersion.cmake" @ONLY)
install(FILES
  "${PROJECT_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/Quick-DERConfig.cmake"
  "${PROJECT_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/Quick-DERConfigVersion.cmake"
  DESTINATION "${INSTALL_CMAKE_DIR}" COMPONENT dev)
