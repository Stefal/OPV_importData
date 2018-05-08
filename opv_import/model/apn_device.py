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
# Description: Represent an Open Path View APN device, handle it's configuration.

import json
import logging
from path import Path

from opv_import.helpers import UdiskDevice

APN_CONF_RELATIVE_PATH = Path("APN_config.json")
APN_CONF_NUMBER_KEY = "APN_num"
APN_DEFAULT_CONFIG = { APN_CONF_NUMBER_KEY: None }


class ApnDevice(UdiskDevice):
    """
    Represent an APN device.
    """

    def __init__(self, device_name: Path):
        """
        Intanciate an APN Device.
        :param device_name: The device name, should be something like "/dev/sda1"
        """
        super().__init__(device_name=device_name)

        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self._apn_conf = None  # Configuration not loaded, lazy loading
        self._ignore_unexisting_configuration = False  # Will ignore configuration if it doesn't exists (doesn't raise execeptions)

    def _load_configuration(self):
        """
        Load APN configuration.
        """
        self.logger.debug("Loading configuration from APN storage device %s", super().dev_name)

        path_conf_file = super().mount_path / APN_CONF_RELATIVE_PATH
        if path_conf_file.exists():
            with open(path_conf_file, "r") as conf_file:
                self._apn_conf = json.load(conf_file)
        else:
            self.logger.debug("Configuration file need to be here : %s", path_conf_file)
            self._apn_conf = {}
            self._apn_conf.update(APN_DEFAULT_CONFIG)

    @property
    def ignore_unexisting_configuration(self) -> bool:
        """ Tell if it ignore unexisting configuration on device. """
        return self._ignore_unexisting_configuration

    @ignore_unexisting_configuration.setter
    def ignore_unexisting_configuration(self, ignore_config):
        """
        Set to ignore if config file doesn't exists this mean it will start from a default clear config.
        :param ignore_config: True if you know that the config file isn't present.
        """
        self._ignore_unexisting_configuration = ignore_config

    @property
    def apn_number(self) -> int:
        """
        Return APN number. Load it from configuration.
        :return: APN number.
        :raises ApnDeviceNumberNotFoundError: When number wasn't found.
        """
        if self._apn_conf is None:
            self._load_configuration()
        apn_number = self._apn_conf.get(APN_CONF_NUMBER_KEY, None)

        if apn_number is None:
            raise ApnDeviceNumberNotFoundError()

        return apn_number

    @apn_number.setter
    def apn_number(self, number: int):
        """
        Set the APN number and save it to the device. Will automatically save the configuration.
        :param number: Number of the APN.
        """
        if self._apn_conf is None:
            self._load_configuration()

        self._apn_conf[APN_CONF_NUMBER_KEY] = number
        self.save_config()

    def save_config(self):
        """
        Save config on device.
        Set default config if config is none.
        """
        self.logger.debug("Saving configuration file on APN storage device %s", super().dev_name)

        if self._apn_conf is None:
            self._load_configuration()

        path_conf_file = super().mount_path / APN_CONF_RELATIVE_PATH
        with open(path_conf_file, "w") as conf_file:
            json.dump(self._apn_conf, conf_file)

    def __repr__(self) -> str:
        """ Representation of a device"""
        try:
            return "ApnDevice[devname: \"{d.dev_name}\", apn_number: {d.apn_number}]".format(d=self)
        except ApnDeviceNumberNotFoundError:
            return "ApnDevice[devname: \"{d.dev_name}\", apn_number: NotFound]".format(d=self)



class ApnDeviceNumberNotFoundError(Exception):
    """ When APN number isn't found in configuration file. """
    pass
