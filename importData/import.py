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

import os
import os.path
from importSD import Main
from makeLots import makeLots, moveAllLots

from docopt import docopt

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

    srcDir = os.path.expanduser(conf["data-dir"].format(campaign=conf.get('campaign')))
    csvFile = os.path.join(srcDir, "pictureInfo.csv")
    lotsOutput = os.path.expanduser(conf["lots-output-dir"].format(campaign=conf.get('campaign')))

    Main().init(conf.get('campaign'), conf)
    Main().start()

    if conf.get('treat'):
        print("Recuperation of data from SD card is finished")

        lots = makeLots(srcDir, csvFile)
        moveAllLots(lots, lotsOutput)

        print("Lots generated")
