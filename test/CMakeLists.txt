include_directories(${CMAKE_SOURCE_DIR}/include)
add_executable (certio.test
	EXCLUDE_FROM_ALL
	certio.c)
target_link_libraries (certio.test
	quickderStatic)
	
add_test_builder(certio.test ${CMAKE_CURRENT_SOURCE_DIR}/verisign.der)
