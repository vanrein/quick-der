TESTS = certio.ok # kxover.ok krb5ticket.ok

LIBDIR = ../lib
LIBQD = libquickder.a

all: $(LIBDIR)/$(LIBQD) $(TESTS)

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
	gcc -I ../include -o "$@" "$<" "$(LIBDIR)/$(LIBQD)"

%.ok: %.test
	"./$<" && touch "$@"

certio.ok: certio.test
	./certio.test verisign.der
	touch "$@"

kxover.ok: kxover.test
	./kxover.test 

