import json
import nacl.pwhash
import nacl.secret
import os
import sys

from base64 import b64decode, b64encode
from getpass import getpass


def generate_key(ask_confirm: bool):
    pw = getpass('Password: ').encode('utf-8')
    if ask_confirm:
        confirm = getpass('Confirm password: ').encode('utf-8')
        if pw != confirm:
            print('ERROR: Your password and confirmation password do not match.')
            sys.exit()

    salt = b'\xd0\xe1\x03\xc2Z<R\xaf]\xfe\xd5\xbf\xf8u|\x8f'
    return nacl.pwhash.argon2id.kdf(nacl.secret.SecretBox.KEY_SIZE, pw, salt)


def load_from_file(key: bytes, filename: str):
    if not os.path.isfile(filename):
        return

    # Read the encrypted file
    with open(filename, 'r') as f:
        content = f.read()
        encrypted = b64decode(content)

    # Decrypt
    box = nacl.secret.SecretBox(key)
    try:
        plaintext = box.decrypt(encrypted)
    except nacl.exceptions.CryptoError:
        print('ERROR: Wrong password.')
        sys.exit()

    # Read JSON
    read = json.loads(plaintext)
    return read


def save_to_file(key: bytes, filename: str, data: dict):
    # Produce JSON string
    plaintext = json.dumps(data)

    # Encrypt metadata
    box = nacl.secret.SecretBox(key)
    encrypted = box.encrypt(plaintext.encode('utf-8'))

    # Store encrypted metadata
    with open(filename, 'w') as f:
        content = b64encode(encrypted).decode('ascii')
        f.write(content)
