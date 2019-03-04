include(PythonSupport)
FindPythonInterpreter()

add_custom_target(python
    ${PYTHON_EXECUTABLE} ${CMAKE_SOURCE_DIR}/setup.py install
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})

if (NOT NO_TESTING)
    add_test(NAME python_test
             COMMAND ${PYTHON_EXECUTABLE} ${CMAKE_SOURCE_DIR}/setup.py test
             WORKING_DIRECTORY ${CMAKE_SOURCE_DIR})
endif()

set (_ppath 
	${_ppath}
    "${CMAKE_CURRENT_SOURCE_DIR}/silly 1"
    "${CMAKE_CURRENT_SOURCE_DIR}/sully 2"
    )
add_custom_target(ppath_test
    COMMAND ${CMAKE_COMMAND} -E env "PYTHONPATH=$<SHELL_PATH:${_ppath}>"
        $<SHELL_PATH:${PYTHON_EXECUTABLE}> $<SHELL_PATH:${CMAKE_CURRENT_SOURCE_DIR}/ppathtest.py>
    )
add_custom_target(ppath_notest
    COMMAND ${CMAKE_COMMAND} -E env
        ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/ppathtest.py
    )
