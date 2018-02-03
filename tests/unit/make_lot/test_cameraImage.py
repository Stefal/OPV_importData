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
# Description: Unit test camera image.

import pytest
from unittest.mock import patch, call
from opv_import import CameraImage
from path import Path

class TestCameraImage(object):

    @patch('opv_import.pictures_utils.read_exif_time')
    def test_get_timestamp_ok(self, pic_util_mock):
        ts = 10
        path = "toto.jpg"
        pic_util_mock.return_value = ts
        cam_pic = CameraImage(path=path)
        obtained_ts = cam_pic.get_timestamp()

        # calling more times
        cam_pic.get_timestamp()
        cam_pic.get_timestamp()

        assert len(pic_util_mock.call_args_list) == 1, "Exif reader was called more than once (performance issu)"
        assert pic_util_mock.call_args_list[0] == call(path), "Exif reader was called with the wrong image path"
        assert obtained_ts == ts, "Wrong timestamp"

    @patch('opv_import.pictures_utils.read_exif_time')
    def test_get_timestamp_failed(self, pic_util_mock):
        path = "404.jpg"
        cam_pic = CameraImage(path=path)

        pic_util_mock.side_effect = FileNotFoundError

        with pytest.raises(FileNotFoundError):
            cam_pic.get_timestamp()

    def test__eq__(self):
        ca = CameraImage(path=Path("ca.JPG"))
        ca_bis = CameraImage(path=Path("ca.JPG"))
        cc = CameraImage(path=Path("cc.JPG"))

        assert ca == ca_bis, "Equal files"
        assert ca != cc, "Different files"
