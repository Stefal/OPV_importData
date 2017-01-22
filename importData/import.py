#!/usr/bin/python3
# coding: utf-8

"""Import the data into the treatment chain
Usage:
    ./import.py [options] <campaign>

Arguments:
    campaign              The name of the campaign to import
Options:
    -h --help             Show this screen
    --csv-path=<str>      The path of CSV file for synchro
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
"""
import task
import managedb

from path import path
from treat import treat
from docopt import docopt
from importSD import Main
from makeLots import makeLots
from utils import Config, convert_args


if __name__ == "__main__":
    """ Import Images from SD """
    # Read the __doc__ and build the Arguments
    args = docopt(__doc__)
    f_args = dict()

    # Convert args
    for n in ['clean-sd', 'import', 'treat']:
        f_args[n] = convert_args(args, n, True)
    for n in ['data-dir', 'lots-output-dir', 'id-rederbro', 'description', 'csv-path']:
        f_args[n] = convert_args(args, n)
    f_args['campaign'] = args['<campaign>']

    # Remove empty values
    f_args = {k: v for k, v in f_args.items() if v is not None}

    # Create config and update with args
    # !!!!!!!
    # To change : not absolute path
    # !!!!!!!
    conf = Config('config/main.json')
    conf.update(f_args)

    print("=================================================")
    print("===== Let's import the image from SD card =======")

    campaign = managedb.make_campaign(conf['campaign'], conf['id-rederbro'], conf.get('description'))
    lots = []

    # We need to improve this
    # Case 1 : we pass the Arguments
    # Case 2 : Go get the file on rederbro
    srcDir = path(conf["data-dir"].format(campaign=conf.get('campaign'))).expand()
    csvFile = path(srcDir) / "pictureInfo.csv"

    if conf.get('import'):
        print("Get data from SD card ...")
        Main().init(conf.get('campaign'), conf).start()
        print("... Done ! Data recover.")

    if conf.get('treat'):
        for l in makeLots(srcDir, csvFile):
            lot = treat(campaign, l)
            # lot object can't be send through network
            task.assemble.delay(lot.id)
