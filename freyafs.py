import errno
import math
import os
import json
from pathlib import Path

from fuse import FuseOSError, Operations

from cache import Cache
from metadata import Metadata
from structure import PathInfo, PathStructure
from utils.persist import generate_key, load_from_file, save_to_file


class FreyaFS(Operations):
    def __init__(self, root, mountpoint, memory_cap, eviction_technique, dump_metadata):
        self.root = Path(root)
        self.filename = self.root / '.freyafs'
        self.cids = {}
        self.key = generate_key(ask_confirm=not os.path.exists(self.filename))

        data = load_from_file(self.key, self.filename)
        if data is not None:
            self.structure = PathStructure.from_dict(data['structure'])
            self.metadata = Metadata.from_dict(root=self.root, data=data['metadata'])
            self.cids = data['cids']
        else:
            self.structure = PathStructure()
            self.metadata = Metadata(root=self.root)
            self.metadata.add_dir(path=self.structure['/'])

        # Keep track of open files
        self.cache: Cache = Cache(
            root=self.root,
            memory_cap=memory_cap,
            eviction_technique=eviction_technique,
            ipfs_cids=self.cids)

        print(f'[*] FreyaFS mounted at {mountpoint}')
        print(f'FreyaFS will persist your encrypted data at {root}.')
        if memory_cap is not None and memory_cap is not math.inf:
            print(f'[i] Cache memory cap set at {memory_cap} B (eviction with {eviction_technique.value}).')

        if dump_metadata:
            print('[i] Some information about the file system')
            print('[i] Files')
            for path_id, cids in self.cids.items():
                info = self.metadata[PathInfo.make(path_id)]
                print(f'> ID:                       {path_id}')
                print(f'  Size:                     {info.stats["st_size"]}')
                print(f'  On disk size (encrypted): {os.path.getsize((self.root / path_id).absolute())}')
                print(f'  Number of CIDs:           {len(cids)}')

            print('[i] FreyaFS metadata')
            to_write = {
                'structure': self.structure.to_dict(),
                'metadata': self.metadata.to_dict(),
                'cids': self.cids,
            }
            print(f'> In memory size (JSON):    {len(json.dumps(to_write))}')
            print(f'> On disk size (encrypted): {os.path.getsize(self.filename)}')

    def dump(self):
        to_write = {
            'structure': self.structure.to_dict(),
            'metadata': self.metadata.to_dict(),
            'cids': self.cids,
        }

        save_to_file(self.key, self.filename, to_write)

    # --------------------------------------------------------------------- Helpers

    def _actual_path(self, path: str):
        path_info = self.structure[path]
        actual_path = (self.root / path_info.path_id).absolute()
        return actual_path

    def _cids(self, path: str):
        path_info = self.structure[path]
        return self.cids[path_info.path_id]

    # --------------------------------------------------------------------- Filesystem methods

    def access(self, path, mode):
        if path not in self.structure:
            raise FuseOSError(errno.EACCES)

    def chmod(self, path, mode):
        path_info = self.structure[path]
        self.metadata[path_info].chmod(mode)

    def chown(self, path, uid, gid):
        path_info = self.structure[path]
        self.metadata[path_info].chown(uid, gid)

    # Attributi di path (file o cartella)
    def getattr(self, path, fh=None):
        if path not in self.structure:
            raise FuseOSError(errno.ENOENT)

        path_info = self.structure.get(path, follow_symlinks=False)
        info = self.metadata[path_info]
        return info.stats

    def readdir(self, path, fh):
        yield '.'
        yield '..'
        for x in self.structure.contents(path):
            yield x

    def readlink(self, path):
        path_info = self.structure.get(path, follow_symlinks=False)
        actual_path = path_info.link_to_path
        if actual_path.startswith('/'):
            # Path name is absolute, sanitize it.
            return os.path.relpath(actual_path, self.root)
        else:
            return actual_path

    def mknod(self, path, mode, dev):
        actual_path = self._actual_path(path)
        return os.mknod(actual_path, mode, dev)

    def rmdir(self, path):
        path_info = self.structure[path]
        del self.structure[path]
        del self.metadata[path_info]

    def mkdir(self, path, mode):
        path_info = PathInfo.make_only_id()
        self.structure.add(path, path_info)
        self.metadata.add_dir(path_info, mode)

    def statfs(self, path):
        actual_path = self._actual_path(path)
        stv = os.statvfs(actual_path)
        return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
                                                         'f_blocks', 'f_bsize',
                                                         'f_favail', 'f_ffree', 'f_files', 'f_flag',
                                                         'f_frsize', 'f_namemax'))

    def unlink(self, path):
        path_info = self.structure.get(path, follow_symlinks=False)
        del self.structure[path]
        del self.cids[path_info.path_id]

        meta = self.metadata[path_info]
        if meta.is_dir():
            del self.metadata[path_info]
            return

        # Meta is file: decrement st_nlink and remove on 0
        meta.dec_nlink()
        if meta.nlink == 0:
            del self.metadata[path_info]
            os.remove(self.root / path_info.path_id)

    # Used for SOFT links
    def symlink(self, name, target):
        path_info = PathInfo.make_symlink(target)
        self.structure.add(name, path_info)
        self.metadata.add_soft_link(path_info, mode=0o777)

        # The pointed path is kept in memory at all times for speed,
        # but the symlink files contain also the path as their content
        self.cache.create(path_info)
        bytes_written, size = self.cache.write_bytes(path_info, target.encode('utf-8'), 0)
        self.metadata[path_info].set_size(size)

        self.cache.flush(path_info)
        self.cache.release(path_info)

    def rename(self, old, new):
        # Renaming only moves around stuff, but does not rename actual files
        # on disk, nor fake names. So there is no need to update the cache.
        self.structure.rename(old, new)

    # Used for HARD links
    def link(self, name, target):
        info = self.structure.add_hard_link(name, target)
        self.metadata[info].inc_nlink()

    def utimens(self, path, times=None):
        path_info = self.structure[path]
        self.metadata[path_info].utimens(times)

    # --------------------------------------------------------------------- File methods

    def open(self, path, flags):
        if path not in self.structure:
            raise FuseOSError(errno.ENOENT)
        path_info = self.structure[path]
        self.cache.open(path_info, self.metadata[path_info].stats['st_mtime'])
        return 0

    def create(self, path, mode, fi=None):
        path_info = PathInfo.make()
        self.structure.add(path, path_info)
        self.metadata.add_file(path_info, mode)
        self.cache.create(path_info)
        return 0

    def read(self, path, length, offset, fh):
        path_info = self.structure[path]
        if path_info in self.cache:
            return self.cache.read_bytes(path_info, offset, length)

        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        path_info = self.structure[path]
        if path_info in self.cache:
            bytes_written, size = self.cache.write_bytes(path_info, buf, offset)
            self.metadata[path_info].set_size(size)
            return bytes_written

        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def truncate(self, path, length, fh=None):
        path_info = self.structure[path]
        if path_info in self.cache:
            self.cache.truncate_bytes(path_info, length)
            self.metadata[path_info].set_size(length)
            return

        actual_path = self._actual_path(path)
        with open(actual_path, 'r+') as f:
            f.truncate(length)

    def flush(self, path, fh):
        path_info = self.structure[path]
        if path_info in self.cache:
            self.cache.flush(path_info, force=True)
            return 0

        return os.fsync(fh)

    def release(self, path, fh):
        path_info = self.structure[path]
        if path_info in self.cache:
            self.cache.release(path_info)
            return 0

        return os.close(fh)

    def fsync(self, path, fdatasync, fh):
        return self.flush(path, fh)
