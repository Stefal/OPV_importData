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

    @patch("opv_import.makelot.geopoint.GeoPoint")
    def test_has_error(self, mock_geopt):
        p = mock_geopt()
        o = OrientationAngle(degree=2, minutes=3)

        meta_err = RederbroMeta(timestamp=2, geopoint=p, orientation=o, gopro_errors={0: False, 1: True})
        meta_ok = RederbroMeta(timestamp=2, geopoint=p, orientation=o, gopro_errors={0: False, 1: False})
        assert meta_err.has_error()
        assert not meta_ok.has_error()

    @patch("opv_import.makelot.geopoint.GeoPoint")
    @patch("opv_import.makelot.geopoint.GeoPoint.__eq__")
    def test_eq(self, mock_geopt, mock_geopt_eq):
        p = mock_geopt()
        o = OrientationAngle(degree=2, minutes=3)
        meta_a = RederbroMeta(timestamp=3, geopoint=p, orientation=o, gopro_errors={0: False, 1: True})
        meta_b = RederbroMeta(timestamp=2, geopoint=p, orientation=o, gopro_errors={0: False, 1: False})
        meta_c = RederbroMeta(timestamp=2, geopoint=p, orientation=o, gopro_errors={0: False, 1: False})

        mock_geopt_eq.side_effect = [False, True]
        assert meta_a != meta_b, "Meta equality"
        assert meta_b == meta_c
