#
# CMAKE SETUP (version, build style)
#
# SPDX-License-Identifier: BSD-2-Clause
# License-Filename: LICENSE.MD

message(FATAL_ERROR "This repository has moved to GitLab\n\nGet Quick-DER from\n\thttps://gitlab.com/arpa2/quick-der/\n")


cmake_minimum_required (VERSION 3.2 FATAL_ERROR)
project ("Quick-DER" C)

set (CMAKE_C_STANDARD 99)
set (CMAKE_C_STANDARD_REQUIRED ON)

include (FeatureSummary)
find_package (ARPA2CM 0.5 NO_MODULE)
set_package_properties (ARPA2CM PROPERTIES
	DESCRIPTION "CMake modules for ARPA2 projects"
	TYPE REQUIRED
	URL "https://github.com/arpa2/arpa2cm/"
	PURPOSE "Required for the CMake build system of Quick DER"
)

if (ARPA2CM_FOUND)
	set (CMAKE_MODULE_PATH
		${CMAKE_MODULE_PATH}
		${CMAKE_SOURCE_DIR}/cmake
		${ARPA2CM_MODULE_PATH}
	)
else()
        feature_summary (WHAT ALL)
	message (FATAL_ERROR "ARPA2CM is required.")
endif()

include (MacroEnsureOutOfSourceBuild)
include (MacroAddUninstallTarget)
include (MacroGitVersionInfo)
include (MacroCreateConfigFiles)
include (CMakeDependentOption)

macro_ensure_out_of_source_build("Do not build Quick-DER in the source directory.")

#
# OPTIONS / BUILD SETTINGS
#
option (DEBUG
	"Produce verbose output while unpacking and packing DER"
	ON)
option (SPEC_RFC
	"Build include files from ASN.1 fragments of RFCs"
	ON)
option (SPEC_ITU
	"Build include files from ASN.1 fragments of ITU specs"
	ON)
cmake_dependent_option(SPEC_ARPA2
	"Build include files from ASN.1 specs for ARPA2 projects"
	ON
	"SPEC_RFC" OFF)
option (NO_INSTALL_PYTHON
	"Do not install Python modules (e.g. the Python bindings, asn2qd1ate)."
	OFF)
option (NO_TESTING
	"Disable testing."
	OFF)
get_version_from_git (Quick-DER 1.3)

if (NOT NO_TESTING)
	enable_testing ()
endif()

#
# BUILDING
#
add_subdirectory (lib)

include(PythonSupport)
FindPythonInterpreter()

# This is a hack to make sure that, while building
# Quick DER, the asn2quickder script from the SOURCE
# is used, not an already installed one.
set(_qd_asn2quickder ${CMAKE_SOURCE_DIR}/python/scripts/asn2quickder
    CACHE FILEPATH "Path to asn2quickder script" FORCE)

if (NOT NO_INSTALL_PYTHON)
    add_subdirectory (python)
endif ()

add_custom_target (asn2quickder-done)

if (SPEC_RFC)
	add_subdirectory (rfc)
endif ()
if (SPEC_ITU)
	add_subdirectory (itu)
endif ()
if (SPEC_ARPA2)
	add_subdirectory (arpa2)
endif ()

if (NOT NO_TESTING)
    add_subdirectory (test)
endif()

add_uninstall_target ()

#
# PACKAGING
#

set (CPACK_PACKAGE_NAME "Quick-DER")
set (CPACK_PACKAGE_VERSION ${Quick-DER_VERSION})
set (CPACK_PACKAGE_VENDOR "ARPA2.net")
set (CPACK_PACKAGE_CONTACT "Rick van Rein <rick@openfortress.nl>")
# License information for packaging. This uses the SPDX license
# identifiers from https://spdx.org/licenses/
set (CPACK_FREEBSD_PACKAGE_LICENSE "BSD-2-Clause")

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

install(FILES 
		cmake/MacroASN1Module.cmake 
		cmake/module-test.c.in
		cmake/module-test.py.in
	DESTINATION ${ARPA2CM_TOOLCHAIN_DIR})
