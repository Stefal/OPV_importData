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
# Description: Unit test GeoPoint representation.

from opv_import.makelot.geopoint import GeoPoint

class TestGeoPoint(object):

    def test_properties(self):
        p = GeoPoint(lat=44.987137, lon=6.482013, alt=1522.112)

        assert p.lon == 6.482013, "Longitude isn't well set"
        assert p.lat == 44.987137, "La isn't well set"
        assert p.alt == 1522.112, "Longitude isn't well set"
        assert p.coordinates[0] == 44.987137
        assert p.coordinates[1] == 6.482013
        assert p.coordinates[2] == 1522.112

    def test_eq(self):
        pa = GeoPoint(lat=44.987137, lon=6.482013, alt=1522.112)
        pb = GeoPoint(lat=44.987137, lon=6.482013, alt=18)
        pc = GeoPoint(lat=44.987137, lon=2, alt=1522.112)
        pd = GeoPoint(lat=44, lon=6.482013, alt=1522.112)
        pabis = GeoPoint(lat=44.987137, lon=6.482013, alt=1522.112)

        assert pa == pabis, "Equality test, should be equals"
        assert pa != pb, "Altitude are different"
        assert pa != pc, "Longitude are different"
        assert pa != pd, "Latitude are different"

    def test_repr(self):
        p = GeoPoint(lat=44.987137, lon=6.482013, alt=1522.112)

        assert p.__repr__() == "GeoPoint(lon: 6.482013, lat: 44.987137, alt: 1522.112)"
