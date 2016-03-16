PREFIX=/usr/local
BINDIR=$(PREFIX)/bin
MANDIR=$(PREFIX)/share/man/man1
DOCDIR=$(PREFIX)/share/doc/buku
UNAME_S:=$(shell uname -s)


.PHONY: install uninstall

install:
	install -m755 -d $(BINDIR)
	install -m755 -d $(MANDIR)
	install -m755 -d $(DOCDIR)
	gzip -c buku.1 > buku.1.gz
	@if [ "$(UNAME_S)" = "Linux" ]; then\
		install -m755 -t $(BINDIR) buku; \
		install -m644 -t $(MANDIR) buku.1.gz; \
		install -m644 -t $(DOCDIR) README.md; \
	fi
	@if [ "$(UNAME_S)" = "Darwin" ]; then\
		install -m755  buku $(BINDIR); \
		install -m644  buku.1.gz $(MANDIR); \
		install -m644  README.md $(DOCDIR); \
	fi
	rm -f buku.1.gz

uninstall:
	rm -f $(BINDIR)/buku
	rm -f $(MANDIR)/buku.1.gz
	rm -rf $(DOCDIR)
