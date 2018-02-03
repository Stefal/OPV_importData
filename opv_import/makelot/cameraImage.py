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
# Description: Represent a camera image file.

import opv_import
from path import Path
from opv_import import pictures_utils

class CameraImage:
    def __init__(self, path: Path):
        """
        Intentiate a camera image.

        :param path: picture path.
        :type path: Path (path.py)
        """
        self.path = path
        self._ts = None
        self.leveled_ts = None

    def get_timestamp(self):
        """
        Returns pictures timestamp.

        :return: return picture timestamp.
        """
        if self._ts is None:
            self._ts = pictures_utils.read_exif_time(self.path)

        return self._ts

    def __eq__(ca, cb):
        """ 2 cam images are equal if they represent the same file"""
        print("__eq__")
        print(ca.path)
        print(cb.path)
        return ca.path == cb.path

    def __repr__(self):
        return "Path: {} / Timestamp: {}".format(self.path, self._ts)
