# google-cli Makefile

PREFIX=/usr/local
BINDIR=$(PREFIX)/bin
MANDIR=$(PREFIX)/share/man/man1
DOCDIR=$(PREFIX)/share/doc/markit
UNAME_S:=$(shell uname -s)


.PHONY: install uninstall

install:
	install -m755 -d $(BINDIR)
	install -m755 -d $(MANDIR)
	install -m755 -d $(DOCDIR)
	gzip -c markit.1 > markit.1.gz
	@if [ "$(UNAME_S)" = "Linux" ]; then\
		install -m755 -t $(BINDIR) markit; \
		install -m644 -t $(MANDIR) markit.1.gz; \
		install -m644 -t $(DOCDIR) README.md; \
	fi
	@if [ "$(UNAME_S)" = "Darwin" ]; then\
		install -m755  markit $(BINDIR); \
		install -m644  markit.1.gz $(MANDIR); \
		install -m644  README.md $(DOCDIR); \
	fi
	rm -f markit.1.gz

uninstall:
	rm -f $(BINDIR)/markit
	rm -f $(MANDIR)/markit.1.gz
	rm -rf $(DOCDIR)
