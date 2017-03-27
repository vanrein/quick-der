# Provisioning Python compilation and installation

# Compile the modules?  It only speeds up module loading, not runtime...
# python -c 'import py_compile; py_compile.compile ("MODULE.py")'
# python -c 'import compileall; compileall.compile_dir (".")'
# add_custom_command (makebe COMMAND ...)
# add_custom_target (newbe DEPENDS makebe)

configure_file (setup.py.in ${CMAKE_CURRENT_BINARY_DIR}/setup.py @ONLY)

add_custom_command (OUTPUT quickder-shared-module-build
			COMMAND ${CMAKE_COMMAND} -E copy ${CMAKE_CURRENT_SOURCE_DIR}/quick_der/*.py ${CMAKE_CURRENT_BINARY_DIR}/quick_der
			COMMAND python ${CMAKE_CURRENT_BINARY_DIR}/setup.py build
			COMMAND python ${CMAKE_CURRENT_BINARY_DIR}/setup.py install --root ${CMAKE_CURRENT_BINARY_DIR}/installroot --install-platlib .
			DEPENDS rfc-modules itu-modules arpa2-modules
	)
add_custom_target (quickder-shared-module ALL
		DEPENDS quickder-shared-module-build)
#NOMORE# add_custom_command (TARGET quickder-shared-module
	#NOMORE# PRE_BUILD
	#NOMORE# )

install(CODE "execute_process(COMMAND python setup.py install WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR})")
