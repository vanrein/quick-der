include_directories(${CMAKE_SOURCE_DIR}/include)

# Test X509 decode/encode
add_executable (certio.test
	certio.c)
target_link_libraries (certio.test
	quickderStatic)
add_test(certio.test 
	certio.test ${CMAKE_CURRENT_SOURCE_DIR}/verisign.der)

# Unfinished test to KRB decoding (it needs a test-input file)
add_executable (kxover.test
	kxover.c)
target_link_libraries (kxover.test
	quickderStatic)
add_test(kxover.test kxover.test)