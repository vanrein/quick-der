# Build the Quick-DER library twice: once shared, once static.
include_directories (../include)

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

install (TARGETS quickderShared
	LIBRARY DESTINATION lib
	PUBLIC_HEADER DESTINATION include/quick-der)
