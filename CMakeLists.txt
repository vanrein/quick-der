#
# CMAKE SETUP (version, build style)
#
cmake_minimum_required (VERSION 3.1 FATAL_ERROR)
project ("Quick-DER" C)

set (CMAKE_MACOSX_RPATH 0)  # Don't use rpaths (but we don't build executables anyway)
set (CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} ${CMAKE_SOURCE_DIR}/cmake)

include (MacroEnsureOutOfSourceBuild)
include (MacroAddUninstallTarget)
include (MacroGitVersionInfo)
include (MacroCreateConfigFiles)

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
	"Build include files from ASN.1 specs for ARPA2 projects"
	ON)

get_version_from_git (Quick-DER 0.0.0)

enable_testing ()

#
# DEPENDENCIES
#

if (SPEC_RFC OR SPEC_ITU OR SPEC_ARPA2)
	#TODO# depend on asn2quickder's "asn1ate" python package
endif ()


#
# BUILDING
#
add_subdirectory (lib)
if (SPEC_RFC)
	add_subdirectory (rfc)
endif ()
if (SPEC_ITU)
	add_subdirectory (itu)
endif ()
if (SPEC_ARPA2)
	add_subdirectory (arpa2)
endif ()
add_subdirectory (tool)
add_subdirectory (test)

add_uninstall_target ()

#
# PACKAGING
#

set (CPACK_PACKAGE_NAME "Quick-DER")
set (CPACK_PACKAGE_VERSION ${Quick-DER_VERSION})
set (CPACK_PACKAGE_VENDOR "ARPA2.net")
set (CPACK_PACKAGE_CONTACT "Rick van Rein <rick@openfortress.nl>")
include (PackAllPossible)
include (CPack)

#
# CMAKE CONFIGURATION FILES
#
# These make it simple to use find_package(Quick-DER) in other
# projects, because Quick-DER can be found (and version information
# obtained) automatically.
#
create_config_files (Quick-DER)
