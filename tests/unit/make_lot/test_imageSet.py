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
# Description: Unit test image set.

from unittest.mock import patch
from opv_import import ImageSet

class TestImageSet(object):

    @patch("opv_import.makelot.cameraImage")
    def get_list_camera_image(self, mock_camImg, nb_pic):
        r = {}
        for i in range(0, nb_pic):
            r[i] = mock_camImg()
        return r

    def test_is_complete_ok(self):
        nb_img = 6
        img_set = ImageSet(l=self.get_list_camera_image(nb_pic=nb_img), number_of_pictures=nb_img)

        assert img_set.number_of_pictures == nb_img, "Number of pictures is incorrect"
        assert img_set.is_complete(), "ImageSet should be complete"

    def test_is_complete_fail(self):
        nb_img = 6
        img_set = ImageSet(l=self.get_list_camera_image(nb_pic=nb_img + 1), number_of_pictures=nb_img)

        assert not img_set.is_complete(), "Complete set should be incomplete"
