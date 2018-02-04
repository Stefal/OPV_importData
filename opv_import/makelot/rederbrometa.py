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
# Description: Represent rederbro CSV meta data.

from typing import Dict
from collections import namedtuple
from opv_import.makelot import GeoPoint

OrientationAngle = namedtuple("OrientationAngle", ["degree", "minutes"])

class RederbroMeta():

    def __init__(self, timestamp: int=0, geopoint: GeoPoint=None, orientation: OrientationAngle=None, gopro_errors: Dict[int, bool]={}):
        """
        Create a RederbroMeta which contains meta such as geolocation, orientation and camera error indicator.

        :param timestamp: Meta timestamp.
        :type timestamp: int
        :param geopoint: Geolocated position of the pictures.
        :type geopoint: GeoPoint
        :param orientation: Compass sensor informations.
        :type orientation: OrientationAngle, angle in dregree and minutes.
        :param gopro_errors: camera error indicator, a dictionnary apn_id -> boolean, False if camera had an issue
        :type gopro_errors: Dict[int, bool]
        """
        self.timestamp = timestamp
        self.orientation = orientation
        self.gopro_errors = gopro_errors

    def has_took_picture(self, apn_id: int) -> bool:
        """
        Indicate if a camera took pictures.Dict

        :param apn_id: ID of the camera
        :type apn_id: int
        :return: True if the camera took a picture according to the rederbro metas.
        :rtype: bool
        """
        return self.gopro_errors[apn_id] if apn_id in self.gopro_errors else False

    def __eq__(ma, mb):
        return (
            ma.timestamp == mb.timestamp and
            ma.orientation == mb.orientation and
            ma.gopro_errors == mb.gopro_errors
        )
