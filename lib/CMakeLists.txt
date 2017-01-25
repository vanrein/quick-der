# Build the Quick-DER library twice: once shared, once static.
include_directories (../include)

# Forward the CMake option to the compiler
if (DEBUG)
	add_definitions(-DDEBUG)
endif()

set(quickder_SRC 
	der_header.c
	der_iterate.c
	der_pack.c
	der_prepack.c
	der_skipenter.c
	der_unpack.c
	der_walk.c)

add_library (quickderShared SHARED ${quickder_SRC})
set_target_properties (quickderShared
	PROPERTIES OUTPUT_NAME quickder)

add_library (quickderStatic STATIC ${quickder_SRC})
set_target_properties (quickderStatic
	PROPERTIES OUTPUT_NAME quickder)

# The shared lib is leading and carries the public header files on Apple
# platforms. The static lib is installed too, and then all the header files
# from the top-level include/ directory. For installing the headers, don't
# need an extra quick-der/ level because that's retained in the file paths.
install (TARGETS quickderShared
	LIBRARY DESTINATION lib
	PUBLIC_HEADER DESTINATION include/quick-der)
install (TARGETS quickderStatic
	ARCHIVE DESTINATION lib)
install (DIRECTORY ../include/quick-der
	DESTINATION include
	FILES_MATCHING PATTERN "*.h")