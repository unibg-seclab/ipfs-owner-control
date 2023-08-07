import stat
import time
import os

from enum import Enum

# For now, RWX for the current user and RX for everyone
DEFAULT_MODE = 0o755


class PathType(Enum):
    FILE = 'file'
    DIR = 'dir'
    SYMLINK = 'symlink'

    def stat_flags(self):
        assocs = {
            PathType.FILE: stat.S_IFREG,
            PathType.DIR: stat.S_IFDIR,
            PathType.SYMLINK: stat.S_IFREG | stat.S_IFLNK
        }

        return assocs[self]


class PathMetadata:
    def __init__(self, stats=None, path_type=None, mode=DEFAULT_MODE):
        if stats:
            self.stats = {**stats}
        else:
            now = time.time()
            self.stats = {
                'st_mode': mode,
                'st_size': 0,
                'st_nlink': 2 if path_type == PathType.DIR else 1,
                'st_atime': now,
                'st_ctime': now,
                'st_gid': os.getgid(),
                'st_mtime': now,
                'st_uid': os.getuid()
            }

        if path_type is None:
            extra_mode = 0
        else:
            extra_mode = path_type.stat_flags()

        self.stats['st_mode'] = extra_mode | self.stats['st_mode']

    def _mode_has(self, flag):
        return self.stats['st_mode'] & flag == flag

    def is_file(self):
        return self._mode_has(stat.S_IFREG)

    def is_dir(self):
        return self._mode_has(stat.S_IFDIR)

    def chmod(self, mode):
        self.stats['st_mode'] = mode

    def chown(self, uid, gid):
        self.stats['st_uid'] = uid
        self.stats['st_gid'] = gid

    def utimens(self, times=None):
        now = time.time()
        (atime, mtime) = times if times is not None else (now, now)
        self.stats['st_atime'] = atime
        self.stats['st_mtime'] = mtime

    def set_size(self, size):
        self.stats['st_size'] = size

    @property
    def nlink(self):
        return self.stats['st_nlink']

    def inc_nlink(self):
        self.stats['st_nlink'] += 1

    def dec_nlink(self):
        self.stats['st_nlink'] -= 1

    def to_dict(self):
        return self.stats

    @staticmethod
    def from_dict(data):
        return PathMetadata(stats=data)
