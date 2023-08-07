import os


class FastFile:
    def __init__(self, path: str, mode: str):
        self.path = path
        self.fd = None

        if mode == 'r':
            self.flags = os.O_RDONLY
        elif mode == 'w':
            self.flags = os.O_WRONLY | os.O_CREAT
        else:
            raise ValueError(f'Invalid mode "{mode}" provided, choose between "r" and "w"')

    def __enter__(self):
        self.fd = os.open(self.path, self.flags)
        return self

    def __exit__(self, __exc_type, __exc_value, __traceback):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None

    def write(self, data, offset=0):
        assert self.fd is not None
        os.lseek(self.fd, offset, os.SEEK_SET)
        os.write(self.fd, data)

    def truncate(self, length):
        assert self.fd is not None
        os.truncate(self.fd, length)

    def read(self):
        assert self.fd is not None
        size = os.path.getsize(self.path)
        data = os.read(self.fd, size)
        return data
