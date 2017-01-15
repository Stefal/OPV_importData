#!/usr/bin/python3
# coding: utf-8

"""Import the data into the treatment chain
Usage:
    ./import.py [options] <campaign>

Arguments:
    campaign              The name of the campaign to import
Options:
    -h --help             Show this screen
    --no-clean-sd         Clean SD after copying.
                          /!\\
                            This need sudo rights and you may loose
                            the content of the SD card if something fail !
                          /!\\
    --clean-sd            Do NOT clean SD after copying.
    --no-treat            Don't treat files
    --treat               Treat files
    --import              Import files
    --no-import           Don't import files
    --data-dir=<str>      Where should be placed file imported from SD
    --lots-output-dir=<str>   Where created lots may be placed
    --id-rederbro=<str>   Id of the rederbro use fot the campaign
    --description=<str>   Description of the campaign
    --csv-local=<str>     Local path of the csv file (pictureInfo)
"""
from docopt import docopt
from path import path

from importSD import Main
from makeLots import makeLots
from utils import Config, convert_args
from treat import treat

import task
import managedb

if __name__ == "__main__":
    args = docopt(__doc__)
    f_args = dict()

    # Convert args
    for n in ['clean-sd', 'import', 'treat']:
        f_args[n] = convert_args(args, n, True)
    for n in ['data-dir', 'lots-output-dir', 'id-rederbro', 'description']:
        f_args[n] = convert_args(args, n)
    f_args['campaign'] = args['<campaign>']

    # Remove empty values
    f_args = {k: v for k, v in f_args.items() if v is not None}

    # create config and update with args
    conf = Config('config/main.json')
    conf.update(f_args)

    campaign = managedb.make_campaign(conf['campaign'], conf['id-rederbro'], conf.get('description'))
    lots = []

    srcDir = path(conf["data-dir"].format(campaign=conf.get('campaign'))).expand()
    csvFile = path(srcDir) / "pictureInfo.csv"

    if conf.get('import'):
        Main().init(conf.get('campaign'), conf).start()
        print("Recuperation of data from SD card is finished")

    if conf.get('treat'):
        for l in makeLots(srcDir, csvFile):
            lot = treat(campaign, l)
            task.assemble.delay(lot.id) #lot object can't be send through network
