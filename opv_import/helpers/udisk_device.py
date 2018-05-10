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
# Description: Abstract helper to manage device via udiskctl.

import re
import logging
import subprocess
from path import Path
import pyudev

UDISK_MOUNTED_PATH_REGEX = r"(\/media.+)\.\n"


class UdiskDevice:

    def __init__(self, device: pyudev.Device):
        """
        Init a device copier from a device name.
        :param device_name: Name of the partition, should be something like /dev/sda1, /dev/sdb2 ...
        """
        self.logger = logging.getLogger(UdiskDevice.__module__ + "." + UdiskDevice.__class__.__name__)

        self._device = device
        self._mount_path = None   # will be the mounted path

    def _udisks_extract_mount_path(self, udisk_output: str) -> Path:
        """
        Extract mount path from udisksctl output.
        :param output: udisksctl ouput.
        :return: The mounted path.
        """
        self.logger.debug("_udisks_extract_mount_path : %s", udisk_output)
        # ouput is like : Mounted /dev/sdc1 at /media/benjamin/B291-4FA9.
        m = re.search(UDISK_MOUNTED_PATH_REGEX, udisk_output, flags=re.MULTILINE)
        if m is not None:
            return Path(m.groups()[0])
        return None

    def mount(self) -> Path:
        """
        Will mount the device.
        :raises MissingUdisckError: If udisksctl isn't found
        :raises MountError: If the mount command failed.
        :return: Mount path
        """
        self.logger.debug("Mounting : %s", self.dev_name)
        try:
            p = subprocess.Popen(['udisksctl', 'mount', '-b', self.dev_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, _ = p.communicate()
            self._mount_path = self._udisks_extract_mount_path(udisk_output=out.decode("utf8"))

            if self._mount_path is None:  # try if it's not already mounted
                self._mount_path = self._find_mount_path()

            if self._mount_path is None:
                self.logger.error("_find_mount_path: %s", self._find_mount_path())
                raise MountError("Mount path not found in udisksctl ouput for {}".format(self.dev_name))

            self.logger.debug("Mounted at : %s", self._mount_path)
            return self._mount_path
        except subprocess.CalledProcessError as ex:
            self.logger.error("{} not mounted".format(self.dev_name))
            raise MountError("Mount of {devname} (cmd:{r.cmd}) returned exit code {r.returncode} with stderr {r.stderr}".format(
                devname=self.dev_name,
                r=ex
            ))
        except FileNotFoundError:
            self.logger.error("udisks not installed on system")
            raise MissingUdiskError("udisks not installed on system")

    def unmount(self):
        """ Unmount the device."""
        self.logger.debug("Unmounting : %s", self.dev_name)
        try:
            p = subprocess.Popen(['udisksctl', 'unmount', '-b', self.dev_name], stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
            p.communicate()

            self._mount_path = None
        except subprocess.CalledProcessError as ex:
            self.logger.error("{} not unmounted".format(self.dev_name))
            raise UnMountError(
                "Mount of {devname} (cmd:{r.cmd}) returned exit code {r.returncode} with stderr {r.stderr}".format(
                    devname=self.dev_name,
                    r=ex
                ))
        except FileNotFoundError:
            self.logger.error("udisks not installed on system")
            raise MissingUdiskError("udisks not installed on system")

    def _find_mount_path(self) -> Path:
        """
        Find the mount Path if it exists. Check mount point in /proc/mounts
        :return: The mount Path. Or None if not mounted.
        """
        with open("/proc/mounts", "r") as mounts:
            for line in mounts:
                if line.startswith(self.dev_name):
                    return Path(line.split(' ')[1])

        return None

    def is_mounted(self) -> bool:
        """ Tell if the device is mounted, refesh the mount_path property"""
        # When using diskctl, mount folder is created at mount and deleted after.
        # So we just need to check if the mount folder is existing.
        # We also found the mount Path if not already done.
        if self._mount_path is None:  # try to find mount Path
            self._mount_path = self._find_mount_path()

        return self._mount_path is not None and self._mount_path.exists()

    @property
    def mount_path(self) -> Path:
        """ Return the mounted path. Will mount it if it's not already done."""
        if not self.is_mounted():
            self.mount()
        return self._mount_path

    @property
    def dev_name(self) -> str:
        """ Return device name. """
        return self._device['DEVNAME']

    @property
    def parent_dev_name(self) -> str:
        """
        Return the parent device name (without partition number)
        :return: The parent device name.
        """
        if 'parent' in self._device:
            return self._device.parent['DEVNAME']
        else:
            return self._device['DEVNAME'][:-1]


class MountError(Exception):
    """ When mount goes badly, see message for more details on the error"""
    pass


class MissingUdiskError(Exception):
    """ When mounting fail because of udisck missing (udisksctl command not found in PATH) """
    pass


class UnMountError(Exception):
    """ When unmount goes badly, see message for more details on the error"""
    pass