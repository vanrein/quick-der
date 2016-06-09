OBJS = der_pack.o der_prepack.o der_unpack.o der_iterate.o der_walk.o der_skipenter.o der_header.o

TARGETS = libquickder.a libquickder.so

CFLAGS=-Wall -Wextra -pedantic -Wstrict-prototypes -Wold-style-definition -Wwrite-strings -Wshadow -Wformat -Wformat-security -Wunreachable-code -Wmissing-prototypes

CC ?= gcc
AR ?= ar

all: $(TARGETS)

install: $(TARGETS)
	install $(TARGETS) '$(DESTDIR)$(PREFIX)/lib'
	mkdir -p '$(DESTDIR)$(PREFIX)/include/quick-der'
	install ../include/quick-der/api.h '$(DESTDIR)$(PREFIX)/include/quick-der'
	mkdir -p '$(DESTDIR)$(PREFIX)/lib/pkgconfig'
	( echo 'prefix=$(PREFIX)' ; echo 'exec_prefix=$${prefix}' ; echo 'includedir=$${prefix}/include' ; echo 'libdir=$${prefix}/lib' ; echo ; echo 'Name: quick-der' ; echo "Description: Quick \`n\' Easy DER library" ; echo 'Version: 0.0' ; echo 'URL: https://github.com/vanrein/quick-der' ; echo 'Cflags: -I$${includedir}' ; echo 'Libs: -L$${libdir} -lquickder' ) > '$(DESTDIR)$(PREFIX)/lib/pkgconfig/quick-der.pc'

uninstall:
	for f in $(TARGETS); do rm -f "$(DESTDIR)$(PREFIX)/lib/$$f" ; done
	rm -f '$(DESTDIR)$(PREFIX)/include/quick-der/api.h'
	rmdir --ignore-fail-on-non-empty '$(DESTDIR)$(PREFIX)/include/quick-der'
	rm -f '$(DESTDIR)$(PREFIX)/lib/pkgconfig/quick-der.pc'
	rmdir --ignore-fail-on-non-empty '$(DESTDIR)$(PREFIX)/lib/pkgconfig'

clean:
	rm -f $(OBJS) $(TARGETS)

.c.o:
	$(CC) -fPIC $(CFLAGS) -c -I../include -o "$@" "$<"

libquickder.a: $(OBJS)
	rm -rf "$@"
	$(AR) rc "$@" $(OBJS)

libquickder.so: $(OBJS)
	$(CC) -I../include --shared $(CFLAGS) -o "$@" $(OBJS)

stats: $(OBJS)
	@for o in *.o ; do objdump -h -j .text $$o | sed -e '/\.text/!d' -e 's/^.*\.text[ \t]*\([^ \t]*\).*/\1'" $${o%.o}/" ;done | while read sz fun ; do printf '%5d %s\n' 0x$$sz $$fun ; done
