import requests

IPFS_API = 'http://localhost:5001/api/v0'


def block_put(data):
    r = requests.post(f'{IPFS_API}/block/put', files={'data': data})
    return r.json()['Key']


def block_get(cid):
    r = requests.post(f'{IPFS_API}/block/get?arg={cid}')
    return r.content


def file_write(path, data):
    r = requests.post(f'{IPFS_API}/files/write?arg={path}', files={'data': data})
    print(r)
    print(r.content)


def send_to_ipfs(data, name='data'):
    r = requests.post(f'{IPFS_API}/add', files={name: data})
    cid = r.json()['Hash']
    return cid


def unpin_locally(cid):
    requests.post(f'{IPFS_API}/pin/rm?arg={cid}')


def get_from_ipfs(cid):
    r = requests.post(f'{IPFS_API}/cat?arg={cid}')
    return r.content


def remove_local_block(cid):
    requests.post(f'{IPFS_API}/block/rm?arg={cid}')
