# SUBDIRS = lib asn2qder test rfc arpa2
SUBDIRS = lib tool test rfc

all:
	#
	# To incorporate subprojects with valuable add-ons, run:
	#
	# git submodule update --init
	#
	@ $(foreach d,$(SUBDIRS),$(MAKE) -C '$d' all &&) echo "Made all subdirectories"

install:
	@ $(foreach d,$(SUBDIRS),$(MAKE) -C '$d' all &&) echo "Installed all subdirectories"

uninstall:
	@ $(foreach d,$(SUBDIRS),$(MAKE) -C '$d' all &&) echo "Uninstalled all subdirectories"

clean:
	@ $(foreach d,$(SUBDIRS),$(MAKE) -C '$d' all &&) echo "Cleaned all subdirectories"
