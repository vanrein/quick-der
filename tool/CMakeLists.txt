# Install only the driver; assume asn1ate comes from elsewhere
# (even though we ship it as part of the sources) -- this is
# because installing a python subtree is too complicated for now.
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
