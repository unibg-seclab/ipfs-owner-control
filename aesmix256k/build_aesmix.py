#!/usr/bin/env python

import cffi
import os

ffibuilder = cffi.FFI()

ffibuilder.cdef("""
    /* aes_mix.h */
    void mixencrypt(const unsigned char* data, unsigned char* out,
                    const unsigned long size, const unsigned char* key,
                    const unsigned char* iv);
    void mixdecrypt(const unsigned char* data, unsigned char* out,
                    const unsigned long size, const unsigned char* key,
                    const unsigned char* iv);
    #define BLOCK_SIZE              ...
    #define MINI_SIZE               ...
    #define MINI_PER_BLOCK          ...
    #define MACRO_SIZE              ...

    /* aes_mix_multi.h */

    void t_mixencrypt(unsigned int thr, const unsigned char* data, unsigned char* out,
                      const unsigned long size, const unsigned char* key, const unsigned char* iv);

    void t_mixdecrypt(unsigned int thr, const unsigned char* data, unsigned char* out,
                      const unsigned long size, const unsigned char* key, const unsigned char* iv);
""")

ffibuilder.set_source(
    '_aesmix',
    """
    #include "aes_mix.c"
    #include "aes_mix_multi.c"
    """,
    include_dirs=[os.getcwd()],
    libraries=['m', 'crypto'],
)

if __name__ == "__main__":
    ffibuilder.compile()
