import random
import string
from base64 import b64decode, b64encode
from typing import NamedTuple

import nacl.pwhash
import nacl.secret
import nacl.utils


def random_id(k):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=k))


class PathInfo(NamedTuple):
    path_id: str
    link_to_path: str
    key: bytes
    iv: bytes

    @staticmethod
    def make(path_id=None, key=None, iv=None, link_to_path=None):
        path_id = path_id if path_id is not None else random_id(10)
        key = key if key is not None else nacl.utils.random(16)
        iv = iv if iv is not None else nacl.utils.random(16)
        return PathInfo(path_id=path_id, key=key, iv=iv, link_to_path=link_to_path)

    @staticmethod
    def make_symlink(link_to_path):
        return PathInfo.make(link_to_path=link_to_path)

    @staticmethod
    def make_only_id(path_id=None):
        path_id = path_id if path_id is not None else random_id(10)
        return PathInfo(path_id, link_to_path=None, key=b'', iv=b'')

    def __repr__(self):
        return f'Path(path_id="{self.path_id}")'

    def __eq__(self, other):
        return isinstance(other, PathInfo) and self.path_id == other.path_id

    def to_dict(self):
        return {
            'path_id': self.path_id,
            'link_to_path': self.link_to_path,
            'key': b64encode(self.key).decode('ascii'),
            'iv': b64encode(self.iv).decode('ascii'),
        }

    @staticmethod
    def from_dict(data):
        return PathInfo(
            path_id=data['path_id'],
            link_to_path=data['link_to_path'],
            key=b64decode(data['key'].encode('ascii')),
            iv=b64decode(data['iv'].encode('ascii')))
