# Macro add_test_builder() to add a test-executable that isn't built
# by default to the build-tests target, and to add a test running
# that target as well.
#
# Arguments:
#  - command:    target-name of an executable that has been built
#  - [argn...]:  optional arguments to pass in to the test-run
#
# Using this macro, it is possible to use add_executable(foo EXCLUDE_FROM_ALL ...)
# to defer building a test-executable until the tests are actually run. Whether
# this is a good idea is another thing.
add_custom_target(build-tests)

macro(add_test_builder command)
	add_dependencies(build-tests ${command})
	add_test(${command} ${command} ${ARGN})
endmacro()
