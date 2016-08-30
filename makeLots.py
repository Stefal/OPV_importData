import time
import datetime
import exifread

import csv

from os import walk
import os.path
import re

def readEXIFTime(picPath):
    with open(picPath, "rb") as f:
        tags = exifread.process_file(f, stop_tag='EXIF DateTimeOriginal')

    timestamp = int(time.mktime(datetime.datetime.strptime(tags['EXIF DateTimeOriginal'].values, "%Y:%m:%d %H:%M:%S").timetuple()))

    return timestamp

def listImgsByAPN(srcDir):
    r = re.compile('APN[0-9]+')
    j = re.compile('.+\.(jpeg|jpg)', re.IGNORECASE)
    isJpg = lambda x: j.match(x)
    isAPN = lambda x: r.match(x)
    return {dirpath: filter(isJpg, filenames) for (dirpath,_,filenames) in walk(srcDir)
                if isAPN(os.path.basename(dirpath))}


def getAllTimestamps(srcDir):
    d = listImgsByAPN(srcDir)
    return {dirpath:
                [(readEXIFTime(os.path.join(dirpath, imgName)), imgName) for imgName in listImg]
                    for dirpath, listImg in d.items()}

def sortAPNByTimestamp(apns):
    return {k: sorted(v, key=lambda x: x[0]) for k, v in apns.items()}

def applyOffset2Timestamps(apns): #This fct set the min founded timestamp to 0
    f = {}
    for k, v in apns.items():
        min_timestamp  = min(vals[0] for vals in v) #vals[0] is timestamp
        f[k] = [(vals[0] - min_timestamp, *vals[1:]) for vals in v]
    return f

def makeLots():
    epsilon = 3
    srcDir = "/home/tristan/opv/datasets/"
    csvName = "charrues15_Samedi_picturesInfo_inverse.csv"

    data = getAllTimestamps(srcDir) # get timestamp data
    #data['csv'] = readCSV(os.path.join(srcDir, csvName)) #get csv data

    data = applyOffset2Timestamps(data)
    data = sortAPNByTimestamp(data)
    lotID = 0
    lots = list()

    while True:
        firstTimestampsSet = {k : v[0][0] for k, v in data.items() if len(v)}
        if not len(firstTimestampsSet): # if no more values to treat
            break
        min_val = min(firstTimestampsSet.values())

        pathInLot = [k for k, v in firstTimestampsSet.items() if v - min_val < epsilon]

        lots.append(dict())
        for k in pathInLot:
            lots[lotID][k] = data[k][0]
            del data[k][0]
        lotID += 1
    return lots

def readCSV(filename):
    f = []
    passHeader = False
    with open(filename, 'r') as csvFile:
        data = csv.reader(csvFile, delimiter=';')
        for row in data:
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
            f.append((timestamp, timestamp, lat, lng, alt, degree, minutes))
    return f[::-1]
