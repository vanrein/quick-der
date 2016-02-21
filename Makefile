# SUBDIRS = lib asn2qder rfc test
SUBDIRS = lib tool test

all:
	for d in $(SUBDIRS); do make -C "$$d" all ; done

install:
	for d in $(SUBDIRS); do make -C "$$d" install ; done

uninstall:
	for d in $(SUBDIRS); do make -C "$$d" uninstall ; done

clean:
	for d in $(SUBDIRS); do make -C "$$d" clean ; done
