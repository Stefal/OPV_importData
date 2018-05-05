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
# Description: APN Device (storage device) tests.

import pytest
from opv_import.model import ApnDevice
from opv_import.model.apn_device import APN_CONF_NUMBER_KEY, APN_CONF_RELATIVE_PATH, APN_DEFAULT_CONFIG
from unittest.mock import patch, MagicMock, call
from path import Path


class TestApnDevice(object):

    @patch("path.Path.exists")
    @patch("opv_import.helpers.UdiskDevice.dev_name")
    @patch("opv_import.helpers.UdiskDevice.__init__")
    @patch("json.load")
    @patch("opv_import.helpers.UdiskDevice.mount_path")
    @patch("builtins.open", create=True)
    def test__load_configuration(self, mock_open, mock_udisk_mount_path, mock_json, mock_udisk_init, mock_disk_dev_name, mock_path_exists):
        mnt_path = Path("/mnt/SD1")

        # Parent class
        mock_udisk_init.return_value = None
        mock_udisk_mount_path.return_value = mnt_path
        mock_disk_dev_name.return_value = "/dev/sda1"

        # Open Mock
        file_mock = MagicMock()
        ctx_open = MagicMock()
        ctx_open.__enter__ = MagicMock()
        ctx_open.__enter__.return_value = file_mock
        ctx_open.__exit__ = MagicMock()
        mock_open.return_value = ctx_open

        # Path
        mock_path_exists.return_value = True

        # Json mock
        mock_json.return_value = {APN_CONF_NUMBER_KEY: 42}

        device = ApnDevice(device_name="/dev/sda1")
        device._load_configuration()

        assert mock_path_exists.call_count == 1
        assert mock_open.call_args_list == [call(mnt_path / APN_CONF_RELATIVE_PATH, 'r')]
        assert mock_json.call_count == 1
        assert device._apn_conf == mock_json.return_value

    @patch("path.Path.exists")
    @patch("opv_import.helpers.UdiskDevice.dev_name")
    @patch("opv_import.helpers.UdiskDevice.__init__")
    @patch("json.load")
    @patch("opv_import.helpers.UdiskDevice.mount_path")
    @patch("builtins.open", create=True)
    def test__load_configuration_default(self, mock_open, mock_udisk_mount_path, mock_json, mock_udisk_init, mock_disk_dev_name,
                                 mock_path_exists):
        mnt_path = Path("/mnt/SD1")

        # Parent class
        mock_udisk_init.return_value = None
        mock_udisk_mount_path.return_value = mnt_path
        mock_disk_dev_name.return_value = "/dev/sda1"

        # Open Mock
        file_mock = MagicMock()
        ctx_open = MagicMock()
        ctx_open.__enter__ = MagicMock()
        ctx_open.__enter__.return_value = file_mock
        ctx_open.__exit__ = MagicMock()
        mock_open.return_value = ctx_open

        # Path
        mock_path_exists.return_value = False

        # Json mock
        mock_json.return_value = {APN_CONF_NUMBER_KEY: 42}

        device = ApnDevice(device_name="/dev/sda1")
        device._load_configuration()

        assert mock_path_exists.call_count == 1
        assert mock_open.call_count == 0
        assert mock_json.call_count == 0
        assert device._apn_conf == APN_DEFAULT_CONFIG

    @patch("opv_import.helpers.UdiskDevice.__init__")
    def test_ignore_unexisting_configuration(self, mock_disk_init):
        device = ApnDevice(device_name="/dev/sda1")
        device.ignore_unexisting_configuration = True

        assert device.ignore_unexisting_configuration == True

    @patch("opv_import.helpers.UdiskDevice.__init__")
    @patch("opv_import.model.ApnDevice._load_configuration")
    def test_apn_number(self, mock_load_conf, mock_disk_init):
        device = ApnDevice(device_name="/dev/sda1")
        device._apn_conf = APN_DEFAULT_CONFIG
        device._apn_conf[APN_CONF_NUMBER_KEY] = 42
        device.apn_number

        assert mock_load_conf.call_count == 0

    @patch("opv_import.helpers.UdiskDevice.mount_path")
    @patch("opv_import.model.ApnDevice._load_configuration")
    @patch("opv_import.helpers.UdiskDevice.dev_name")
    @patch("opv_import.helpers.UdiskDevice.__init__")
    @patch("builtins.open", create=True)
    @patch("json.dump")
    def test_save_config(self, mock_json, mock_open, mock_device_init, mock_devname, mock_load_conf, mock_udisk_mount_path):
        mock_devname.return_value = "/dev/sda1"

        # Open Mock
        file_mock = MagicMock()
        ctx_open = MagicMock()
        ctx_open.__enter__ = MagicMock()
        ctx_open.__enter__.return_value = file_mock
        ctx_open.__exit__ = MagicMock()
        mock_open.return_value = ctx_open

        # Parent class
        mnt_path = Path("/mnt/SD1")
        mock_udisk_mount_path.return_value = mnt_path

        device = ApnDevice(device_name="/dev/sda1")
        device.save_config()

        assert mock_load_conf.call_count == 1
        assert mock_open.call_count == 1
        assert mock_json.call_count == 1
        assert mock_udisk_mount_path.call_count == 1

