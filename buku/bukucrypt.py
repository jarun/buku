#! /usr/bin/env python3

import logging
import os
import sys

from .bukuutil import get_default_dbdir

LOGGER = logging.getLogger()
LOGERR = LOGGER.error


class BukuCrypt:
    """Class to handle encryption and decryption of
    the database file. Functionally a separate entity.

    Involves late imports in the static functions but it
    saves ~100ms each time. Given that encrypt/decrypt are
    not done automatically and any one should be called at
    a time, this doesn't seem to be an outrageous approach.
    """

    # Crypto constants
    BLOCKSIZE = 0x10000  # 64 KB blocks
    SALT_SIZE = 0x20
    CHUNKSIZE = 0x80000  # Read/write 512 KB chunks

    @staticmethod
    def get_filehash(filepath):
        """Get the SHA256 hash of a file.

        Parameters
        ----------
        filepath : str
            Path to the file.

        Returns
        -------
        hash : bytes
            Hash digest of file.
        """

        from hashlib import sha256

        with open(filepath, 'rb') as fp:
            hasher = sha256()
            buf = fp.read(BukuCrypt.BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = fp.read(BukuCrypt.BLOCKSIZE)

            return hasher.digest()

    @staticmethod
    def encrypt_file(iterations, dbfile=None):
        """Encrypt the bookmarks database file.

        Parameters
        ----------
        iterations : int
            Number of iterations for key generation.
        dbfile : str, optional
            Custom database file path (including filename).
        """

        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.ciphers import (Cipher, modes, algorithms)
            from getpass import getpass
            from hashlib import sha256
            import struct
        except ImportError:
            LOGERR('cryptography lib(s) missing')
            sys.exit(1)

        if iterations < 1:
            LOGERR('Iterations must be >= 1')
            sys.exit(1)

        if not dbfile:
            dbfile = os.path.join(get_default_dbdir(), 'bookmarks.db')
        encfile = dbfile + '.enc'

        db_exists = os.path.exists(dbfile)
        enc_exists = os.path.exists(encfile)

        if db_exists and not enc_exists:
            pass
        elif not db_exists:
            LOGERR('%s missing. Already encrypted?', dbfile)
            sys.exit(1)
        else:
            # db_exists and enc_exists
            LOGERR('Both encrypted and flat DB files exist!')
            sys.exit(1)

        password = getpass()
        passconfirm = getpass()
        if not password or not passconfirm:
            LOGERR('Empty password')
            sys.exit(1)
        if password != passconfirm:
            LOGERR('Passwords do not match')
            sys.exit(1)

        try:
            # Get SHA256 hash of DB file
            dbhash = BukuCrypt.get_filehash(dbfile)
        except Exception as e:
            LOGERR(e)
            sys.exit(1)

        # Generate random 256-bit salt and key
        salt = os.urandom(BukuCrypt.SALT_SIZE)
        key = ('%s%s' % (password, salt.decode('utf-8', 'replace'))).encode('utf-8')
        for _ in range(iterations):
            key = sha256(key).digest()

        iv = os.urandom(16)
        encryptor = Cipher(
            algorithms.AES(key),
            modes.CBC(iv),
            backend=default_backend()
        ).encryptor()
        filesize = os.path.getsize(dbfile)

        try:
            with open(dbfile, 'rb') as infp, open(encfile, 'wb') as outfp:
                outfp.write(struct.pack('<Q', filesize))
                outfp.write(salt)
                outfp.write(iv)

                # Embed DB file hash in encrypted file
                outfp.write(dbhash)

                while True:
                    chunk = infp.read(BukuCrypt.CHUNKSIZE)
                    if len(chunk) == 0:
                        break
                    elif len(chunk) % 16 != 0:
                        chunk = '%s%s' % (chunk, ' ' * (16 - len(chunk) % 16))

                    outfp.write(encryptor.update(chunk) + encryptor.finalize())

            os.remove(dbfile)
            print('File encrypted')
            sys.exit(0)
        except Exception as e:
            LOGERR(e)
            sys.exit(1)

    @staticmethod
    def decrypt_file(iterations, dbfile=None):
        """Decrypt the bookmarks database file.

        Parameters
        ----------
        iterations : int
            Number of iterations for key generation.
        dbfile : str, optional
            Custom database file path (including filename).
            The '.enc' suffix must be omitted.
        """

        try:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives.ciphers import (Cipher, modes, algorithms)
            from getpass import getpass
            from hashlib import sha256
            import struct
        except ImportError:
            LOGERR('cryptography lib(s) missing')
            sys.exit(1)

        if iterations < 1:
            LOGERR('Decryption failed')
            sys.exit(1)

        if not dbfile:
            dbfile = os.path.join(get_default_dbdir(), 'bookmarks.db')
        else:
            dbfile = os.path.abspath(dbfile)
            dbpath, filename = os.path.split(dbfile)

        encfile = dbfile + '.enc'

        enc_exists = os.path.exists(encfile)
        db_exists = os.path.exists(dbfile)

        if enc_exists and not db_exists:
            pass
        elif not enc_exists:
            LOGERR('%s missing', encfile)
            sys.exit(1)
        else:
            # db_exists and enc_exists
            LOGERR('Both encrypted and flat DB files exist!')
            sys.exit(1)

        password = getpass()
        if not password:
            LOGERR('Decryption failed')
            sys.exit(1)

        try:
            with open(encfile, 'rb') as infp:
                size = struct.unpack('<Q', infp.read(struct.calcsize('Q')))[0]

                # Read 256-bit salt and generate key
                salt = infp.read(32)
                key = ('%s%s' % (password, salt.decode('utf-8', 'replace'))).encode('utf-8')
                for _ in range(iterations):
                    key = sha256(key).digest()

                iv = infp.read(16)
                decryptor = Cipher(
                    algorithms.AES(key),
                    modes.CBC(iv),
                    backend=default_backend(),
                ).decryptor()

                # Get original DB file's SHA256 hash from encrypted file
                enchash = infp.read(32)

                with open(dbfile, 'wb') as outfp:
                    while True:
                        chunk = infp.read(BukuCrypt.CHUNKSIZE)
                        if len(chunk) == 0:
                            break

                        outfp.write(decryptor.update(chunk) + decryptor.finalize())

                    outfp.truncate(size)

            # Match hash of generated file with that of original DB file
            dbhash = BukuCrypt.get_filehash(dbfile)
            if dbhash != enchash:
                os.remove(dbfile)
                LOGERR('Decryption failed')
                sys.exit(1)
            else:
                os.remove(encfile)
                print('File decrypted')
        except struct.error:
            LOGERR('Tainted file')
            sys.exit(1)
        except Exception as e:
            LOGERR(e)
            sys.exit(1)
