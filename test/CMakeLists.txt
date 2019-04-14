include_directories(${CMAKE_SOURCE_DIR}/include ${CMAKE_SOURCE_DIR}/lib)

set(_ppath $ENV{PYTHONPATH})
set(_python_test ${CMAKE_COMMAND} -E env PYTHONPATH=${CMAKE_SOURCE_DIR}/python:${_ppath} python)

# Test X509 decode/encode
add_executable (certio.test
	certio.c)
target_link_libraries (certio.test
	quickderStatic)
add_test(certio-c-test
	certio.test ${CMAKE_CURRENT_SOURCE_DIR}/verisign.der)
add_test(certio-py-test
	 ${_python_test} ${CMAKE_CURRENT_SOURCE_DIR}/certio.py ${CMAKE_CURRENT_SOURCE_DIR}/verisign.der)

# Test construction of an empty instance
add_test(empty-py-test
	${_python_test} ${CMAKE_CURRENT_SOURCE_DIR}/empty-instance.py)
add_test(pack-py-test
	${_python_test} ${CMAKE_CURRENT_SOURCE_DIR}/der_format.py)

if (SPEC_RFC)
    # LDAP tests only work if the LDAP ASN.1 bindings have been generated
	add_executable (ldap.test
		ldapsearch.c)

	add_dependencies(ldap.test rfc-modules)

	target_include_directories(ldap.test PUBLIC ${CMAKE_BINARY_DIR}/rfc)
	target_link_libraries(ldap.test
		quickderStatic)
	add_test (ldap.test.0
		ldap.test ${CMAKE_CURRENT_SOURCE_DIR}/ldap-search-request-0.bin)
	add_test (ldap.test.1
		ldap.test ${CMAKE_CURRENT_SOURCE_DIR}/ldap-search-request-1.bin)
	add_test (ldap.test.2
		ldap.test ${CMAKE_CURRENT_SOURCE_DIR}/ldap-search-request-2.bin)
endif ()

macro(c_test _name)
	add_executable (${_name}.test ${_name}.c)
	target_link_libraries(${_name}.test quickderStatic)
	add_test (${_name}.test ${_name}.test)
endmacro()

c_test(der_data)
c_test(int_putget)
c_test(bool_putget)
c_test(data_putget)
