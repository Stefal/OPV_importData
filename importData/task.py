#!/usr/bin/python3
# coding: utf-8

import celery
import potion_client

app = celery.Celery('tasks', backend='redis://localhost/', broker='redis://localhost//')

client = potion_client.Client('http://localhost:5000')


@app.task
def assemble(id_lot):
    """ Assemble lot"""
    lot = client.Lot(id_lot)
    # Do a lot of thing
    return
