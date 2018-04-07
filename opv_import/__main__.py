#!/usr/bin/python3
# coding: utf-8

"""Import the data into the treatment chain
Usage:
    opv-import [options] <id_malette> <campaign>

Arguments:
    campaign                   The name of the campaign to import
Options:
    -h --help                  Show this screen
    --csv-path=<str>           The path of CSV file for synchro
    --no-clean-sd              Clean SD after copying.
                                /!\\
                                    This need sudo rights and you may loose
                                    the content of the SD card if something fail !
                                /!\\
    --config-file=<str>         The path to the config file. Default configuration is embeded in the script.
    --clean-sd                  Do NOT clean SD after copying.
    --no-treat                  Don't treat files
    --treat                     Treat files
    --export                    Send files to the task queue
    --no-export                 Don't send files to the task queue
    --import                    Import files
    --no-import                 Don't import files
    --ref=<str>                 'first' the first images (oldest) constitute a reference lot,
                                'last' the last images (newest) constitue a reference lot.
    --data-dir=<str>            Where should be placed file imported from SD
    --lots-output-dir=<str>     Where created lots may be placed
    --id-rederbro=<str>         Id of the rederbro use fot the campaign
    --description=<str>         Description of the campaign
    --dir-manager-uri=<str>     URI of the DirectoryManager [default: http://localhost:5001]
    --dir-manager-file          Tells directory manager to use local hardlinking or copy.
                                Use this option if you are on the DirectoryManager server manager to speed up transferts.
                                You should also set dir-manager-tmp to a directory on the same partition (partition of the picture files)
                                so that hardlinks work.
    --dir-manager-tmp=<str>     Tells the DirectoryManagerClient where is it's tempory directory.
    --makelot-new-version       Make camera lot using the new algorithm, actually this algorithm is under developpment and doesn't handle CSV metadata
                                This new version doesn't handle import from SD card so you need to set the datadir.

    --api-uri=<str>             URI of the DirectoryManager [default: http://localhost:5000]
    --debug                     Set logs to debug.
"""

from . import managedb
from .treat import treat, treat_new
from .importSD import Main
from .makeLots import makeLots
from .utils import Config, convert_args
from .const import Const

from path import Path
from docopt import docopt

from opv_directorymanagerclient import DirectoryManagerClient, Protocol

from opv_import.makelot import LotMaker, Lot

import logging

formatter_f = logging.Formatter('%(asctime)s %(name)-25s %(levelname)-8s %(message)s')
formatter_c = logging.Formatter('%(name)-30s: %(levelname)-8s %(message)s')

fh = logging.FileHandler('/tmp/importData.log')
ch = logging.StreamHandler()

ch.setFormatter(formatter_c)
fh.setFormatter(formatter_f)

ch.setLevel(logging.INFO)
fh.setLevel(logging.DEBUG)

rootLogger = logging.getLogger('importData')
rootLogger.addHandler(ch)
rootLogger.addHandler(fh)


logger = logging.getLogger('importData.' + __name__)

def main():
    """ Import Images from SD """
    # Read the __doc__ and build the Arguments
    args = docopt(__doc__)
    f_args = dict()

    # logs
    rootLogger.setLevel(logging.DEBUG if "--debug" in args and args["--debug"] else logging.INFO)
    loggerLM = logging.getLogger("opv_import.makelot.lotMaker.LotMaker")
    loggerLM.setLevel(logging.DEBUG)
    loggerLM.addHandler(ch)
    loggerLM.addHandler(fh)
    ch.setLevel(rootLogger.getEffectiveLevel())
    fh.setLevel(rootLogger.getEffectiveLevel())

    # Convert args
    for n in ['clean-sd', 'import', 'treat', 'export', 'dir-manager-file', 'makelot-new-version']:
        f_args[n] = convert_args(args, n, True)
    for n in ['api-uri', 'dir-manager-uri', 'config-file', 'data-dir', 'lots-output-dir', 'id-rederbro', 'description', 'csv-path', 'ref']:
        f_args[n] = convert_args(args, n)
    f_args['campaign'] = args['<campaign>']

    id_malette = args['<id_malette>']

    # Remove empty values
    f_args = {k: v for k, v in f_args.items() if v is not None}

    # --- Config ---
    conf = Config(configString=Const.default_config)
    # Update with user specified config file
    if 'config-file' in f_args.keys():
        conf.loadConfigFile(f_args.pop('config-file'))
    # Update with args
    conf.update(f_args)

    managedb.make_client(conf['api-uri'])

    campaign = managedb.make_campaign(id_malette, conf['campaign'], conf['id-rederbro'], conf.get('description'))

    # We need to improve this
    # Case 1 : we pass the Arguments
    # Case 2 : Go get the file on rederbro
    srcDir = Path(conf["data-dir"].format(campaign=conf.get('campaign'))).expand()
    # CSV path from args if it exist, fallback to data directory
    csvFile = Path(conf['csv-path']) if 'csv-path' in conf else None

    if conf.get('makelot-new-version'):
        logger.info("Choose makelot-new-version algorithm.")
        lm = LotMaker(pictures_path=srcDir, rederbro_csv_path=csvFile, nb_cams=6)
        lm.load_cam_images()

        logger.info("Making camera sets ...")
        cam_sets = lm.make_gopro_set_new(threshold_max_consecutive_incomplete_sets=35)

        if csvFile is not None:
            lm.load_metas()
            lots = lm.generate_all_lot(
                img_sets=cam_sets,
                threshold_max_consecutive_incomplete_sets=35,
                threshold_incomplete_set_window_size=10,
                threshold_incomplete_set_max_in_window=4)
        else:
            lots = [Lot(cam_set=s, meta=None) for s in cam_sets]

        # instanciating DirectoryManagerCliLotent
        dm_client_args = {}
        if '--dir-manager-tmp' in args and args['--dir-manager-tmp'] is not None and Path(args['--dir-manager-tmp']).isdir():
            dm_client_args["workspace_directory"] = args['--dir-manager-tmp']

        dm_client_args["default_protocol"] = Protocol.FILE if conf['dir-manager-file'] else Protocol.FTP
        dm_client_args["api_base"] = conf['dir-manager-uri']
        dir_manager_client = DirectoryManagerClient(**dm_client_args)

        # inserting ImageSets in the database and dm
        logger.info("Listing images sets from partitions and inserting them into OPV-API OPV-DM")
        for l in lots:
            logger.info("Treating log : %r ", l)
            treat_new(id_malette, campaign, l, dir_manager_client, hardlinking=conf['dir-manager-file'])

        return

    if conf.get('import'):
        logger.info("=================================================")
        logger.info("======= Let's import images from SD cards =======")

        Main().init(conf.get('campaign'), conf).start()
        logger.info("... Done ! Data recover.")
        return

    if conf.get('treat'):
        logger.info("=================================================")
        logger.info("================ Treating data  =================")

        dm_client_args = {}
        if '--dir-manager-tmp' in args and args['--dir-manager-tmp'] is not None and Path(args['--dir-manager-tmp']).isdir():
            dm_client_args["workspace_directory"] = args['--dir-manager-tmp']

        dm_client_args["default_protocol"] = Protocol.FILE if conf['dir-manager-file'] else Protocol.FTP
        dm_client_args["api_base"] = conf['dir-manager-uri']
        dir_manager_client = DirectoryManagerClient(**dm_client_args)
        logger.info(srcDir)
        refFirst = conf.get("ref") == 'first'
        logger.info("FirstLotRef = " + str(refFirst))
        for l in makeLots(srcDir, csvFile, firstLotRef=refFirst):
            logger.debug("-- main --")
            logger.debug(l)
            treat(id_malette, campaign, l, dir_manager_client, hardlinking=conf['dir-manager-file'])
            # lot object can't be send through network
            if conf.get('export'):  # send to task queue
                pass


if __name__ == "__main__":
    main()
