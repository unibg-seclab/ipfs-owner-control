from ._aesmix import lib, ffi

import math
import multiprocessing

MINI_SIZE = lib.MINI_SIZE
BLOCK_SIZE = lib.BLOCK_SIZE
MINI_PER_BLOCK = lib.MINI_PER_BLOCK
MACRO_SIZE = lib.MACRO_SIZE


def _is_power_of(x, base):
    return x == math.pow(base, math.floor(math.log(x, base)))


def _mixprocess(data, key, iv, fn, to_string, threads=None):
    threads = threads if threads is not None else multiprocessing.cpu_count()
    assert len(key) == 16, 'key must be 16 bytes long'
    assert len(iv) == 16, 'iv must be 16 bytes long'
    assert len(data) % MACRO_SIZE == 0, \
        f'plaintext size must be a multiple of {MACRO_SIZE}'

    _data = ffi.from_buffer('unsigned char[]', data)
    _out = ffi.new('unsigned char[]', len(data))
    _size = ffi.cast('unsigned long', len(data))
    _thr = ffi.cast('unsigned int', threads)
    _key = ffi.new('unsigned char[]', key)
    _iv = ffi.new('unsigned char[]', iv)

    if fn in (lib.mixencrypt, lib.mixdecrypt):
        fn(_data, _out, _size, _key, _iv)
    elif fn in (lib.t_mixencrypt, lib.t_mixdecrypt):
        fn(_thr, _data, _out, _size, _key, _iv)
    else:
        raise Exception('unknown mix function %r' % fn)

    res = ffi.buffer(_out, len(data))
    return res[:] if to_string else res


def mixencrypt(data, key, iv, to_string=True):
    '''Encrypts the data using Mix&Slice (mixing phase).
    Args:
        data (bytestr): The data to encrypt. Must be a multiple of MACRO_SIZE.
        key (bytestr): The key used for AES encryption. Must be 16 bytes long.
        iv (bytestr): The iv used for AES encryption. Must be 16 bytes long.
        to_string (bool): returns a bytestr if true, ffi.buffer otherwise.
    Returns:
        An encrypted bytestr if to_string is true, ffi.buffer otherwise.
    '''
    return _mixprocess(data, key, iv, lib.mixencrypt, to_string)


def mixdecrypt(data, key, iv, to_string=True):
    '''Decrypts the data using Mix&Slice (mixing phase).
    Args:
        data (bytestr): The data to decrypt. Must be a multiple of MACRO_SIZE.
        key (bytestr): The key used for AES decryption. Must be 16 bytes long.
        iv (bytestr): The iv used for AES decryption. Must be 16 bytes long.
        to_string (bool): returns a bytestr if true, ffi.buffer otherwise.
    Returns:
        A decrypted bytestr if to_string is true, ffi.buffer otherwise.
    '''
    return _mixprocess(data, key, iv, lib.mixdecrypt, to_string)

def t_mixencrypt(data, key, iv, threads=None, to_string=True):
    """Encrypts the data using Mix&Slice (mixing phase) using multiple threads.
    Args:
        data (bytestr): The data to encrypt. Must be a multiple of MACRO_SIZE.
        key (bytestr): The key used for AES encryption. Must be 16 bytes long.
        iv (bytestr): The iv used for AES encryption. Must be 16 bytes long.
        threads (int): The number of threads used. (default: cpu count).
        to_string (bool): returns a bytestr if true, ffi.buffer otherwise.
    Returns:
        An encrypted bytestr if to_string is true, ffi.buffer otherwise.
    """
    return _mixprocess(data, key, iv, lib.t_mixencrypt, to_string, threads)


def t_mixdecrypt(data, key, iv, threads=None, to_string=True):
    """Decrypts the data using Mix&Slice (mixing phase) using multiple threads.
    Args:
        data (bytestr): The data to decrypt. Must be a multiple of MACRO_SIZE.
        key (bytestr): The key used for AES decryption. Must be 16 bytes long.
        iv (bytestr): The iv used for AES decryption. Must be 16 bytes long.
        threads (int): The number of threads used. (default: cpu count).
        to_string (bool): returns a bytestr if true, ffi.buffer otherwise.
    Returns:
        A decrypted bytestr if to_string is true, ffi.buffer otherwise.
    """
    return _mixprocess(data, key, iv, lib.t_mixdecrypt, to_string, threads)