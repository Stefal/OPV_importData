import csv
from collections import namedtuple, defaultdict
import re

from path import path
from os import walk

import time
import datetime
import exifread

###
# Logging utilities
###
import logging

logger = logging.getLogger("makelots")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')

# Will log on the terminal
steam_handler = logging.StreamHandler()
steam_handler.setLevel(logging.DEBUG)
logger.addHandler(steam_handler)

###
# Data Structures
###

Photo = namedtuple("Photo", ["timestamp", "path"])
Csv = namedtuple("Csv", ["timestamp", "data"])

###
# utilities fct to list images
###

def readEXIFTime(picPath: str) -> int:
    """
    Read DateTimeOriginal tag from exif data
    return timestamp
    """
    with open(picPath, "rb") as f:
        tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal')

    timestamp = int(time.mktime(datetime.datetime.strptime(tags['EXIF DateTimeOriginal'].values, "%Y:%m:%d %H:%M:%S").timetuple()))

    return timestamp

def listImgsByAPN(srcDir: str) -> dict:
    """
    return the list of all images in srcDir and sort them by APN
    """
    logger.debug("Start listing images")
    r = re.compile('APN[0-9]+')
    j = re.compile('.+\.(jpeg|jpg)', re.IGNORECASE)

    def isJpg(x):
        """return true if string x finish by jpg/jpeg"""
        return j.match(x)

    def isAPN(x):
        """return true if string x is APN* """
        return r.match(x)

    imgListByApn = defaultdict(list)

    for (dirpath, _, filenames) in walk(srcDir):
        if isAPN(path(dirpath).basename()):
            imgListByApn[dirpath] = list(filter(isJpg, filenames))

            if len(imgListByApn[dirpath]) == 0:
                logger.warning("No image founded in {}".format(dirpath))

    logger.debug("All images listed")
    return imgListByApn

def getImgData(p: str) -> Photo:
    return Photo(readEXIFTime(p), path(p))

def getImgsData(srcDir: str) -> dict:
    """
    get all the data from scrDir (img, timestamps...)
    """
    d = listImgsByAPN(srcDir)

    imgData = defaultdict(list)

    for dirpath, listImg in d.items():
        for imgName in listImg:
            imgPath = path(dirpath) / imgName
            # extract the apn number from the last segment of dirpath (APN0, 1...)
            apnNo = int(re.search(r"\d+", path(dirpath).basename()).group(0))

            imgData[apnNo].append(getImgData(imgPath))
    return imgData

###
# Utilies fct to help finding lots
###

def sortAPNByTimestamp(apns, reverse=False):
    """Sort all data by timestamp"""
    apnSorted = {apn: sorted(vals, key=lambda x: x.timestamp) for apn, vals in apns.items()}

    if reverse:
        apnSorted = apnSorted[::-1]

    return apnSorted

def findOffset(apns, method=min):
    """
    Find the first valable offset
    There is multiple methods:
    - min -> the first lot is working
    - max -> the last lot is working
    """
    offsets = {}
    for apn, vals in apns.items():
        offsets[apn] = method(v.timestamp for v in vals)
    return offsets

def levelTimestamps(apns: dict, method=min) -> dict:
    """
    Map timestamps to 0..
    methods:
    - min -> level 1st photo to 0
    - max -> level -1st photo to 0
    - otherwise: TODO
    """
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

def makeLots(srcDir: str, csvFile: str) -> list:
    """
    Make all the lots
    return a list of lots
    """
    logger.info("Starting making lots")
    epsilon = 6

    data = getImgsData(srcDir)
    data['csv'] = readCSV(csvFile)

    data = levelTimestamps(data)
    data = sortAPNByTimestamp(data)

    # The algorithme try to combine photos taken with
    # less than 6 sec of interval
    # to make a lot, if no photo found,
    # the lot is incomplet but can be created
    while True:
        # The part of the data we will treat (maybe a lot)
        p = {k: v[0].timestamp for k, v in data.items() if len(v)}

        if len(p) == 0:  # == if data is empty => no more values to treat
            break

        min_val = min(p.values())

        # The list of all keys that have an img in current lot
        keys = [k for k, v in p.items() if v - min_val < epsilon]

        if len(keys) == 1 and keys[0] == 'csv':  # prevent timing errors on gopros pictures meta
            data = levelTimestamps(data)
            continue

        lot = {}
        for k in keys:
            lot[k] = data[k][0]
            del data[k][0]

        yield lot

    logger.info("All lots generated")

    return lots

def readCSV(csv_path: str) -> list:
    """
    Read the CSV file which correspond to the operation
    CSV is
    timestamp,lat,long,alt,degree°minutes,goproFailed
    return a list of Csv
    """
    data = []

    passHeader = False
    with open(csv_path, 'r') as csvFile:
        d = csv.reader(csvFile, delimiter=';')
        for row in d:

            # pass the first line
            if not passHeader:
                passHeader = True
                continue

            # Convert data in a more writable way
            timestamp = int(time.mktime(time.strptime(row[0])))
            lat = float(row[1])
            lng = float(row[2])
            alt = float(row[3])
            degree, minutes = row[4].split('\u00b0')
            degree = float(degree)
            minutes = float(minutes[1:-1])
            goproFailed = int(row[5])

            sensorsMeta = {
                "takenDate": timestamp,
                "gps": {
                    "lat": lat,
                    "lon": lng,
                    "alt": alt
                },
                "compass": {
                    "degree": degree,
                    "minutes": minutes
                },
                "goproFailed": goproFailed
            }

            data.append(Csv(timestamp, sensorsMeta))
    return data
