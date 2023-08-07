from Crypto.Util import number

from aesmix.padder import Padder as PadderBase

# Extended from https://github.com/unibg-seclab/aesmix/blob/master/python/aesmix/padder.py
# to be able to work with bytearray instead of bytes, so to prevent re-allocation of data


class Padder(PadderBase):
    def __init__(self, blocksize: int):
        super().__init__(blocksize)

    def pad_mutable(self, data: bytearray):
        """Pads the data to the blocksize and adds trailing padding info.
        Mutates the parameter.
        """
        padsize = self._padinfosize
        new_size = len(data) + padsize
        if new_size % self._blocksize != 0:
            zeros = self._blocksize - (new_size % self._blocksize)
            data.extend(b'\x00' * zeros)
            padsize += zeros
        data.extend(number.long_to_bytes(padsize, self._padinfosize))
        assert len(data) % self._blocksize == 0

    def unpad_mutable(self, data: bytearray):
        """Unpads the data by removing the trailing padding data.
        Mutates the parameter.
        """
        padsize = number.bytes_to_long(data[-self._padinfosize:])
        assert padsize >= self._padinfosize
        data[len(data)-padsize:] = b''
