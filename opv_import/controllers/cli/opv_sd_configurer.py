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
Configure a set of SD card by setting an "apn_number" to each card.
Usage:
    opv-sd-configurer [options]

Options:
    -h --help                   Show this screen
    --debug                     Enable debugging options.
"""

import logging
import docopt
from opv_import.model.apn_device import ApnDeviceNumberNotFoundError
from opv_import.model import ApnDevice
from opv_import.helpers.logging import setup_logging
from opv_import.services import SdConfigurer

import signal

def main():
    # Loggers to handle + debug option
    setup_logging()

    args = docopt.docopt(__doc__)
    logging.getLogger("opv_import").setLevel(logging.DEBUG if "--debug" in args and args["--debug"] else logging.INFO)
    logger = logging.getLogger(__name__)

    # UI to display progression
    def ask_apn_num(device: ApnDevice) -> int:
        try:
            device.apn_number
            logger.info("Device already have a number : %i", device.apn_number)
        except ApnDeviceNumberNotFoundError:
            logger.info("Device doesn't have a number (or configuration file)")
        return int(input("-----> Please enter new APN number for the device : "))

    # Start configurer tool
    conf_manager = SdConfigurer(ask_apn_num=ask_apn_num)

    # Interruptions
    signal.signal(signal.SIGINT, lambda signnum, frame: conf_manager.stop(force=True))

    conf_manager.start()
    logger.info("You can now insert devices ... waiting")

    conf_manager.wait()
    logger.debug("After wait")

    conf_manager.stop()


if __name__ == "__main__":
    main()