OBJS = der_pack.o der_prepack.o der_unpack.o der_iterate.o der_walk.o der_skipenter.o der_header.o

TARGETS = libquickder.a libquickder.so

PREFIX = /usr/local

all: $(TARGETS)

install: $(TARGETS)
	install $(TARGETS) "$(PREFIX)/lib"
	mkdir -p "$(PREFIX)/include/quick-der"
	install ../include/quick-der/api.h "$(PREFIX)/include/quick-der"

uninstall:
	for f in $(TARGETS); do rm -f "$(PREFIX)/lib/$$f" ; done
	rm -f "$(PREFIX)/include/quick-der/api.h"
	rmdir --ignore-fail-on-non-empty "$(PREFIX)/include/quick-der"

clean:
	rm -f $(OBJS) $(TARGETS)

.c.o:
	gcc -fPIC -Os -c -I../include -o "$@" "$<"

libquickder.a: $(OBJS)
	rm -rf "$@"
	ar rc "$@" $(OBJS)

libquickder.so: $(OBJS)
	gcc -I../include --shared -Os -o "$@" $(OBJS)

stats: $(OBJS)
	@for o in *.o ; do objdump -h -j .text $$o | sed -e '/\.text/!d' -e 's/^.*\.text[ \t]*\([^ \t]*\).*/\1'" $${o%.o}/" ;done | while read sz fun ; do printf '%5d %s\n' 0x$$sz $$fun ; done
