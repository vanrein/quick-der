# Install the driver scripts
install(FILES
	${CMAKE_CURRENT_SOURCE_DIR}/asn2quickder.py
	DESTINATION bin
	PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
	RENAME asn2quickder)
install(FILES
	${CMAKE_CURRENT_SOURCE_DIR}/asn1literate.py
	DESTINATION bin
	PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
	RENAME asn1literate)

# Install our own fork of asn1ate
file(COPY setup.py DESTINATION ${CMAKE_CURRENT_BINARY_DIR})

execute_process (COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_CURRENT_BINARY_DIR}/asn2qd1ate)

add_custom_command (OUTPUT quickder-asn2qd1ate-build
			COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_CURRENT_SOURCE_DIR}/asn2qd1ate/*.py ${CMAKE_CURRENT_BINARY_DIR}/asn2qd1ate
			COMMAND python setup.py build
			COMMAND python setup.py install --root ${CMAKE_CURRENT_BINARY_DIR}/installroot --install-platlib .
			WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
	)
add_custom_target (quickder-asn2qd1ate ALL
		DEPENDS quickder-asn2qd1ate-build)

if (NOT NO_INSTALL_PYTHON)
	if (CMAKE_INSTALL_PREFIX)
		set(_python_install_args --prefix ${CMAKE_INSTALL_PREFIX})
	else ()
		set(_python_install_args "")
	endif ()

	install(CODE "execute_process(COMMAND python setup.py install ${_python_install_args} WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR})")
endif()
