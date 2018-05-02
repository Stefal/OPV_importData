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
# Description: Abstract helper to manage copies from an external device (SD cards, hardrives ...).

import re
import logging
import subprocess
import threading
from path import Path

from typing import List

from abc import abstractmethod

UDISK_MOUNTED_PATH_REGEX = r"(\/media.+)\.\n"


class DeviceCopier(threading.Thread):

    def __init__(self, device_name: str):
        """
        Init a device copier from a device name.
        :param device_name: Name of the partition, should be something like /dev/sda1, /dev/sdb2 ...
        """
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self._dev_name = device_name
        self._mount_path = None   # will be the mounted path

    def _udisks_extract_mount_path(self, udisk_output: str) -> Path:
        """
        Extract mount path from udisksctl output.
        :param output: udisksctl ouput.
        :return: The mounted path.
        """
        # ouput is like : Mounted /dev/sdc1 at /media/benjamin/B291-4FA9.
        m = re.search(UDISK_MOUNTED_PATH_REGEX, udisk_output, flags=re.MULTILINE)
        if m is not None:
            return Path(m.groups()[0])
        return None

    def _mount(self) -> Path:
        """
        Will mount the device.
        :raises MissingUdisckError: If udisksctl isn't found
        :raises MountError: If the mount command failed.
        :return: Mount path
        """
        self.logger.debug("Mounting : %s", self._dev_name)
        try:
            p = subprocess.Popen(['udisksctl', 'mount', '-b', self._dev_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, _ = p.communicate()
            self._mount_path = self._udisks_extract_mount_path(udisk_output=out.decode("utf8"))

            if self._mount_path is None:
                raise MountError("Mount path not found in udisksctl ouput")

            self.logger.debug("Mounted at : %s", self._mount_path)
            return self._mount_path
        except subprocess.CalledProcessError as ex:
            self.logger.error("{} not mounted".format(self._dev_name))
            raise MountError("Mount of {devname} (cmd:{r.cmd}) returned exit code {r.returncode} with stderr {r.stderr}".format(
                devname=self._dev_name,
                r=ex
            ))
        except FileNotFoundError:
            self.logger.error("udisks not installed on system")
            raise MissingUdisckError("udisks not installed on system")

    @property
    def mount_path(self) -> Path:
        """ Return the mounted path. Will mount it if it's not already done."""
        if self._mount_path is None:
            self._mount()
        return self._mount_path

    @abstractmethod
    def _list_src_paths_to_copy(self) -> List[Path]:
        """ Abstract, should return list of path to copy. You should use mount_path to get the device mounted path."""
        raise NotImplemented

    @abstractmethod
    def _compute_destination(self, source: Path) -> Path:
        """ Compute destination Path from source Path, you need to implement it."""
        raise NotImplemented

    def run_copy(self):
        """ Make the actual copy"""
        # TODO
        pass

    def run(self):
        """ Simply run the copy."""
        self.run_copy()


class MountError(Exception):
    """ When mount goes badly, see message for more details on the error"""
    pass


class MissingUdisckError(Exception):
    """ When mounting fail because of udisck missing (udisksctl command not found in PATH) """
    pass
