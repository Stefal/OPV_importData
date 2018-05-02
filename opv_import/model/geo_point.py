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
# Description: Represent a geolocated point.

from geojson import Point

class GeoPoint(Point):

    def __init__(self, lon: float=0, lat: float=0, alt: float=0):
        """
        Intantiate a geolocation point (not oriented).
        :param lon: Longitude.
        :type lon: int.
        :param lat: Latitude.
        :type lat: int
        :param alt: Altitude.
        :type alt: int
        """
        Point.__init__(self, (lat, lon, alt))

    @property
    def lat(self) -> float:
        """ Latitude """
        return self.coordinates[0]

    @lat.setter
    def lat(self, lat: float):
        """ Set latitude """
        self.coordinates[0] = lat

    @property
    def lon(self) -> float:
        """ Longitude """
        return self.coordinates[1]

    @lon.setter
    def lon(self, lon: float):
        """ Set longitude """
        self.coordinates[1] = lon

    @property
    def alt(self) -> float:
        """ Altitude """
        return self.coordinates[2]

    @lat.setter
    def lat(self, alt: float):
        """ Set altitude """
        self.coordinates[2] = alt

    def __repr__(self):
        return "GeoPoint(lon: {}, lat: {}, alt: {})".format(self.lon, self.lat, self.alt)
