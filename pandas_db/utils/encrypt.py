import os
import hashlib


def encrypt(string):
    salt = os.environ.get('SALT', '')
    """
    Hashes a string for use in storing password to a database.
    Optional salt string for added security.
    """
    derived_key = hashlib.pbkdf2_hmac('sha256', bytes(string, 'UTF-8'), bytes(salt, 'UTF-8'), 100_000)

    return derived_key.hex()
