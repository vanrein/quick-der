# PythonSupport.cmake -- support-macros for using Python cross-platform
#
# This module provides one function for manipulating PYTHONPATH and one
# macro for finding a Python3 interpreter; it uses whatever is most
# suitable for the current CMake version to find it, but provides an
# old-fashioned interface.
#
# Copyright 2019, Adriaan de Groot <groot@kde.org>
#
# Redistribution and use is allowed according to the terms of the two-clause BSD license.
#    SPDX-License-Identifier: BSD-2-Clause.degroot
#    License-Filename: LICENSES/BSD-2-Clause.degroot

# Find a Python3 interpreter. This is a flimsy wrapper around find_package,
# and only sets PYTHON_FOUND and PYTHON_EXECUTABLE, as the old-fashioned way.
macro (FindPythonInterpreter)
    if (NOT PYTHON_FOUND)
        message (STATUS "Looking for Python")
    endif()
    if ( CMAKE_VERSION VERSION_GREATER 3.12 )
        find_package (Python)
        if (NOT Python_Interpreter_FOUND )
            message (FATAL_ERROR "No Python interpreter found")
        else()
            set (PYTHON_EXECUTABLE ${Python_EXECUTABLE})
        endif()
        set (PYTHON_FOUND ${Python_Interpreter_FOUND})
    else()
        # set( Python_ADDITIONAL_VERSIONS "3" "3.5" "3.6" "3.7" )
        find_package (PythonInterp)
        if (NOT PYTHONINTERP_FOUND)
            message (FATAL_ERROR "No Python interpreter found.")
        endif()
        set (PYTHON_FOUND ${PYTHONINTERP_FOUND})
    endif()
endmacro()
