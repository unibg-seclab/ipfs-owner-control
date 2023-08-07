import math
import os
import threading
import errno

from time import time
from fuse import FuseOSError
from typing import Callable, Any
from pathlib import Path

import utils.mixslice as MixSlice
from structure.pathinfo import PathInfo
from utils.filebytecontent import FileByteContent

from .entry import CacheEntry
from .eviction import EvictionTechnique


LOCK = threading.Lock()


class Cache:
    def __init__(self,
                 root: Path,
                 eviction_technique=EvictionTechnique.LRU,
                 ipfs_cids=None,
                 memory_cap=math.inf):
        self.root = root
        self.files = {}
        self.evicted = {}

        self.ipfs_cids = ipfs_cids

        self.memory_cap = memory_cap
        self.total_size = 0
        self.eviction_technique = eviction_technique

    @property
    def free_space(self):
        return self.memory_cap - self.total_size

    def __contains__(self, path: PathInfo):
        return path in self.files

    # ------------------------------------------------------ Helpers

    def _decrypt(self, path: PathInfo):
        actual_path = self.root / path.path_id
        cids = self.ipfs_cids[path.path_id]
        return MixSlice.decrypt(actual_path, path.key, path.iv, cids=cids)

    def _encrypt(self, path: PathInfo):
        entry = self.files[path]
        plaintext = entry.content.read_all()
        dest = (self.root / path.path_id).absolute()

        cids = MixSlice.encrypt(
            data=plaintext,
            path=dest,
            key=path.key,
            iv=path.iv)

        self.ipfs_cids[path.path_id] = cids

    def _apply_to_file(self, path: PathInfo, f: Callable[[CacheEntry], Any]):
        file = self.files[path]

        prev_size = len(file.content)
        res, new_content = f(file)
        new_size = len(new_content)

        if prev_size != new_size:
            with LOCK:
                self.total_size = self.total_size - prev_size + new_size

        return res

    def _free_space(self, target=0):
        if self.free_space >= target:
            return

        with LOCK:
            items = self.files.items()

        items = sorted(
            items, key=lambda pair: self.eviction_technique(pair[1]))

        while self.free_space < target and len(items) > 0:
            (path, entry) = items.pop(0)
            self._evict(path, entry)

    def _evict(self, path: PathInfo, entry: CacheEntry):
        self.flush(path)
        self.release(path, force=True)
        with LOCK:
            entry.content = None
            self.evicted[path] = entry

    def _unevict(self, path: PathInfo):
        entry = self.evicted[path]
        del self.evicted[path]

        plaintext = FileByteContent(self._decrypt(path))
        entry.content = plaintext
        return entry

    def _load(self, path: PathInfo, mtime=None):
        with LOCK:
            if path in self.files:
                return False

            freshly_created = False
            if path in self.evicted:
                entry = self._unevict(path)
            else:
                plaintext = FileByteContent(self._decrypt(path))
                entry = CacheEntry(plaintext, mtime)
                freshly_created = True

        self._insert_entry(path, entry)
        return freshly_created

    def _insert_entry(self, path: PathInfo, entry: CacheEntry):
        if entry.size > self.memory_cap:
            raise FuseOSError(errno.ENOMEM)
        self._free_space(target=entry.size)
        with LOCK:
            self.files[path] = entry
            self.total_size += entry.size

    # ------------------------------------------------------ Opening and creating

    def open(self, path: PathInfo, mtime):
        freshly_created = self._load(path, mtime)
        with LOCK:
            if not freshly_created and path in self.files:
                self.files[path].opens += 1
                return

    def create(self, path: PathInfo):
        with LOCK:
            if path in self.files:
                self.files[path].opens += 1
                return

            entry = self._unevict(path) if path in self.evicted else None

        if entry:
            self._insert_entry(entry)
            return

        with LOCK:
            plaintext = FileByteContent(b'')
            self.files[path] = CacheEntry(plaintext)
            # Here self.files[path].size is obviously 0, so no need to free space

        self.flush(path)

    # ------------------------------------------------------ Reading and writing

    def read_bytes(self, path: PathInfo, offset, length):
        self._load(path)

        with LOCK:
            if path not in self.files:
                return None
        content = self.files[path].content
        return content.read_bytes(offset, length)

    def write_bytes(self, path: PathInfo, buf, offset):
        self._load(path)

        with LOCK:
            if path not in self.files:
                return 0

        def write(file):
            bytes_written = file.content.write_bytes(buf, offset)
            return bytes_written, file.content

        bytes_written = self._apply_to_file(path, write)

        self.files[path].modified = True
        self.files[path].mtime = int(time())

        return bytes_written, self.files[path].size

    def truncate_bytes(self, path: PathInfo, length):
        self._load(path)

        with LOCK:
            if path not in self.files:
                return

        def truncate(file):
            file.content.truncate(length)
            return None, file.content

        self._apply_to_file(path, truncate)

        self.files[path].modified = True
        self.files[path].mtime = int(time())

    # ------------------------------------------------------ Closing files

    def flush(self, path: PathInfo, force=True):
        with LOCK:
            if path not in self.files:
                return

            entry = self.files[path]

        disk_path = (self.root / path.path_id).absolute()
        file_already_exists = os.path.exists(disk_path)
        if file_already_exists:
            os.utime(disk_path, (entry.atime, entry.mtime))

        with LOCK:
            if entry.modified or force:
                self._encrypt(path)
                entry.modified = False
            else:
                return

        if not file_already_exists:
            os.utime(disk_path, (entry.atime, entry.mtime))

    def release(self, path: PathInfo, force=False):
        def release_from(store):
            file = store[path]
            file.opens -= 1
            if not file.opens or force:
                del store[path]
            return file

        with LOCK:
            if path in self.evicted:
                release_from(self.evicted)
            elif path in self.files:
                file = release_from(self.files)
                if not file.opens or force:
                    self.total_size -= file.size
