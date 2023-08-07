from aesmix256k import mixencrypt, mixdecrypt, MACRO_SIZE
from multiprocessing import Pool

from pathlib import Path

from .fastfile import FastFile
from .padder import Padder
from .ipfs import block_put, block_get

padder = Padder(blocksize=MACRO_SIZE)
SIZE_TO_KEEP = 1024  # Keep 1KB over 256KB of macro block


def _encrypt_block(arg):
    block, key, iv = arg
    encrypted = mixencrypt(data=block, key=key, iv=iv)
    to_keep = encrypted[:SIZE_TO_KEEP]
    to_ipfs = encrypted[SIZE_TO_KEEP:]

    cid = block_put(to_ipfs)

    return to_keep, cid


def _decrypt_block(arg):
    kept_data, cid, key, iv = arg

    from_ipfs = block_get(cid)

    decrypted = mixdecrypt(kept_data + from_ipfs, key, iv)
    return decrypted


def encrypt(data, path: Path, key, iv):
    """Encrypts plaintext data.

    Args:
        data (bytestr|bytearray): The data to encrypt (multiple of MACRO_SIZE).
        key (bytestr): The key used for AES encryption (16 bytes long).
        iv (bytestr): The iv used for AES encryption (16 bytes long).
    """
    padded_data = data if isinstance(data, bytearray) else bytearray(data)
    padder.pad_mutable(padded_data)

    num_macroblocks = len(padded_data) // MACRO_SIZE
    with Pool() as p:
        args = [
            (padded_data[MACRO_SIZE*i: MACRO_SIZE*(i+1)], key, iv) for i in range(num_macroblocks)
        ]
        res = p.map(_encrypt_block, args)

    ipfs_cids = []
    to_keep = bytearray(b'')
    for kept, cid in res:
        to_keep += kept
        ipfs_cids.append(cid)

    with FastFile(path, 'w') as f:
        f.write(to_keep)

    return ipfs_cids


def decrypt(path, key, iv, cids=[], threads=None):
    """Decrypts data saved in the given path.

    Args:
        path (str): The path to read.
        key (bytestr): The key used for AES encryption (16 bytes long).
        iv (bytestr): The iv used for AES encryption (16 bytes long).
        threads (int): The number of threads used. (default: cpu count).
    """
    with FastFile(path, 'r') as f:
        kept_pieces = f.read()

    num_macroblocks = len(cids)
    assert len(kept_pieces) // SIZE_TO_KEEP == num_macroblocks

    with Pool() as p:
        pieces = p.map(_decrypt_block,
                       [(kept_pieces[i*SIZE_TO_KEEP: (i+1)*SIZE_TO_KEEP], cids[i], key, iv)
                        for i in range(num_macroblocks)])

    data = bytearray(b'')
    for p in pieces:
        data += p
    data = padder.unpad(data)
    return data
