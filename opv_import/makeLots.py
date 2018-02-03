#!/usr/bin/python3
# coding: utf-8

import re
import logging
from path import Path
from os import walk, listdir
from collections import namedtuple, defaultdict
from opv_import.pictures_utils import read_exif_time as pic_read_exif_time
from opv_import.rederbro_utils import read_rederbro_csv

logger = logging.getLogger("importData." + __name__)

# -- Script description
# 1 - make GoPro lot (ImageSet)
# 2 - filter and group rederbro CSV datas
# 3 - execute search reference algorithm for each group of rederbro CSV data
# 4 - associate data with found references


###
# Data Structures
###
Photo = namedtuple("Photo", ["timestamp", "path"])
Csv = namedtuple("Csv", ["timestamp", "data"])

# TODO : use a real model in this package !! namedtuple shouldn't be in this file, we should have one for sensors data also

###
# utilities fct to list images
###

def listImgsByAPN(src_dir: str):
    """
    Fetch all images in srcDir under APNx directories (and their subdirectories).
    Return them in a dict where the key is the apnNo the value a list a images Path.

    :param srcDir: Source directory should contain APN[0-9] subdirectories with images (images might be under subdirectories it also works
    :return: Return them in a dict where the key is the apnNo the value a list a images Path.
             {0: [Path("srcDir/APN0/sudir/img.jpg"), .....], 1: [Path("srcDir/APN1/img.jpg"), .....], ... 6: [...] }
    """
    logger.info("Start listing images")
    imgListByApn = defaultdict(list)

    r = re.compile('APN[0-9]+')
    j = re.compile('.+\.(jpeg|jpg)', re.IGNORECASE)

    def isJpg(x):
        """return true if string x finish by jpg/jpeg"""
        return j.match(x)

    def isAPN(x):
        """return true if string x is APN* """
        return r.match(x)

    def getApnNum(dirpath):
        """
        Return APN number from directory name "srcDir/APNx".
        :param dirpath: dir path "srcDir/APNx"
        :return: x the apnNo
        """
        return int(re.search(r"\d+", Path(dirpath).basename()).group(0))

    def getAllPic(basedir):
        """
        Return all Path of JPG files in basedir and it's subdirectories.
        :param dirpath: directory to explore
        :return: List of pic path [Path(basedir/picA.jpg), ...]
        """
        pics = list()
        for dirpath, _, filenames in walk(basedir):
            for f in filenames:
                if isJpg(f):
                    pics.append(Path(dirpath) / f)
        return pics

    for apnDir in listdir(src_dir):  # Fetch cameras folders
        if isAPN(apnDir):  # check it's a camera folder
            fullpath = Path(src_dir) / apnDir
            apnNo = getApnNum(fullpath)
            imgListByApn[apnNo] = getAllPic(fullpath)   # getting all pictures in it and it's subdirectories

            if len(imgListByApn[apnNo]) == 0:
                logger.warning("No image founded for camera {} in {}".format(str(apnNo), fullpath))

    logger.debug("Fetched pictures for each cameras : ")
    logger.debug(imgListByApn)
    return imgListByApn

def getImgData(p: str) -> Photo:
    return Photo(pic_read_exif_time(p), Path(p))

def getImgsData(srcDir: str) -> dict:
    """
    get all the data from scrDir (img, timestamps...)
    """
    pictures_by_apn = listImgsByAPN(srcDir)
    imgData = {apnNo: [getImgData(pic_path) for pic_path in pictures_paths] for apnNo, pictures_paths in pictures_by_apn.items()}
    logger.debug("Images with ts : ")
    logger.debug(imgData)
    return imgData

def getImgsDataBis(srcDir: str):
    """
    get all the data from scrDir (img, timestamps...)
    """
    d = listImgsByAPN(srcDir)

    imgData = defaultdict(list)

    for dirpath, listImg in d.items():
        # extract the apn number from the last segment of dirpath (APN0, 1...)
        apnNo = int(re.search(r"\d+", Path(dirpath).basename()).group(0))

        for imgName in listImg:
            imgPath = Path(dirpath) / imgName
            imgData[apnNo].append(getImgData(imgPath))

    return imgData

###
# Utilies fct to help finding lots
###


def sortAPNByTimestamp(apns, reverse=False):
    """Sort all data by timestamp"""
    apnSorted = {apn: sorted(vals, key=lambda x: x.timestamp, reverse=reverse) for apn, vals in apns.items()}

    return apnSorted


def findOffset(apns, method=max):
    """
    Find the first valable offset
    There is multiple methods:
    - min -> the first lot is working
    - max -> the last lot is working
    """
    offsets = {}
    for apn, vals in apns.items():
        if vals:
            offsets[apn] = method(v.timestamp for v in vals)
    return offsets


def levelTimestamps(apns: dict, method=max) -> dict:
    """
    Map timestamps to 0..
    methods:
    - min -> level 1st photo to 0
    - max -> level -1st photo to 0
    - otherwise: TODO
    """
    logger.info("Level timestamps for " + ("first (oldest) lot" if method == min else " last (newest) lot"))
    n_apns = defaultdict(list)

    if method is min or method is max:
        offsets = findOffset(apns, method)

        for k in apns.keys():
            for v in apns[k]:
                n_apns[k].append(v._replace(timestamp=v.timestamp - offsets[k]))
    return n_apns

###
# Main part of the function
###


def makeLots(srcDir: str, csvFile: str, firstLotRef=True) -> list:
    """
    Make all the lots
    return a list of lots
    """
    logger.info("Starting making lots")
    epsilon = 6
    counters = {"no_csv": 0, "null_gps": 0}

    data = getImgsData(srcDir)
    data['csv'] = read_rederbro_csv(csvFile)

    data = levelTimestamps(data, method=min if firstLotRef else max)
    data = sortAPNByTimestamp(data)

    # The algorithme try to combine photos taken with
    # less than 6 sec of interval
    # to make a lot, if no photo found,
    # the lot is incomplet but can be created
    changed_data = True
    while changed_data:
        changed_data = False

        # import ipdb; ipdb.set_trace();
        # The part of the data we will treat (maybe a lot)
        p = {k: v[0].timestamp for k, v in data.items() if len(v)}

        if len(p) == 0:  # == if data is empty => no more values to treat
            break

        if "csv" in p.keys() and data['csv'][0].data['goproFailed'] == 111111:  # all gopro failed
            logger.debug("Removing CSV entry")
            del data["csv"][0]
            changed_data = True
            continue

        min_val = min(p.values())

        # The list of all keys that have an img in current lot
        keys = [k for k, v in p.items() if v - min_val < epsilon]

        if len(keys) == 1 and keys[0] == 'csv':  # prevent timing errors on gopros pictures meta
            data["csv"].pop(0)
            changed_data = True
            continue

        lot = {}
        for k in keys:
            changed_data = True
            lot[k] = data[k][0]
            logger.debug("-- makeLots --")
            logger.debug(lot)
            del data[k][0]

        if not("csv" in lot):
            logger.warning("No CSV associated")
            counters["no_csv"] += 1
            counters["null_gps"] += 1
        elif float(lot["csv"].data['gps']['lon']) == 0 and float(lot["csv"].data['gps']['lat']) == 0:
            counters["null_gps"] += 1

        yield lot

    logger.info("All lots generated")
    logger.info(counters)
