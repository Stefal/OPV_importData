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
# Description: test rederbro CSV meta parser.

from unittest.mock import patch, MagicMock, ANY
from opv_import.makelot import MetaCsvParser, RederbroMeta, GeoPoint, OrientationAngle

class TestMetaCsvParser(object):

    def test__map_gp_error(self):
        parser = object.__new__(MetaCsvParser)
        gp_err = parser._map_gp_error(csv_goprofailled='1001')
        expected_gp_err = {0: False, 1: True, 2: True, 3: False}

        assert gp_err == expected_gp_err, "Parsing of goprofailled Failled"

    def test__map_orientation(self):
        parser = object.__new__(MetaCsvParser)
        o = parser._map_orientation(csv_orientation="305° 51'")

        assert o.degree == 305, "Degree parsing failled"
        assert o.minutes == 51, "Minutes parsing failled"

    def test__map_time(self):
        parser = object.__new__(MetaCsvParser)
        ts = parser._map_time(csv_date="Sat Oct 28 08:11:03 2017")

        assert ts == 1509171063, "CSV date not correctly parsed"

    @patch("csv.reader")
    @patch("builtins.open", create=True)
    def test_fetch_metas_inte(self, mock_open, mock_csv_reader):
        csv_mocked = MagicMock()
        csv_mocked.__iter__.return_value = iter([
            ['time', 'lat', 'lon', 'alt', 'rad', 'goProFailed'],
            ['Sat Oct 28 01:39:32 2017', '44.987811', '6.079870', '986.3', "308° 43'", '00'],
            [],
            ['Sat Oct 28 01:40:21 2017', '44.987778', '6.079897', '986.463', "329° 37'", '10']
        ])
        mock_csv_reader.return_value = csv_mocked

        parser = MetaCsvParser(csv_path="toto.csv")
        metas = parser.fetch_metas()

        expected_metas = [
            RederbroMeta(
                timestamp=1509147572,  # Sat Oct 28 01:39:32 2017
                geopoint=GeoPoint(lat=44.987811, lon=6.079870, alt=986.3),
                orientation=OrientationAngle(degree=308, minutes=43),
                gopro_errors={0: True, 1: True}
            ),
            RederbroMeta(
                timestamp=1509147621,  # Sat Oct 28 01:40:21 2017
                geopoint=GeoPoint(lat=44.987778, lon=6.079897, alt=986.463),
                orientation=OrientationAngle(degree=329, minutes=37),
                gopro_errors={0: True, 1: False}
            )
        ]

        mock_open.assert_called_with("toto.csv", 'r')
        mock_csv_reader.assert_called_with(ANY, skipinitialspace=True, delimiter=';')

        assert metas == expected_metas, "Wrong meta from parsing"

    @patch("opv_import.makelot.metacsvparser.MetaCsvParser.fetch_metas")
    def test_get_metas(self, mock_fetch_meta):
        mock_fetch_meta.return_value = []

        parser = MetaCsvParser(csv_path="toto.csv")
        parser.get_metas()
        r = parser.get_metas()

        assert mock_fetch_meta.call_count == 1, "Cache not used"
        assert r == []

    @patch("opv_import.makelot.metacsvparser.MetaCsvParser.get_metas")
    def test_get_meta(self, mock_get_metas):
        mock_get_metas.return_value = [
            RederbroMeta(
                timestamp=1509147621,  # Sat Oct 28 01:40:21 2017
                geopoint=GeoPoint(lat=44.987778, lon=6.079897, alt=986.463),
                orientation=OrientationAngle(degree=329, minutes=37),
                gopro_errors={0: True, 1: False}
            )
        ]

        parser = object.__new__(MetaCsvParser)

        assert parser.get_meta(index=0) == mock_get_metas.return_value[0], "Get specific index wrong"
