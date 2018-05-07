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
# Description: Watch for storage devices to be inserted and copy their DCMI folder to a destination folder.

import logging
from typing import Callable, Dict
from path import Path

from opv_import.helpers import RsyncWrapper
from opv_import.services import AbstractApnDeviceTasker
from opv_import import model
from opv_import.model.apn_device import ApnDeviceNumberNotFoundError

SD_UDEV_OBSERVER_NAME = "OPV SD card import"
COPY_NUMBER_OF_WORKERS = 3
SD_DCIM_FOLDER_PATH = Path("DCIM")

class SdCopier(AbstractApnDeviceTasker):

    def __init__(self, number_of_devices: int, apn_id_to_dest: Callable[[int], Path]):
        """
        Initiate an SdCopier class. Used to watch an copy storage devices datas.
        :param number_of_devices: Number of devices to watch (used to know when we have finished.
        :param apn_id_to_dest: format destination path from an APN ID (it's a lambda).
        """
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        AbstractApnDeviceTasker.__init__(self, number_of_worker=COPY_NUMBER_OF_WORKERS, number_of_devices=number_of_devices)

        self._apn_id_to_dest = apn_id_to_dest

        # progress info dict
        self._progress = {}  # apn_number -> progress rate
        self._terminated = {}  # apn_number -> bool (True if terminated)

    def dest_path(self, apn_number: int) -> Path:  # to remove
        """
        Return destination Path for an apnId.
        :param apn_number: Id of the storage device (APN)
        :return: The destination path for copy.
        """
        return self._apn_id_to_dest(apn_number)

    def _generate_task(self, device: model.ApnDevice) -> Callable:
        """
        Generate the copy/rsync task.
        :param device: Device to be copied.
        :return: A task, callable with no args and no return.
        """
        def task():    # close with device
            # check it's a configured device
            try:
                device.apn_number
            except ApnDeviceNumberNotFoundError:
                self.logger.error("The device %s doesn't have an APN number, migth not be configured aborting copy", device.dev_name)
                return

            def on_progress(progress_rate):
                self.logger.debug("Rsync progress for APN %r, rate: %f", device, progress_rate)
                self._progress[device.apn_number] = progress_rate

            def on_terminate():
                self.logger.debug("Rsync terminated for APN %r", device)
                self._terminated[device.apn_number] = True

            source_path = device.mount_path / SD_DCIM_FOLDER_PATH  # no trailling slash for rsync to copy folder + content
            dest_path = self.dest_path(apn_number=device.apn_number)
            rsync = RsyncWrapper(source_path=source_path, destination_path=dest_path)
            rsync.on_progress(on_progress)
            rsync.on_terminate(on_terminate)
            self.logger.debug("Starting Rsync for APN %r", device)
            rsync.run()
        return task

    @property
    def devices_progressions(self) -> Dict[int, float]:
        """
        Return a dict with the current progression rate (from 0 to 1) for each cameras.
        :return: A dict of the progression rate for each cameras.
        """
        d = {}  # copies dict to a new one, thread safety first ;)
        d.update(self._progress)
        return d

    def is_device_transfert_terminated(self, apn_number: int) -> bool:
        """
        Tell if a device (ApnNumber) as terminated it's transfert or not.
        :param apn_number: The number of the device.
        :return: True if transfert is terminated, False otherwise.
        """
        if apn_number in self._terminated:
            return self._terminated[apn_number]
        else:
            return False
