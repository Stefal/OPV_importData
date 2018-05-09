# coding: utf-8

# Copyright (C) 2017 Open Path View, Maison Du Libre
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

# Contributors: Benjamin BERNARD <benjamin.bernard@openpathview.fr>
# Email: team@openpathview.fr
# Description: CLI to generate lot.

"""
Make lot and save them into the database. From rederbro's datas (images and meta).
Usage:
    opv-make-lot [options] <cameras-dir>

Arguments:
    cameras-dir                     Path to the cameras images (APN{i}/DCIM ...) folders.
Options:
    -h --help                       Show this screen
    --csv-path=<str>                Path to the meta CSV files.
    --campaign-name=<str>           Campaign name [Default: A campaign]
    --campaign-id-rederbro=<int>    ID Rederbro (it's the backpack ID) [Default: 0]
    --campaign-desc=<str>           Description of the campaign. [Default: no description]
    --api-uri=str>                  DBRest API uri [Default: http://opv_master:5000]
    --dm-uri=<str>                  Directory Manager uri [Default: http://opv_master:5005]
    --dm-file=<str>                 Enable file mode using this tmp folder.
    --number-of-devices=<int>       Number of devices to wait for. [default: 6]
    --id-malette=<int>              Malette ID. [Default: 42]
    --debug                         Enable debugging options.
"""

import signal
import logging
import docopt
from opv_import.helpers.logging import setup_logging
from opv_import.services import TreatRederbroData

from opv_api_client import RestClient as OpvApiRestClient
from opv_directorymanagerclient import DirectoryManagerClient, Protocol

from path import Path

DEFAULT_NB_CAM = 6

def parse_arguments(args):
    """
    Parse docopt Arguments.
    :param args: Docopt arguments.
    :return: A dict with the parsed arguments
    """
    # Parsing argments
    p = {}
    p['cameras_dir'] = Path(args["<cameras-dir>"])
    p['csv_path'] = Path(args["--csv-path"]) if args["--csv-path"] else None
    p['campaign_name'] = str(args["--campaign-name"]) if args["--campaign-name"] else None
    p['campaign_id_rederbro'] = int(args["--campaign-id-rederbro"]) if args["--campaign-id-rederbro"] else None
    p['campaign_desc'] = str(args["--campaign-desc"]) if args["--campaign-desc"] else None
    p['api_uri'] = str(args["--api-uri"]) if args["--api-uri"] else None
    p['dm_uri'] = str(args["--dm-uri"]) if args["--dm-uri"] else None
    p['dm_file'] = args["--dm-file"]
    p['number_of_devices'] = int(args["--number-of-devices"]) if args["--number-of-devices"] else DEFAULT_NB_CAM
    p['id_malette'] = int(args["--id-malette"]) if args["--id-malette"] else None

    return p

def main():
    # Loggers to handle + debug option
    setup_logging()

    args = docopt.docopt(__doc__)
    logging.getLogger("opv_import").setLevel(logging.DEBUG if "--debug" in args and args["--debug"] else logging.INFO)
    logger = logging.getLogger(__name__)

    p = parse_arguments(args)


    # UI print parameters
    logger.info("Make lot with parameters : %r", p)

    # UI to display progression
    def on_lot_progress(progression: float):
        """
        Display when a lot is saved in DB.
        :param progression: Progression rate.
        """
        logger.info("Save all lot progress : %f", progression*100)

    # DM arguments
    dm_client_args = {}
    dm_client_args['default_protocol'] = Protocol.FILE if p['dm_file'] else Protocol.FTP
    dm_client_args['api_base'] = p['dm_uri']
    if p['dm_file']:
        dm_client_args['default_protocol'] = p['dm_file']

    # Starting treater service
    treat = TreatRederbroData(
        cam_pictures_dir=p['cameras_dir'],
        id_malette=p['id_malette'],
        opv_api_client=OpvApiRestClient(p['api_uri']),
        opv_dm_client=DirectoryManagerClient(**dm_client_args),
        number_of_cameras=p['number_of_devices'],
        csv_meta_path=p['csv_path']
    )

    logger.info("Starting making lot, go take some coffe (it might be really long)")
    treat.make_lot()
    logger.info("Creating campaign ...")
    treat.create_campaign(name=p['campaign_name'], id_rederbro=p['campaign_id_rederbro'], description=p['campaign_desc'])
    logger.info("Saving lots int db (lucky you, you will know have a progression).")
    treat.save_all_lot(on_progress_listener=on_lot_progress)

    logger.info("Bye :)")


if __name__ == "__main__":
    main()