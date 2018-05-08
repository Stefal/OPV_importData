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
# Description: Command ligne entry point to copy data (DCIM folders) from a set of external devices.

"""
Copy data (DCIM folders) from a set of external devices, containing a configuration file.
Usage:
    opv-sd-copier [options] <output-directory>

Arguments:
    output-directory            Directory where all APN's DCIM folders will be copied (structure will be dir/APN$i/DCIM
Options:
    -h --help                   Show this screen
    --number-of-devices=<int>   Number of devices to wait for. [default: 6]
    --debug                     Enable debugging options.
"""

import logging
import docopt
from opv_import.helpers.logging import setup_logging
from opv_import.services import SdCopier

from path import Path

from typing import Dict

def main():
    # Loggers to handle + debug option
    setup_logging()

    args = docopt.docopt(__doc__)
    logging.getLogger("opv_import").setLevel(logging.DEBUG if "--debug" in args and args["--debug"] else logging.INFO)
    logger = logging.getLogger(__name__)

    number_of_devices = int(args["--number-of-devices"])
    output_directory = Path(args["<output-directory>"])

    # UI print parameters
    logger.info("Number of waited devices : %i", number_of_devices)
    logger.info("Output directory will be : %s", output_directory)

    # UI to display progression
    def display_device_progression(progressions: Dict[int, float], terminated: Dict[int, bool]):
        """
        Display devices copy progresion.
        :param progressions: For each apn_num (key) it's progression rate from 0 to 1.
        :param terminated: For each apn_num (key), tells it the copy is terminated (True) or not (False).
        """
        msg = "Devices copy progression : "
        ids = progressions.keys()
        ids.sort()
        progressions_msg = ()
        for apn_num in progressions.keys():
            progressions_msg.append("APN[apn_num}: {p:.2f}%".format(apn_num=apn_num, p=progressions[apn_num]))

        msg += " | ".join(progressions_msg)

        logger.info(msg)

    # Starting copier service
    copier = SdCopier(number_of_devices=number_of_devices, dest_path=output_directory)
    copier.on_progression_change(event=display_device_progression)  # listen on device progression changes

    logger.info("Starting copy for %i devices to %s", number_of_devices, output_directory)
    copier.start()
    logger.info("You can now insert devices ... waiting")

    copier.wait()

    copier.stop()
    logger.info("All devices where copied to : %s", output_directory)


if __name__ == "__main__":
    main()