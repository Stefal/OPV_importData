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
# Description: Test - SD cleaner service.

import pytest
from unittest.mock import patch, MagicMock, call, PropertyMock
from path import Path
from opv_import.model import ApnDevice, FileSystem
from opv_import.services import SdCleaner

from typing import Callable

class TestSdCleaner(object):

    @patch("subprocess.run")
    @patch("opv_import.services.AbstractApnDeviceTasker.__init__")
    def test__mkfs(self, mock_abs_init, mock_subprocress):
        device = MagicMock(ApnDevice)
        type(device).dev_name = PropertyMock(return_value="/dev/sdc1")

        sd_cleaner = SdCleaner(fs=FileSystem.FAT32)
        sd_cleaner._mkfs(device=device)

        assert device.mount.call_args_list == [call()]
        assert device.unmount.call_args_list == [call()]
        assert mock_subprocress.call_args_list == [call(['sudo', 'mkfs', "-t", "vfat", "-F", "32", "/dev/sdc1"])]

    @patch("opv_import.services.SdCleaner._mkfs")
    @patch("opv_import.services.AbstractApnDeviceTasker.__init__")
    def test__generate_task(self, mock_abs_init, mock_mkfs):
        iso_path = MagicMock(Path)
        iso_path.exists = MagicMock(return_value=True)
        iso_path.__str__ = MagicMock(return_value="img.iso")

        device = MagicMock(ApnDevice)
        device.unmount = MagicMock(Callable)
        type(device).apn_number = PropertyMock(return_value=42)

        clean_event_listener = MagicMock(Callable)

        sd_cleaner = SdCleaner(fs=FileSystem.FAT32)
        sd_cleaner.on_clean(clean_event=clean_event_listener)
        task = sd_cleaner._generate_task(device=device)
        task()

        assert mock_mkfs.call_args_list == [call(device=device)]
        assert sd_cleaner.is_device_transfert_terminated(apn_number=42)
        assert clean_event_listener.call_args_list == [call(device)]
