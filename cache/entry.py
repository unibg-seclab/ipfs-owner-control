from time import time


class CacheEntry:
    def __init__(self, content, mtime=None):
        self.content = content
        self.opens = 1  # number of concurrent apps with this file open
        self.modified = True if not mtime else False
        self.atime = int(time())
        self.mtime = self.atime if not mtime else mtime

    @property
    def size(self):
        return len(self.content)
