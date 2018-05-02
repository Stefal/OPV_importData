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
# Description: Test - Abstract helper to manage copies from an external device (SD cards, hardrives ...).

import pytest
from opv_import.helpers import DeviceCopier
from path import Path
from unittest.mock import patch, call, MagicMock


class TestDeviceCopier(object):

    def test__udisks_extract_mount_path(self):
        devc = DeviceCopier(device_name="/dev/sdc1")
        assert devc._udisks_extract_mount_path(
            udisk_output='Mounted /dev/sdc1 at /media/benjamin/B291-4FA9.\n') == Path("/media/benjamin/B291-4FA9")
        assert devc._udisks_extract_mount_path(
            udisk_output='\nMounted /dev/sdc1 at /media/benjamin/B291-4FA9.\n\n') == Path("/media/benjamin/B291-4FA9")
        assert devc._udisks_extract_mount_path(
            udisk_output='\nMounted /dev/sdc1 at \n') is None

    @patch("subprocess.Popen")
    def test__mount_ok(self, mock_popen):
        p = MagicMock()
        p.communicate = MagicMock()
        out = MagicMock(bytes)
        out.decode = MagicMock()
        out.decode.return_value = 'Mounted /dev/sdc1 at /media/benjamin/B291-4FA9.\n'
        p.communicate.return_value = (out, MagicMock())
        mock_popen.return_value = p

        devc = DeviceCopier(device_name="/dev/sdc1")
        assert devc._mount() == "/media/benjamin/B291-4FA9"
        assert mock_popen.call_args_list == [call(['udisksctl', 'mount', '-b', '/dev/sdc1'], stderr=-1, stdout=-1)]

