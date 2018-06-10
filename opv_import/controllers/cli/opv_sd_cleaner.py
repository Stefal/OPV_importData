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
# Description: Command ligne entry point to clean devices using a ISO of a clean device.

"""
Clean external devices keeping it's configuration.
Usage:
    opv-sd-cleaner [options] <file-system>

Arguments:
    file-system                 Parition will be reformated in this file system, can be 'FAT32' or 'EXFAT'
Options:
    -h --help                   Show this screen
    --number-of-devices=<int>   Number of devices to wait for. [default: 6]
    --debug                     Enable debugging options.
"""

import logging
import docopt
import signal
from opv_import.model import ApnDevice, FileSystem
from opv_import.helpers.logging import setup_logging
from opv_import.services import SdCleaner
from opv_import.services.sd_cleaner import SD_CLEANER_NO_DEVICE_COUNT

from path import Path

def map_fs(fs_str: str) -> FileSystem:
    """
    Transform FS str into model one.
    :param fs_str: can be 'FAT32' or 'EXFAT'
    :return: The FS model.
    """
    if fs_str == "FAT32":
        return FileSystem.FAT32
    elif fs_str == 'EXFAT':
        return FileSystem.EXFAT
    else:
        return None

def main():
    # Loggers to handle + debug option
    setup_logging()

    args = docopt.docopt(__doc__)
    logging.getLogger("opv_import").setLevel(logging.DEBUG if "--debug" in args and args["--debug"] else logging.INFO)
    logger = logging.getLogger(__name__)

    fs = map_fs(fs_str=args["<file-system>"])
    number_of_devices = int(args["--number-of-devices"]) if args["--number-of-devices"] else SD_CLEANER_NO_DEVICE_COUNT

    if fs is None:
        logger.error("Invalid filesystem '%s', valid FS are 'FAT32' or 'EXFAT'", args["<file-system>"])
        return

    # UI print parameters
    logger.info("Number of waited devices : %i", number_of_devices)

    # UI to display progression
    def clean_event_listener(device: ApnDevice):
        """
        Display when a device is cleaned
        :param device: Cleaned device.
        """
        logger.info("Device %r was cleaned and unmount, can be removed safely.", device)

    # Starting copier service
    cleaner = SdCleaner(fs=fs, number_of_devices=number_of_devices)
    cleaner.on_clean(clean_event=clean_event_listener)

    # Interruptions
    signal.signal(signal.SIGINT, lambda signnum, frame: cleaner.stop(force=True))

    logger.info("Starting cleaner for %i devices", number_of_devices)
    cleaner.start()
    logger.info("You can now insert devices ... waiting")

    cleaner.wait()

    cleaner.stop()
    logger.info("All devices where cleaned.")


if __name__ == "__main__":
    main()