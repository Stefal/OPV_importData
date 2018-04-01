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

import datetime
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
        self.geopoint = geopoint
        self.gopro_errors = gopro_errors
        self.id_meta = None  # for dev and debug purposes

    def has_took_picture(self, apn_id: int) -> bool:
        """
        Indicate if a camera took pictures.Dict

        :param apn_id: ID of the camera
        :type apn_id: int
        :return: True if the camera took a picture according to the rederbro metas.
        :rtype: bool
        """
        return self.gopro_errors[apn_id] if apn_id in self.gopro_errors else False

    def has_error(self) -> bool:
        """
        Indicate if at least one camera had an error.

        :return: True if an error occured
        :rtype: bool
        """
        for statut in self.gopro_errors.values():
            if statut:
                return True
        return False

    def get_timestamp(self) -> int:
        """
        Get meta timestamp.

        :return: the timestamp.
        :rtype: int
        """
        return self.timestamp

    def __eq__(ma, mb) -> bool:
        """
        Equality between 2 meta data.

        :param ma: First rederbro meta (current/self)
        :param mb: Second rederbor meta.
        :return: True if both are the same.
        :rtype: bool
        """
        return (
            ma.timestamp == mb.timestamp and
            ma.orientation == mb.orientation and
            ma.geopoint == mb.geopoint and
            ma.gopro_errors == mb.gopro_errors
        )

    def __repr__(self) -> str:
        """
        Printable version of a rederbro meta.

        :return: Printable representation of a meta.
        """
        d = datetime.datetime.fromtimestamp(self.timestamp)
        return "RederbroMeta(id_meta: {}, date: {}, orientation: {}, gopro_errors: {}, geopoint: {})".format(self.id_meta, d.ctime(), self.orientation, self.gopro_errors, self.geopoint)
