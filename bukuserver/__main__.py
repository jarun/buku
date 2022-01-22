try:
    from . import server
except ImportError:
    from bukuserver import server


if __name__ == '__main__':
    server.cli()
