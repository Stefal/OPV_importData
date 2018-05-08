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
from typing import Callable
from opv_import.services import AbstractApnDeviceTasker
from opv_import import model

SD_CONFIGURER_NUM_THREAD = 1


class SdConfigurer(AbstractApnDeviceTasker):

    def __init__(self, ask_apn_num: Callable[[model.ApnDevice], int]):
        """
        A configurer for SD/device storage. Let's you configure the apn_number when a device is inserted.
        :param ask_apn_num:
        """
        self.logger = logging.getLogger(SdConfigurer.__module__ + "." + SdConfigurer.__class__.__name__)

        AbstractApnDeviceTasker.__init__(self, number_of_worker=SD_CONFIGURER_NUM_THREAD)

        self._ask_apn_num = ask_apn_num

    def _generate_task(self, device: model.ApnDevice) -> Callable:
        """
        Generate the copy/rsync task.
        :param device: Device to be copied.
        :return: A task, callable with no args and no return.
        """
        def task():
            self.logger.debug("Inserted device dev_name : %r", device.dev_name)
            device.apn_number = self._ask_apn_num(device)
            device.save_config()  # really ensure it's saved
            device.unmount()
            self.logger.info("Device (%r) configured and unmounted :) ", device)

        return task
