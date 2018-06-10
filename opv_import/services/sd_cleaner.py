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
# Description: Watch for storage devices to be inserted and ask to configure the device.

import logging
from typing import Callable, Dict
import subprocess
from opv_import.services import AbstractApnDeviceTasker
from opv_import import model
import time

from path import Path

SD_CLEANER_NUM_THREAD = 3
SD_CLEANER_NO_DEVICE_COUNT = -1


class SdCleaner(AbstractApnDeviceTasker):

    def __init__(self, iso_path: Path,
                 number_of_devices: int=SD_CLEANER_NO_DEVICE_COUNT):
        """
        M Propre service. Clean SD/devices.
        :param iso_path: Path of a clean ISO.
        :param number_of_devices: Will stop if all devices where seen, devices needs to be numbered from 0 to number_of_devices-1.
        :raises FileNotFoundError: When the ISO file doesn't exists.
        """
        AbstractApnDeviceTasker.__init__(self, number_of_worker=SD_CLEANER_NUM_THREAD, number_of_devices=number_of_devices)
        self.logger = logging.getLogger(SdCleaner.__module__ + "." + SdCleaner.__class__.__name__)

        self._iso_path = iso_path
        if not iso_path.exists():
            raise FileNotFoundError

        self._clean_event = None  # clean event

        self._terminated = {apn_num: 0 for apn_num in range(0, number_of_devices)}  # apn_number -> bool (True if terminated)

    def on_clean(self, clean_event: Callable[[model.ApnDevice], None]=None):
        """
        Clean event setter, will be fired when a device is cleaned.
        :param clean_event: Event to be triggered when a device is cleaned, will be called with the device.
        """
        self._clean_event = clean_event

    def _dd_device(self, device: model.ApnDevice):
        """
        DD the device if ISO.
        :param device: Device to dd.
        """
        self.logger.debug("Umounting and cleaning device %r, with iso : %s", device, self._iso_path)
        device.unmount()
        subprocess.run(['sudo', 'dd', "if={iso}".format(iso=self._iso_path), "of={parent}".format(parent=device.parent_dev_name)])
        time.sleep(0.25)  # unexplained bug
        device.mount()
        self.logger.debug("Device cleaned (and mounted again) : %r", device)

    def _generate_task(self, device: model.ApnDevice) -> Callable:
        """
        Generate the clean task.
        :param device: Device to be copied.
        :return: A task, callable with no args and no return.
        """
        def task():
            self.logger.debug("Cleaning device : %r", device)
            device.apn_number # access it to be sure that configuration file is loaded

            self._dd_device(device=device)  # cleaning device

            # device.save_config()  # really ensure it's saved

            # device.unmount()

            # setting device to treated
            self._terminated[device.apn_number] = True

            self.logger.debug("Device (%r) cleaned, configured and unmounted :) ", device)
            device.save_config()
            device.unmount()

            if self._clean_event is not None:
                self._clean_event(device)

        return task

    @property
    def devices_terminated(self) -> Dict[int, float]:
        """
        Return a dict with the current states of devices, is the are terminated or not.
        :return: A dict of terminated states (apn_num -> True if terminated).
        """
        d = {}  # copies dict to a new one, thread safety first ;)
        d.update(self._terminated)
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
