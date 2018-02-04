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
# Description: test rederbro CSV meta data.

from unittest.mock import patch
from opv_import.makelot import RederbroMeta, GeoPoint, OrientationAngle

class TestRederbroMeta(object):

    @patch("opv_import.makelot.geopoint.GeoPoint")
    def test_init(self, mock_geopt):
        p = mock_geopt()
        o = OrientationAngle(degree=2, minutes=3)
        gp_err = {0: True, 1: False}

        meta = RederbroMeta(timestamp=2, geopoint=p, orientation=o, gopro_errors=gp_err)
        assert meta.timestamp == 2
        assert meta.orientation == o
        assert meta.gopro_errors == gp_err

    @patch("opv_import.makelot.geopoint.GeoPoint")
    def test_has_took_picture(self, mock_geopt):
        p = mock_geopt()
        o = OrientationAngle(degree=2, minutes=3)
        gp_err = {0: False, 1: True}

        meta = RederbroMeta(timestamp=2, geopoint=p, orientation=o, gopro_errors=gp_err)
        assert not meta.has_took_picture(apn_id=0)
        assert meta.has_took_picture(apn_id=1)
        assert not meta.has_took_picture(apn_id=10)
