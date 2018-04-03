#!/usr/bin/python3
# coding: utf-8

import os
import logging
import datetime
from . import managedb
from path import Path
from opv_api_client import ressources
from opv_import.makelot import Lot
from opv_directorymanagerclient import DirectoryManagerClient

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
    logger.debug(" -- treat --")
    logger.debug(l)
    try:
        sensorsData = l['csv'].data
    except KeyError:
        sensorsData = {'gps': {'lat': 0, 'lon': 0, 'alt': 0},
                       'compass': {'degree': 0, 'minutes': 0},
                       'takenDate': 0,
                       'goproFailed': 0}

    logger.debug("-- sensorsData --")
    logger.debug(sensorsData)
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

def apnGoProError(bools):
    val = 0
    for k in bools:
        mask = bools[k] << k
        val |= mask
    return val

def treat_new(id_malette: int, campaign: ressources.Campaign, l: Lot, dir_manager_client: DirectoryManagerClient, hardlinking: bool=False):
    """ Push hard in DB and return lot"""
    logger.debug(" -- Treat new version --")
    logger.debug(l)

    if l.meta is not None:
        sensorsData = {'gps': {'lat': l.meta.geopoint.lat, 'lon': l.meta.geopoint.lon, 'alt': l.meta.geopoint.alt},
                       'compass': {'degree': l.meta.orientation.degree, 'minutes': l.meta.orientation.minutes},
                       'takenDate': l.meta.timestamp,
                       'goproFailed': apnGoProError(l.meta.gopro_errors)}
    else:
        sensorsData = {'gps': {'lat': 0, 'lon': 0, 'alt': 0},
                       'compass': {'degree': 0, 'minutes': 0},
                       'takenDate': 0,
                       'goproFailed': 0}

    logger.debug("-- sensorsData --")
    logger.debug(sensorsData)
    sensors = managedb.make_sensors(id_malette,
                                    lng = sensorsData['gps']['lon'],
                                    alt = sensorsData['gps']['alt'],
                                    lat = sensorsData['gps']['lat'],
                                    degrees = sensorsData['compass']['degree'],
                                    minutes = sensorsData['compass']['minutes'])

    uuid = copyImages(l.cam_set, dir_manager_client, hardlinking)

    date = datetime.datetime.fromtimestamp(sensorsData['takenDate'])
    lot = managedb.make_lot(id_malette,
                            campaign = campaign,
                            pictures_path = uuid,
                            sensors = sensors,
                            goprofailed = sensorsData['goproFailed'],
                            takenDate = date)

    # if len(l) != 7:
    #     logging.info("Malformed lot n°{}".format(lot.id))
    logging.info("Lot n°{} generated".format(lot.id))

    return lot
