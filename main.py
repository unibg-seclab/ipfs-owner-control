import math
from argparse import ArgumentParser
from fuse import FUSE

from freyafs import FreyaFS
from cache.eviction import EvictionTechnique, values as eviction_values


if __name__ == '__main__':
    parser = ArgumentParser(
        description='Freya File System - a Mix&Slice virtual file system'
    )

    parser.add_argument('mountpoint',
                        metavar='MOUNT',
                        help='mount point of FreyaFS')
    parser.add_argument('data',
                        metavar='DATA',
                        help='folder containing your encrypted files')
    parser.add_argument('-d', '--debug',
                        help='run in debug mode',
                        action='store_true',
                        default=False)
    parser.add_argument('-t', '--multithread',
                        help='run in multi-threaded mode',
                        action='store_true',
                        default=False)
    parser.add_argument('--cache-max-mem',
                        help='maximum memory to allow for the cache of open files (in Bytes)',
                        type=int,
                        default=math.inf)
    parser.add_argument('--eviction-technique',
                        help=f'how to perform cache eviction, one of {", ".join(eviction_values())}',
                        type=EvictionTechnique,
                        default=EvictionTechnique.LRU)
    parser.add_argument('--dump-metadata',
                        help='print metadata information to the terminal',
                        action='store_true',
                        default=False)

    args = parser.parse_args()
    data = args.data
    mountpoint = args.mountpoint

    print('[*] Mounting FreyaFS...')
    fs = FreyaFS(data,
                 mountpoint,
                 memory_cap=args.cache_max_mem,
                 eviction_technique=args.eviction_technique,
                 dump_metadata=args.dump_metadata)
    FUSE(fs,
         mountpoint,
         foreground=True,
         debug=args.debug,
         nothreads=not args.multithread,
         big_writes=True)

    print('\n[*] Unmounting FreyaFS...')
    print('[*] FreyaFS unmounted')
    print('[*] Updating FreyaFS metadata...')
    fs.dump()
    print('[*] FreyaFS metadata updated')
