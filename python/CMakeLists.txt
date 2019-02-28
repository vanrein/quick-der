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
