#!/usr/bin/python3
# coding: utf-8

"""Import the data into the treatment chain
Usage:
    opv-import [options] <campaign>

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
    --config-file=<str>   The path to the config file.[default: ./config/main.json]
    --clean-sd            Do NOT clean SD after copying.
    --no-treat            Don't treat files
    --treat               Treat files
    --export              Send files to the task queue
    --no-export           Don't send files to the task queue
    --import              Import files
    --no-import           Don't import files
    --data-dir=<str>      Where should be placed file imported from SD
    --lots-output-dir=<str>   Where created lots may be placed
    --id-rederbro=<str>   Id of the rederbro use fot the campaign
    --description=<str>   Description of the campaign
    --dir-manager-uri=<str> URI of the DirectoryManager [default: http://localhost:5001]
    --api-uri=<str>       URI of the DirectoryManager [default: http://localhost:5000]
"""

from . import managedb
from .treat import treat
from .importSD import Main
from .makeLots import makeLots
from .utils import Config, convert_args

from path import Path
from docopt import docopt

from opv_directorymanagerclient import DirectoryManagerClient, Protocol

import logging

formatter_f = logging.Formatter('%(asctime)s %(name)-25s %(levelname)-8s %(message)s')
formatter_c = logging.Formatter('%(name)-25s: %(levelname)-8s %(message)s')

fh = logging.FileHandler('/tmp/importData.log')
ch = logging.StreamHandler()

ch.setFormatter(formatter_c)
fh.setFormatter(formatter_f)

ch.setLevel(logging.INFO)
fh.setLevel(logging.DEBUG)

rootLogger = logging.getLogger('importData')
rootLogger.addHandler(ch)
rootLogger.addHandler(fh)

rootLogger.setLevel(logging.DEBUG)


logger = logging.getLogger('importData.' + __name__)

def main():
    """ Import Images from SD """
    # Read the __doc__ and build the Arguments
    args = docopt(__doc__)
    f_args = dict()

    # Convert args
    for n in ['clean-sd', 'import', 'treat', 'export']:
        f_args[n] = convert_args(args, n, True)
    for n in ['api-uri', 'dir-manager-uri', 'config-file', 'data-dir', 'lots-output-dir', 'id-rederbro', 'description', 'csv-path']:
        f_args[n] = convert_args(args, n)
    f_args['campaign'] = args['<campaign>']

    # Remove empty values
    f_args = {k: v for k, v in f_args.items() if v is not None}

    # Create config and update with args
    # !!!!!!!
    # To change : not absolute path
    # !!!!!!!
    conf = Config(f_args.pop('config-file'))
    conf.update(f_args)

    logger.info("=================================================")
    logger.info("===== Let's import the image from SD card =======")

    managedb.make_client(conf['api-uri'])
    campaign = managedb.make_campaign(conf['campaign'], conf['id-rederbro'], conf.get('description'))

    # We need to improve this
    # Case 1 : we pass the Arguments
    # Case 2 : Go get the file on rederbro
    srcDir = Path(conf["data-dir"].format(campaign=conf.get('campaign'))).expand()
    csvFile = Path(srcDir) / "pictureInfo.csv"

    if conf.get('import'):
        logger.info("Get data from SD card ...")
        Main().init(conf.get('campaign'), conf).start()
        logger.info("... Done ! Data recover.")

    if conf.get('treat'):
        dir_manager_client = DirectoryManagerClient(api_base=conf['dir-manager-uri'], default_protocol=Protocol.FTP)
        for l in makeLots(srcDir, csvFile):
            lot = treat(campaign, l, dir_manager_client)
            # lot object can't be send through network
            if conf.get('export'): # send to task queue
                pass


if __name__ == "__main__":
    main()
