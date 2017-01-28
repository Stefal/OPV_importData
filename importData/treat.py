#!/usr/bin/python3
# coding: utf-8

from . import managedb
from . import filemanager
import datetime
import logging

logger = logging.getLogger("importData." + __name__)
from path import path

def copyImages(lot, dir_manager_client):
    """
    Copy images using DirectoryManagerClient.
    :param lot: A list of ('Csv':[], 0: '/tt/aa/APN0/IMG_00.JPG' ...)
    :param dir_manager_client: A DirectoryManagerClient.
    """
    l = lot.copy()
    l.pop('csv', None)

    with dir_manager_client.Open() as (uuid, dir_path):
        for key, photo in l.items():
            photo.path.copy(path(dir_path) / 'APN{}{}'.format(key, photo.path.ext))

    return uuid

def treat(campaign, l, dir_manager_client):
    """ Push hard in DB and return lot"""
    try:
        sensorsData = l['csv'].data
    except KeyError:
        sensorsData = {'gps': {'lat': 0, 'lon': 0, 'alt': 0},
                       'compass': {'degree': 0, 'minutes': 0},
                       'takenDate': 0,
                       'goproFailed': 0}

    sensors = managedb.make_sensors(sensorsData['gps']['lat'],
                                    sensorsData['gps']['lon'],
                                    sensorsData['gps']['alt'],
                                    sensorsData['compass']['degree'],
                                    sensorsData['compass']['minutes'])

    uuid = copyImages(l, dir_manager_client)

    date = datetime.datetime.fromtimestamp(sensorsData['takenDate'])
    lot = managedb.make_lot(campaign,
                            uuid,
                            sensors,
                            sensorsData['goproFailed'],
                            date)

    if len(l) != 7:
        logging.info("Malformed lot n°{}".format(lot.id))
    logging.info("Lot n°{} generated".format(lot.id))

    return lot
