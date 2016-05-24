PREFIX ?= /usr/local
BINDIR ?= $(DESTDIR)$(PREFIX)/bin
MANDIR ?= $(DESTDIR)$(PREFIX)/share/man/man1
DOCDIR ?= $(DESTDIR)$(PREFIX)/share/doc/buku

BASHCOMPDIR = $(DESTDIR)/etc/bash_completion.d
FISHCOMPDIR = $(DESTDIR)/usr/share/fish/vendor_completions.d
ZSHCOMPDIR = $(DESTDIR)/usr/share/zsh/site-functions

.PHONY: all install install.comp uninstall uninstall.comp

all:

install:
	install -m755 -d $(BINDIR)
	install -m755 -d $(MANDIR)
	install -m755 -d $(DOCDIR)
	gzip -c buku.1 > buku.1.gz
	install -m755 buku $(BINDIR)
	install -m644 buku.1.gz $(MANDIR)
	install -m644 README.md $(DOCDIR)
	rm -f buku.1.gz

install.comp:
	install -m755 -d $(BASHCOMPDIR) $(FISHCOMPDIR) $(ZSHCOMPDIR)
	install -m644 auto-completion/bash/buku-completion.bash $(BASHCOMPDIR)
	install -m644 auto-completion/fish/buku.fish $(FISHCOMPDIR)
	install -m644 auto-completion/zsh/_buku $(ZSHCOMPDIR)

uninstall:
	rm -f $(BINDIR)/buku
	rm -f $(MANDIR)/buku.1.gz
	rm -rf $(DOCDIR)

uninstall.comp:
	rm -f $(BASHCOMPDIR)/buku-completion.bash $(FISHCOMPDIR)/buku.fish $(ZSHCOMPDIR)/_buku
