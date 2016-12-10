import time
import datetime
import exifread

import csv
import json

from collections import namedtuple, defaultdict

import os.path
from os import walk, link

import re

from utils import ensure_dir, Config

Photo = namedtuple("Photo", ["timestamp", "path"])
Csv = namedtuple("Csv", ["timestamp", "data"])

def readEXIFTime(picPath):
    """
    Read DateTimeOriginal tag from exif data
    return timestamp
    """
    with open(picPath, "rb") as f:
        tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal')

    timestamp = int(time.mktime(datetime.datetime.strptime(tags['EXIF DateTimeOriginal'].values, "%Y:%m:%d %H:%M:%S").timetuple()))

    return timestamp

def listImgsByAPN(srcDir):
    """
    return the list of all images in srcDir and sort them by APN (in a dict)
    """
    r = re.compile('APN[0-9]+')
    j = re.compile('.+\.(jpeg|jpg)', re.IGNORECASE)

    def isJpg(x):
        """return true if string x finish by jpg/jpeg"""
        return j.match(x)

    def isAPN(x):
        """return true if string x is APN* """
        return r.match(x)

    imgListByApn = []

    for (dirpath, _, filenames) in walk(srcDir):
        if isAPN(os.path.basename(dirpath)):
            imgListByApn.append((dirpath, list(filter(isJpg, filenames))))

    return imgListByApn


def getImgData(srcDir):
    """
    get all the data from scrDir (img, timestamps...)
    """
    d = listImgsByAPN(srcDir)

    imgData = defaultdict(list)

    for dirpath, listImg in d:
        for imgName in listImg:
            imgPath = os.path.join(dirpath, imgName)
            # extract the apn number from the last segment of dirpath (APN0, 1...)
            apnNo = int(re.search(r"\d+", os.path.basename(dirpath)).group(0))

            imgData[apnNo].append(Photo(readEXIFTime(imgPath), imgPath))
    return imgData

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

def levelTimestamps(apns, method=min):
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

def makeLots(srcDir, csvFile):
    """
    Make the full lot
    """
    epsilon = 6

    data = getImgData(srcDir)
    data['csv'] = readCSV(csvFile)

    data = levelTimestamps(data)
    data = sortAPNByTimestamp(data)
    lots = list()

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
        lots.append(lot)

    return lots

def moveLotPictures(lot, outFolder):
    ensure_dir(outFolder)

    for k in lot:
        if k != "csv":  # if it's dirpath
            src = lot[k].path
            dst = os.path.join(outFolder, "APN"+str(k)+".JPG")
            link(src, dst)
        else:  # it's the CSV
            data = lot[k].data
            dst = os.path.join(outFolder, "sensors.json")
            f = open(dst, 'w')
            json.dump(data, f)
            f.close()

def moveAllPictures(lots, outFolder):
    for lotNb, lot in enumerate(lots):
        moveLotPictures(lot, os.path.join(outFolder, str(lotNb)))

def readCSV(filename):
    """
    Read the CSV file which correspond to the operation
    CSV is
    timestamp,lat,long,alt,degree°minutes,goproFailed
    return a list of Csv
    """
    data = []

    passHeader = False
    with open(filename, 'r') as csvFile:
        d = csv.reader(csvFile, delimiter=';')
        for row in d:
            if not passHeader:
                passHeader = True
                continue
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


if __name__ == "__main__":
    conf = Config('config/main.json')
    campaign = input('please enter campaign name: ')

    srcDir = os.path.expanduser(conf["data_dir"].format(campaign=campaign))
    csvFile = os.path.join(srcDir, campaign + '.csv')
    lotsOutput = os.path.expanduser(conf["lots_output_dir"].format(campaign=campaign))

    lots = makeLots(srcDir, csvFile)
    moveAllPictures(lots, lotsOutput)
