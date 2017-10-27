# Provisioning Python compilation and installation

# Compile the modules?  It only speeds up module loading, not runtime...
# python -c 'import py_compile; py_compile.compile ("MODULE.py")'
# python -c 'import compileall; compileall.compile_dir (".")'
# add_custom_command (makebe COMMAND ...)
# add_custom_target (newbe DEPENDS makebe)

configure_file (setup.py.in ${CMAKE_CURRENT_BINARY_DIR}/setup.py @ONLY)

execute_process (COMMAND ${CMAKE_COMMAND} -E make_directory ${CMAKE_BINARY_DIR}/python/quick_der)

# The asn1-spec-modules target is special; it is empty here,
# but the spec-directories (e.g. rfc/, itu/ and arpa2/) add
# dependencies to it via macro add_asn1_modules(), so that the
# python bindings are generated before asn1-spec-modules --
# then the shared-module-build can pick them up.
add_custom_target (asn1-spec-modules ALL)

add_custom_command (OUTPUT quickder-shared-module-build
			COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_CURRENT_SOURCE_DIR}/quick_der/*.py ${CMAKE_CURRENT_BINARY_DIR}/quick_der
			COMMAND python ${CMAKE_CURRENT_BINARY_DIR}/setup.py build
			COMMAND python ${CMAKE_CURRENT_BINARY_DIR}/setup.py install --root ${CMAKE_CURRENT_BINARY_DIR}/installroot --install-platlib .
			DEPENDS asn1-spec-modules
	)
add_custom_target (quickder-shared-module ALL
		DEPENDS quickder-shared-module-build)

if (NOT NO_INSTALL_PYTHON)
	if (CMAKE_INSTALL_PREFIX)
		set(_python_install_args --prefix ${CMAKE_INSTALL_PREFIX})
	else ()
		set(_python_install_args "")
	endif ()

	install(CODE "execute_process(COMMAND python setup.py install ${_python_install_args} WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR})")
endif()
