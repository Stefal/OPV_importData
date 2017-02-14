#!/usr/bin/python3
# coding: utf-8

from . import managedb
import datetime
import logging

logger = logging.getLogger("importData." + __name__)
from path import Path

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
            photo.path.copy(Path(dir_path) / 'APN{}{}'.format(key, photo.path.ext))

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

    sensors = managedb.make_sensors(lng = sensorsData['gps']['lon'],
                                    alt = sensorsData['gps']['alt'],
                                    lat = sensorsData['gps']['lat'],
                                    degree = sensorsData['compass']['degree'],
                                    minutes = sensorsData['compass']['minutes'])

    uuid = copyImages(l, dir_manager_client)

    date = datetime.datetime.fromtimestamp(sensorsData['takenDate'])
    lot = managedb.make_lot(campaign = campaign,
                            picture_path = uuid,
                            sensors = sensors,
                            goprofailed = sensorsData['goproFailed'],
                            takenDate = date)

    if len(l) != 7:
        logging.info("Malformed lot n°{}".format(lot.id))
    logging.info("Lot n°{} generated".format(lot.id))

    return lot
