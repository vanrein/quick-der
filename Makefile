DESTDIR ?=
PREFIX ?= /usr/local

all: configure compile

build-dir:
	@mkdir -p build

configure: build-dir
	( cd build && cmake .. -DCMAKE_INSTALL_PREFIX=$(PREFIX) )

compile: build-dir
	( cd build && $(MAKE) )
	
install: build-dir
	( cd build && $(MAKE) install )
	
test: build-dir
	( cd build && $(MAKE) test )
	
uninstall: build-dir
	( cd build && $(MAKE) uninstall )

clean:
	rm -rf build/
