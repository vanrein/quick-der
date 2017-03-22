# ADD_ASN1_MODULE(<modulename> <groupname>)
#    Add a target to generate <modulename>.h and
#    <modulename>.py from the corresponding ASN.1 file
#    <modulename>.asn1. The target is added as a dependency
#	 to <groupname>, which may be an empty target.
#
# Generation of C header files and Python package files
# from ASN.1 sources via the asn2quickder tool. The
# macro add_asn1_modules() is the main API entry: give
# it a target name (e.g. a custom target added to the
# default build target through
# add_custom_target(group-of-asn-modules ALL) )
# and a list of names. Each name must name a .asn1 file
# (without the extension).
#
#    add_custom_target(my-modules ALL)
#    set_asn2quickder_options(-I incdir1 -I incdir2)
#    add_asn1_modules(my-modules rfc1 rfc2)
#
# This snippet requires files rfc1.asn1 and rfc2.asn1
# to exist.  It produces rfc1.h, rfc1.py, rfc2.h and
# rfc2.py.
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

# Copyright 2017, Adriaan de Groot <groot@kde.org>
#
# Redistribution and use is allowed according to the terms of the two-clause BSD license.
#    https://opensource.org/licenses/BSD-2-Clause
#    SPDX short identifier: BSD-2-Clause

execute_process(COMMAND python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"
		OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
		OUTPUT_STRIP_TRAILING_WHITESPACE)

macro(add_asn1_module _modulename _groupname)
# Generate the module file in <quick-der/modulename.h>
# and quick-der/modulename.py
# and install the header file to include/quick-der/modulename.h.
# and install the Python module to lib/python/site-packages/quick_der/modulename.py
	add_custom_command (OUTPUT quick-der/${_modulename}.h quick-der/${_modulename}.py
		COMMAND ${CMAKE_SOURCE_DIR}/tool/asn2quickder.py ${asn1module_asn2quickder_options} ${CMAKE_CURRENT_SOURCE_DIR}/${_modulename}.asn1
		DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${_modulename}.asn1
		WORKING_DIRECTORY quick-der
		COMMENT "Build include file ${_modulename}.h from ASN.1 spec")
	add_custom_target(${_modulename}_asn1_h DEPENDS quick-der/${_modulename}.h)
	add_custom_target(${_modulename}_asn1_py DEPENDS quick-der/${_modulename}.py)
	install(FILES ${CMAKE_CURRENT_BINARY_DIR}/quick-der/${_modulename}.h DESTINATION include/quick-der)
	install(FILES ${CMAKE_CURRENT_BINARY_DIR}/quick-der/${_modulename}.py DESTINATION ${PYTHON_SITE_PACKAGES}/quick_der)
# Also add a test that builds against that module
	set(ASN1_MODULE_NAME ${_modulename})
	set(ASN1_HEADER_NAME quick-der/${_modulename})
	configure_file(module-test.c.in ${CMAKE_CURRENT_BINARY_DIR}/${_modulename}.c @ONLY)
	configure_file(module-test.py.in ${CMAKE_CURRENT_BINARY_DIR}/${_modulename}-test.py @ONLY)
	add_executable(${_modulename}-test-h ${CMAKE_CURRENT_BINARY_DIR}/${_modulename}.c)
	target_include_directories(${_modulename}-test-h PUBLIC ${CMAKE_SOURCE_DIR}/include ${CMAKE_CURRENT_BINARY_DIR})
	add_dependencies(${_modulename}-test-h ${_groupname})
	add_test(${_modulename}-test-h ${_modulename}-test-h)
	add_test(${_modulename}-test-py python ${_modulename}-test.py)
endmacro()

macro(add_asn1_modules _groupname)
	file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/quick-der)
	foreach (_module ${ARGN})
		add_asn1_module(${_module} ${_groupname})
		add_dependencies(${_groupname} ${_module}_asn1_h)
	endforeach()
endmacro()

macro(add_asn1_document _docname _groupname)
	add_custom_command (OUTPUT doc/${_docname}.md
		COMMAND ${CMAKE_SOURCE_DIR}/tool/asn1literate.py ${CMAKE_CURRENT_SOURCE_DIR}/${_docname}.asn1 ${_docname}.md
		DEPENDS ${CMAKE_CURRENT_SOURCE_DIR}/${_docname}.asn1
		WORKING_DIRECTORY doc
		COMMENT "Build markdown text file ${_docname}.md from ASN.1 spec")
	add_custom_target(${_docname}_asn1_md DEPENDS doc/${_docname}.md)
	install(FILES ${CMAKE_CURRENT_BINARY_DIR}/doc/${_docname}.md DESTINATION share/doc/quick-der)
endmacro()

macro(add_asn1_documents _groupname)
	file(MAKE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/doc)
	foreach (_document ${ARGN})
		add_asn1_document(${_document} ${_groupname})
		add_dependencies(${_groupname} ${_document}_asn1_md)
	endforeach()
endmacro()

macro(set_asn2quickder_options)
	set (asn1module_asn2quickder_options ${ARGN})
endmacro()
