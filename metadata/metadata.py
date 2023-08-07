from pathlib import Path
from structure.pathinfo import PathInfo
from .pathmetadata import DEFAULT_MODE, PathMetadata, PathType


class Metadata:
    def __init__(self, root: Path, data=None):
        self.root = root
        self.data = data if data is not None else {}

    # ------------------------------------------------------ Dunder methods

    def __contains__(self, path: PathInfo):
        return path.path_id in self.data

    def __getitem__(self, path: PathInfo):
        return self.data[path.path_id]

    def __setitem__(self, path: PathInfo, value: PathMetadata):
        self.data[path.path_id] = value

    def __delitem__(self, path: PathInfo):
        del self.data[path.path_id]

    # ------------------------------------------------------ Adding new entries

    def add_file(self, path: PathInfo, mode=DEFAULT_MODE):
        self[path] = PathMetadata(path_type=PathType.FILE, mode=mode)

    def add_dir(self, path: PathInfo, mode=DEFAULT_MODE):
        self[path] = PathMetadata(path_type=PathType.DIR, mode=mode)

    def add_soft_link(self, path: PathInfo, mode=DEFAULT_MODE):
        self[path] = PathMetadata(path_type=PathType.SYMLINK, mode=mode)

    # ------------------------------------------------------ Dict conversions

    def to_dict(self):
        data = {}

        for k, v in self.data.items():
            data[k] = v.to_dict()

        return data

    @staticmethod
    def from_dict(root: Path, data: dict):
        tmp = {}

        # Hard links must be done afterwards,
        # since they have to modify the st_nlink
        # of existig files

        for k, v in data.items():
            tmp[k] = PathMetadata.from_dict(v)

        return Metadata(root=root, data=tmp)
