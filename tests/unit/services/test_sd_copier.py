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
# Description: Test - Watch for storage devices to be inserted and copy their DCMI folder to a destination folder.

import pytest
from unittest.mock import MagicMock, patch, call

from opv_import.services import SdCopier, AbstractApnDeviceTasker
from opv_import.services.sd_copier import COPY_NUMBER_OF_WORKERS
from opv_import.helpers import RsyncWrapper
from opv_import.model import ApnDevice
from path import Path

class TestSdCopier(object):

    @patch("opv_import.services.AbstractApnDeviceTasker.__init__")
    def test_dest_path(self, mock_parent_init):
        def apn_to_dest(apn_number):
            return Path("path/APN{n}".format(n=apn_number))

        sd_cp = SdCopier(number_of_devices=2, apn_id_to_dest=apn_to_dest)
        assert sd_cp.dest_path(42) == Path("path/APN42")
        assert mock_parent_init.call_args_list == [call(sd_cp, number_of_worker=COPY_NUMBER_OF_WORKERS, number_of_devices=2)]

    @patch("opv_import.services.sd_copier.RsyncWrapper")
    @patch("opv_import.services.AbstractApnDeviceTasker.__init__")
    def test_generate_task(self, mock_parent_init, mock_rsync_construct):
        def apn_to_dest(apn_number):
            return Path("path/APN{n}".format(n=apn_number))

        # apn_device mock
        apn_device = MagicMock(ApnDevice)
        apn_device.apn_number = 0
        apn_device.mount_path = "/mnt/SD"


        mock_rsync = MagicMock(RsyncWrapper)
        mock_rsync_construct.return_value = mock_rsync

        sd_cp = SdCopier(number_of_devices=2, apn_id_to_dest=apn_to_dest)
        task = sd_cp._generate_task(device=apn_device)

        task()

        assert mock_rsync_construct.call_args_list == [call(source_path=Path("/mnt/SD/DCIM"), destination_path=Path("path/APN0"))]
        assert mock_rsync.on_progress.call_count == 1
        assert mock_rsync.on_terminate.call_count == 1
        assert mock_rsync.run.call_count == 1

    @patch("opv_import.services.AbstractApnDeviceTasker.__init__")
    def test_is_device_transfert_terminated(self, m_parent):
        def apn_to_dest(apn_number):
            return Path("path/APN{n}".format(n=apn_number))

        sd_cp = SdCopier(number_of_devices=2, apn_id_to_dest=apn_to_dest)

        assert not sd_cp.is_device_transfert_terminated(apn_number=42)
