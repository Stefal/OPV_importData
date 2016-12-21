#!/usr/bin/env python3

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
"""
from importSD import Main
from makeLots import makeLots, moveLot

from docopt import docopt

from path import path

from utils import Config, convert_args

if __name__ == "__main__":
    args = docopt(__doc__)
    f_args = dict()

    # Convert args
    for n in ['clean-sd', 'import', 'treat']:
        f_args[n] = convert_args(args, n, True)
    for n in ['data-dir', 'lots-output-dir']:
        f_args[n] = convert_args(args, n)
    f_args['campaign'] = args['<campaign>']

    # Remove empty values
    f_args = {k: v for k, v in f_args.items() if v is not None}

    # create config and update with args
    conf = Config('config/main.json')
    conf.update(f_args)

    srcDir = path(conf["data-dir"].format(campaign=conf.get('campaign'))).expand()
    csvFile = path(srcDir) / "pictureInfo.csv"
    lotsOutput = path(conf["lots-output-dir"].format(campaign=conf.get('campaign'))).expand

    if conf.get('import'):
        Main().init(conf.get('campaign'), conf).start()
        print("Recuperation of data from SD card is finished")

    if conf.get('treat'):
        for lotNb, lot in enumerate(makeLots(srcDir, csvFile)):
            moveLot(lot, lotsOutput / str(lotNb))
        print("Lots generated")
