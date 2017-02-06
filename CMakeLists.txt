#
# CMAKE SETUP (version, build style)
#
cmake_minimum_required (VERSION 2.8 FATAL_ERROR)
project ("Quick-DER" C)

set (CMAKE_MACOSX_RPATH 0)  # Don't use rpaths (but we don't build executables anyway)
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CMAKE_SOURCE_DIR}/cmake)

include(MacroEnsureOutOfSourceBuild)
macro_ensure_out_of_source_build("Do not build Quick-DER in the source directory.")
include(MacroAddUninstallTarget)
add_uninstall_target()
include(MacroGitVersionInfo)

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
	"Build include files from ASN.1 specs for ARPA2 projects"
	ON)

get_version_from_git(Quick-DER 0.1.5)

enable_testing ()

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
if (SPEC_ITU)
	add_subdirectory(itu)
endif()
if (SPEC_ARPA2)
	add_subdirectory(arpa2)
endif()
add_subdirectory(tool)
add_subdirectory(test)

#
# PACKAGING
#

set (CPACK_PACKAGE_NAME "Quick-DER")
set (CPACK_PACKAGE_VERSION ${Quick-DER_VERSION})
set (CPACK_PACKAGE_VENDOR "ARPA2 Project")
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
configure_file(Quick-DER.pc.in
  "${PROJECT_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/Quick-DER.pc" @ONLY)

install(FILES
  "${PROJECT_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/Quick-DERConfig.cmake"
  "${PROJECT_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/Quick-DERConfigVersion.cmake"
  DESTINATION "${INSTALL_CMAKE_DIR}" COMPONENT dev)
install(FILES 
  "${PROJECT_BINARY_DIR}${CMAKE_FILES_DIRECTORY}/Quick-DER.pc"
  DESTINATION "lib/pkgconfig/")

