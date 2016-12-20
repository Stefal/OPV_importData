#!/usr/bin/env python3
import os
import os.path
from importSD import Main
from makeLots import makeLots, moveAllPictures

from utils import Config


if __name__ == "__main__":
    conf = Config('config/main.json')

    campaign = input('Enter campaign name please: ')
    srcDir = os.path.expanduser(conf["data_dir"].format(campaign=campaign))
    csvFile = os.path.join(srcDir, "pictureInfo.csv")
    lotsOutput = os.path.expanduser(conf["lots_output_dir"].format(campaign=campaign))

    Main().init(campaign, conf)
    Main().start()

    print("Recuperation of data from SD card is finished")

    lots = makeLots(srcDir, csvFile)
    moveAllPictures(lots, lotsOutput)

    print("Lots generated")
