# ADD_ASN1_MODULE(<modulename> <groupname>)
#    Add a target to generate <modulename>.h and
#    <modulename>.py from the corresponding ASN.1 file
#    <modulename>.asn1. The target is added as a dependency
#	 to <groupname>, which may be an empty target.
#
# Generation of C header files and Python package files
# from ASN.1 sources via the asn2quickder tool. The
# macro add_asn1_modules() is the main API entry: give
# it a target name  and a list of (file) names. 
# Each name must name a .asn1 file (without the extension).
#
#    set_asn2quickder_options(-I incdir1 -I incdir2)
#    add_asn1_modules(my-modules rfc1 rfc2)
#
# This snippet requires files rfc1.asn1 and rfc2.asn1
# to exist.  It produces rfc1.h, rfc1.py, rfc2.h and
# rfc2.py.
#
# The custom targets asn1-spec-modules and my-modules
# are created automatically.
#
# In addition, generation of MD text files from ASN.1
# sources via the asn1literate tool.  The macro
# add_asn1_documents() works in a similar fashion to
# produce Markdown documents from suitable ASN.1 input;
# plain ASN.1 input is still suitable, but will simply
# map to an all-code file, interpreting comments as
# Markdown.
#
#    add_custom_target(my-asn1-documents ALL)
#    add_asn1_documents(my-asn1-documents spec1 spec2)
#
# This snippet requires files spec1.asn1 and spec2.asn1 to exist.
#
# For each header generated, a simple test is also
# created, which compiles the generated code. If the
# CMake variable NO_TESTING has a truthy-value, then
# building these tests is suppressed (in addition to the usual
# mechanism of add_test() not running the tests).

# Copyright 2017, Adriaan de Groot <groot@kde.org>
#
# Redistribution and use is allowed according to the terms of the two-clause BSD license.
#    https://opensource.org/licenses/BSD-2-Clause
#    SPDX short identifier: BSD-2-Clause

include (PythonSupport)
FindPythonInterpreter()

execute_process (COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/python/testing)
set (_qd_aam_dir ${CMAKE_CURRENT_LIST_DIR})

find_program (_qd_asn2quickder 
    NAMES
        asn2quickder
    HINTS 
        ${CMAKE_SOURCE_DIR}/python/scripts
        ${ARPA2CM_BIN_DIR}
    )
if (NOT _qd_asn2quickder)
    message(FATAL_ERROR "No asn2quickder was found for this module. Quick-DER is incomplete.")
endif()

if (NOT TARGET asn1-spec-modules)
    add_custom_target(asn1-spec-modules ALL)
endif()
    
macro(add_asn1_module _modulename _groupname)
# Generate the module file in <quick-der/modulename.h>
# and python/testing/modulename.py
# and install the header file to include/quick-der/modulename.h.
	set (_ppath ${_ppath} ${CMAKE_SOURCE_DIR}/python)
	add_custom_command (OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/quick-der/${_modulename}.h
		COMMAND ${CMAKE_COMMAND} -E env PYTHONPATH=${_ppath} ${PYTHON_EXECUTABLE} ${_qd_asn2quickder} -l c ${asn1module_asn2quickder_options} ${CMAKE_CURRENT_SOURCE_DIR}/${_modulename}.asn1
		DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${_modulename}.asn1
		WORKING_DIRECTORY quick-der
		COMMENT "Build include file ${_modulename}.h from ASN.1 spec")
	add_custom_command (OUTPUT ${CMAKE_BINARY_DIR}/python/testing/${_modulename}.py
		COMMAND ${CMAKE_COMMAND} -E env PYTHONPATH=${_ppath} ${PYTHON_EXECUTABLE} ${_qd_asn2quickder} -l python ${asn1module_asn2quickder_options} ${CMAKE_CURRENT_SOURCE_DIR}/${_modulename}.asn1
		DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${_modulename}.asn1
		WORKING_DIRECTORY ${CMAKE_BINARY_DIR}/python/testing
		COMMENT "Build Python script ${_modulename}.py from ASN.1 spec")
	install(FILES ${CMAKE_CURRENT_BINARY_DIR}/quick-der/${_modulename}.h DESTINATION include/quick-der)

	add_custom_target(${_modulename}_asn1_h DEPENDS 
		${CMAKE_CURRENT_BINARY_DIR}/quick-der/${_modulename}.h
		${CMAKE_BINARY_DIR}/python/testing/${_modulename}.py
	)
	add_dependencies(${_groupname} ${_module}_asn1_h)

	# Also add a test that builds against that module
	if (NOT NO_TESTING)
		set(ASN1_MODULE_NAME ${_modulename})
		set(ASN1_HEADER_NAME quick-der/${_modulename})
		configure_file(${_qd_aam_dir}/module-test.c.in ${CMAKE_CURRENT_BINARY_DIR}/${_modulename}.c @ONLY)
		configure_file(${_qd_aam_dir}/module-test.py.in ${CMAKE_CURRENT_BINARY_DIR}/${_modulename}-test.py @ONLY)
		add_executable(${_modulename}-test-h ${CMAKE_CURRENT_BINARY_DIR}/${_modulename}.c)
		target_include_directories(${_modulename}-test-h PUBLIC ${CMAKE_SOURCE_DIR}/include ${CMAKE_CURRENT_BINARY_DIR})
	
		add_dependencies(${_modulename}-test-h asn2quickder-done)
		add_dependencies(asn2quickder-done ${_modulename}_asn1_h)
	
		add_test(${_modulename}-test-h ${_modulename}-test-h)
		add_test(${_modulename}-test-py ${CMAKE_COMMAND} -E env PYTHONPATH=${_ppath} ${PYTHON_EXECUTABLE} ${_modulename}-test.py)
	endif()
endmacro()

macro(add_asn1_modules _groupname)
	if (NOT TARGET ${_groupname})
		add_custom_target(${_groupname} ALL)
	endif()
	add_dependencies(asn1-spec-modules ${_groupname})  # Target comes from the python/ subdir
	file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/quick-der)
	foreach (_module ${ARGN})
		add_asn1_module(${_module} ${_groupname})
	endforeach()
endmacro()

macro(add_asn1_document _docname _groupname)
	add_custom_command (OUTPUT doc/${_docname}.md
		COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_SOURCE_DIR}/python/scripts/asn1literate ${CMAKE_CURRENT_SOURCE_DIR}/${_docname}.asn1 ${_docname}.md
		DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${_docname}.asn1
		WORKING_DIRECTORY doc
		COMMENT "Build markdown text file ${_docname}.md from ASN.1 spec")
	add_custom_target(${_docname}_asn1_md DEPENDS doc/${_docname}.md)
	install(FILES ${CMAKE_CURRENT_BINARY_DIR}/doc/${_docname}.md DESTINATION share/doc/quick-der)
endmacro()

macro(add_asn1_documents _groupname)
	if (NOT TARGET ${_groupname})
		add_custom_target(${_groupname} ALL)
	endif()
	file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/doc)
	foreach (_document ${ARGN})
		add_asn1_document(${_document} ${_groupname})
		add_dependencies(${_groupname} ${_document}_asn1_md)
	endforeach()
endmacro()

macro(set_asn2quickder_options)
	set (asn1module_asn2quickder_options ${ARGN})
endmacro()
