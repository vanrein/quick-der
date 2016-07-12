TESTS = certio.ok # kxover.ok krb5ticket.ok

LIBDIR = ../lib
LIBQD = libquickder.a

EXTRALIBS ?= 

all: "$(LIBDIR)/$(LIBQD)" $(TESTS)

clean:
	for t in $(TESTS) ; do rm -f $$t $${t%.ok}.test ; done

$(LIBDIR)/$(LIBQD):
	make -C "$(LIBDIR)" "$(LIBQD)"

install:
	@echo #
	@echo # The test directory constrains building, but does not install anything
	@echo #

uninstall:


%.test: %.c $(LIBDIR)/$(LIBQD)
	$(CC) -I ../include -o "$@" "$<" "$(LIBDIR)/$(LIBQD)" $(EXTRALIBS)

%.ok: %.test
	"./$<" && touch "$@"

certio.ok: certio.test
	./certio.test verisign.der
	touch "$@"

kxover.ok: kxover.test
	./kxover.test 

