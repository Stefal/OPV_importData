#!/usr/bin/python3
# coding: utf-8

import os
import logging
import datetime
from . import managedb
from path import Path

logger = logging.getLogger("importData." + __name__)

def copyImages(lot, dir_manager_client, hardlink=False):
    """
    Copy images using DirectoryManagerClient.
    :param lot: A list of ('Csv':[], 0: '/tt/aa/APN0/IMG_00.JPG' ...)
    :param dir_manager_client: A DirectoryManagerClient.
    :param hardlink: Tell we should hardlink into DM.
                     Will force hardlinking, take care that it's on the same device
                     (you should set DM workspace_directory on the same device).
    """
    l = lot.copy()
    l.pop('csv', None)

    with dir_manager_client.Open() as (uuid, dir_path):
        for key, photo in l.items():
            dest = Path(dir_path) / 'APN{}{}'.format(key, photo.path.ext)
            if hardlink:
                logger.debug("Hardlinking : {} -> {}".format(photo.path, dest))
                os.link(photo.path, dest)
            else:
                photo.path.copy(dest)

    return uuid

def treat(id_malette, campaign, l, dir_manager_client, hardlinking=False):
    """ Push hard in DB and return lot"""
    try:
        sensorsData = l['csv'].data
    except KeyError:
        sensorsData = {'gps': {'lat': 0, 'lon': 0, 'alt': 0},
                       'compass': {'degree': 0, 'minutes': 0},
                       'takenDate': 0,
                       'goproFailed': 0}


    sensors = managedb.make_sensors(id_malette,
                                    lng = sensorsData['gps']['lon'],
                                    alt = sensorsData['gps']['alt'],
                                    lat = sensorsData['gps']['lat'],
                                    degrees = sensorsData['compass']['degree'],
                                    minutes = sensorsData['compass']['minutes'])

    uuid = copyImages(l, dir_manager_client, hardlinking)

    date = datetime.datetime.fromtimestamp(sensorsData['takenDate'])
    lot = managedb.make_lot(id_malette,
                            campaign = campaign,
                            pictures_path = uuid,
                            sensors = sensors,
                            goprofailed = sensorsData['goproFailed'],
                            takenDate = date)

    if len(l) != 7:
        logging.info("Malformed lot n°{}".format(lot.id))
    logging.info("Lot n°{} generated".format(lot.id))

    return lot
