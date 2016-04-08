PREFIX?=	/usr/local
BINDIR?=	$(PREFIX)/bin
MANDIR?=	$(PREFIX)/share/man/man1
DOCDIR?=	$(PREFIX)/share/doc/buku


.PHONY: install uninstall

install:
	install -m755 -d $(DESTDIR)$(BINDIR)
	install -m755 -d $(DESTDIR)$(MANDIR)
	install -m755 -d $(DESTDIR)$(DOCDIR)
	gzip -c buku.1 > buku.1.gz
	install -m755 buku $(DESTDIR)$(BINDIR)
	install -m644 buku.1.gz $(DESTDIR)$(MANDIR)
	install -m644 README.md $(DESTDIR)$(DOCDIR)
	rm -f buku.1.gz

uninstall:
	rm -f $(DESTDIR)$(BINDIR)/buku
	rm -f $(DESTDIR)$(MANDIR)/buku.1.gz
	rm -rf $(DESTDIR)$(DOCDIR)
