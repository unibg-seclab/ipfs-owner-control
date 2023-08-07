from enum import Enum
from .entry import CacheEntry


class EvictionTechnique(Enum):
    LRU = 'LRU'

    def __call__(self, entry: CacheEntry):
        if self == EvictionTechnique.LRU:
            return entry.mtime


def values():
    return [e.value for e in EvictionTechnique]
