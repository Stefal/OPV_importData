import tarfile
from path import path
from potion_client import Client
from utils import ensure_dir

client = Client("http://localhost:5001")

def addFiles(lot):
    lot.pop('csv', None)

    f = client.File().save()
    tar_path = path(f.path) / 'photos.tar.gz'
    ensure_dir(f.path)

    tarify(lot, tar_path)

    return f.id

def tarify(lot, dst):
    tar = tarfile.open(dst, mode="w:gz")
    for key, photo in lot.items():
        tar.add(photo.path, 'APN{}{}'.format(key, photo.path.ext))
    tar.close()
