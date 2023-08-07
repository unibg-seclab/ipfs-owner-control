from pathlib import Path

from utils.trie import Node, Trie
from .pathinfo import PathInfo


def parts(path):
    return Path(path).parts


class PathStructure:
    def __init__(self, trie=None):
        self.trie = trie if trie is not None else Trie(Node(None, {'/': Node(PathInfo.make_only_id())}))

    def to_dict(self):
        return self.trie.to_dict()

    @staticmethod
    def from_dict(data):
        def transform(d):
            if d is None:
                return None
            else:
                return PathInfo.from_dict(d)

        trie = Trie.from_dict(data, transform=transform)
        return PathStructure(trie)

    def _get(self, path):
        return self.trie[parts(path)].value

    # ------------------------------------------------------ Dunder methods

    def __contains__(self, path):
        return parts(path) in self.trie

    def __getitem__(self, path):
        return self.get(path, follow_symlinks=True)

    def __delitem__(self, path):
        del self.trie[parts(path)]

    # ------------------------------------------------------ Getting, creating and moving Info around

    def contents(self, path):
        return self.trie[parts(path)].contents()

    def add(self, path, entry):
        self.trie[parts(path)] = Node(entry)

    def add_hard_link(self, from_path, to_path):
        target = self[to_path]
        self.add(from_path, target)
        return target

    def rename(self, old, new):
        self.trie.move(parts(old), parts(new))

    def get(self, path, follow_symlinks=True):
        current = path
        item = self._get(current)

        while follow_symlinks and item.link_to_path is not None:
            current = (Path(current).parent / item.link_to_path).resolve()
            item = self._get(str(current))

        return item
