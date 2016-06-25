OBJS = der_pack.o der_prepack.o der_unpack.o der_iterate.o der_walk.o der_skipenter.o der_header.o

TARGETS = libquickder.a libquickder.so

CFLAGS=-Wall -Wextra -pedantic -Wstrict-prototypes -Wold-style-definition -Wwrite-strings -Wshadow -Wformat -Wformat-security -Wunreachable-code -Wmissing-prototypes

DESTPATH=$(abspath $(basename $(DESTDIR))/$(basename $(PREFIX)))

all: $(TARGETS)

install: $(TARGETS)
	mkdir -p "$(DESTPATH)/include/quick-der"
	mkdir -p "$(DESTPATH)/lib/pkgconfig"
	install $(TARGETS) "$(DESTPATH)/lib"
	install ../include/quick-der/api.h "$(DESTPATH)/include/quick-der"
	( echo 'prefix=$(DESTPATH)' ; echo 'exec_prefix=$${prefix}' ; echo 'includedir=$${prefix}/include' ; echo 'libdir=$${prefix}/lib' ; echo ; echo 'Name: quick-der' ; echo "Description: Quick \`n\' Easy DER library" ; echo 'Version: $(VERSION)' ; echo 'URL: https://github.com/vanrein/quick-der' ; echo 'Cflags: -I$${includedir}' ; echo 'Libs: -L$${libdir} -lquickder' ) > '$(DESTPATH)/lib/pkgconfig/quick-der.pc'

uninstall:
	for f in $(TARGETS); do rm -f "$(DESTPATH)/lib/$$f" ; done
	rm -f '$(DESTPATH)/include/quick-der/api.h'
	rmdir --ignore-fail-on-non-empty '$(DESTPATH)/include/quick-der'
	rm -f '$(DESTPATH)/lib/pkgconfig/quick-der.pc'
	rmdir --ignore-fail-on-non-empty '$(DESTPATH)/lib/pkgconfig'

.PHONY: clean	
clean:
	rm -f $(OBJS) $(TARGETS)

.c.o:
	gcc -fPIC $(CFLAGS) -c -I../include -o "$@" "$<"

libquickder.a: $(OBJS)
	rm -rf "$@"
	ar rc "$@" $(OBJS)

libquickder.so: $(OBJS)
	gcc -I../include --shared $(CFLAGS) -o "$@" $(OBJS)

stats: $(OBJS)
	@for o in *.o ; do objdump -h -j .text $$o | sed -e '/\.text/!d' -e 's/^.*\.text[ \t]*\([^ \t]*\).*/\1'" $${o%.o}/" ;done | while read sz fun ; do printf '%5d %s\n' 0x$$sz $$fun ; done
