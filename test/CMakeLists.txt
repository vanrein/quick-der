include_directories(${CMAKE_SOURCE_DIR}/include)

# Test X509 decode/encode
add_executable (certio.test
	certio.c)
target_link_libraries (certio.test
	quickderStatic)
add_test(certio.test
	certio.test ${CMAKE_CURRENT_SOURCE_DIR}/verisign.der)

add_executable (ldap.test
	ldapsearch.c)
target_include_directories(ldap.test PUBLIC ${CMAKE_BINARY_DIR}/rfc)
target_link_libraries(ldap.test
	quickderStatic)
add_test (ldap.test
	ldap.test ${CMAKE_CURRENT_SOURCE_DIR}/ldap-search-request.bin)

add_executable (der_data.test
	der_data.c)
target_link_libraries(der_data.test
	quickderStatic)
add_test (der_data.test
	der_data.test)
