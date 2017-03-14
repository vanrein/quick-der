# Provisioning Python compilation and installation

execute_process(COMMAND python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()"
		OUTPUT_VARIABLE PYTHON_SITE_PACKAGES
		OUTPUT_STRIP_TRAILING_WHITESPACE)

# Compile the modules?  It only speeds up module loading, not runtime...
# python -c 'import py_compile; py_compile.compile ("MODULE.py")'
# python -c 'import compileall; compileall.compile_dir (".")'
# add_custom_command (makebe COMMAND ...)
# add_custom_target (newbe DEPENDS makebe)

configure_file (setup.py.in ${CMAKE_CURRENT_BINARY_DIR}/setup.py @ONLY)

add_custom_command (OUTPUT quickder-shared-module-build
			COMMAND python ${CMAKE_CURRENT_BINARY_DIR}/setup.py build)
add_custom_target (quickder-shared-module ALL
		DEPENDS quickder-shared-module-build)


#OLD# install(FILES _quickder.so DESTINATION ${PYTHON_SITE_PACKAGES}/quick_der)

install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/api.py DESTINATION ${PYTHON_SITE_PACKAGES}/quick_der)
install(FILES ${CMAKE_CURRENT_SOURCE_DIR}/__init__.py DESTINATION ${PYTHON_SITE_PACKAGES}/quick_der)
install(CODE "execute_process(COMMAND ${CMAKE_CURRENT_BINARY_DIR}/setup.py install)")
