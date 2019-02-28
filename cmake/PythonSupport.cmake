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

# Not using WIN32 here, because that's set when the **target** system
# is Windows. Here, we need it while building, regardless of target,
# on a Windows host.
if (CMAKE_HOST_SYSTEM MATCHES "Windows")
    set (PYTHON_PATH_SEPARATOR ";")
else()
    set (PYTHON_PATH_SEPARATOR ":")
endif()

# Sets @p VARNAME to the value of the environment-variable PYTHONPATH,
# with @p path appended to it with a suitable separator. If more than
# one value is passed in, they are all appended with suitable separators.
function (AppendToPythonPath VARNAME path)
    set (_ppath $ENV{PYTHONPATH})
    # Special-case if the existing environment variable is empty.
    if (NOT _ppath)
        set (_ppath ${path})
    else()
        set (_ppath "${_ppath}${PYTHON_PATH_SEPARATOR}${path}")
    endif()
    # And append all the rest.
    foreach (a ${ARGN})
        set (_ppath "${_ppath}${PYTHON_PATH_SEPARATOR}${a}")
    endforeach()
    
    set (${VARNAME} "${_ppath}" PARENT_SCOPE)
endfunction()

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
