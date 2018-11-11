PREFIX ?= /usr/local
BINDIR ?= $(DESTDIR)$(PREFIX)/bin
MANDIR ?= $(DESTDIR)$(PREFIX)/share/man/man1
DOCDIR ?= $(DESTDIR)$(PREFIX)/share/doc/buku

.PHONY: all install uninstall

all:

install:
	install -m755 -d $(BINDIR)
	install -m755 -d $(MANDIR)
	install -m755 -d $(DOCDIR)
	gzip -c buku.1 > buku.1.gz
	install -m755 buku $(BINDIR)/buku
	install -m644 buku.1.gz $(MANDIR)
	install -m644 README.md $(DOCDIR)
	rm -f buku.1.gz

uninstall:
	rm -f $(BINDIR)/buku
	rm -f $(MANDIR)/buku.1.gz
	rm -rf $(DOCDIR)
