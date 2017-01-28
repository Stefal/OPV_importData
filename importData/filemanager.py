#!/usr/bin/python3
# coding: utf-8

from path import path
from potion_client import Client

from .utils import ensure_dir

client = Client("http://localhost:5001")


def addFiles(lot):
    """ Connect to client and get the path"""
    lot.pop('csv', None)

    f = client.File().save()
    ensure_dir(f.path)

    for key, photo in lot.items():
        photo.path.copy(path(f.path) / 'APN{}{}'.format(key, photo.path.ext))

    return f.id
