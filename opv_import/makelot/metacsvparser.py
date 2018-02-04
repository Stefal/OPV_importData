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
# Description: Parse rederbro CSV into a list of RederbroMeta

import csv
import time
from path import Path
from typing import Dict, List
from opv_import.makelot import RederbroMeta, OrientationAngle, GeoPoint

class MetaCsvParser():

    def __init__(self, csv_path: Path):
        self._csv_path = csv_path
        self._metas = None  # cache metas

    def _map_gp_error(self, csv_goprofailled: str) -> Dict[int, bool]:
        """
        Map a gopro_errors int into a dict apn_id -> failed.

        :param csv_goprofailled: Goprofailled CSV entry part, eg : "000000"
        :type: str
        :return: A dict with status for each camera id.
        :rtype: Dict[int, bool]
        """
        gp_err = {}
        goprofailled = int(csv_goprofailled, 2)
        for apn_id in range(0, len(csv_goprofailled)):
            gp_err[apn_id] = not bool((goprofailled >> apn_id) & 1)

        return gp_err

    def _map_orientation(self, csv_orientation: str) -> OrientationAngle:
        """
        Map a CSV orientation entry into an OrientationAngle object.

        :param csv_orientation: backpack orientation data which is like "305° 51'"
        :type: str
        :return: parsed OrientationAngle
        :rtype: OrientationAngle
        """
        degree, minutes = csv_orientation.split('\u00b0')
        minutes = minutes.replace(" ", "").replace("'", "")
        degree = float(degree)
        minutes = float(minutes)
        return OrientationAngle(degree=degree, minutes=minutes)

    def _map_time(self, csv_date: str) -> int:
        """
        Map CSV date into a timestamp.

        :param csv_date: CSV date formated like "Sat Oct 28 08:11:03 2017".
        :type csv_date: str
        :return: Corresponding timestamp.
        :rtype: int
        """
        return int(time.mktime(time.strptime(csv_date)) - 2 * 3600)  # ugly fix, we don't have dst info didn't found better

    def fetch_metas(self) -> List[RederbroMeta]:
        """
        Parse CSV file and return RederbroMeta doesn't cache it, use get_metas() instead.

        :return: The rederbro metas.
        :rtype: List[RederbroMeta]
        """
        metas = []

        passHeader = False
        with open(self._csv_path, 'r') as csvFile:
            d = csv.reader(csvFile, skipinitialspace=True, delimiter=';')
            for row in d:

                # pass the first line
                if not passHeader:
                    passHeader = True
                    continue

                # prevent empty lines
                if len(row) == 0:
                    continue

                # Convert data into rederbro metas
                timestamp = self._map_time(csv_date=row[0])
                lat = float(row[1])
                lng = float(row[2])
                alt = float(row[3])
                point = GeoPoint(lat=lat, lon=lng, alt=alt)
                orientation = self._map_orientation(csv_orientation=row[4])
                gp_err = self._map_gp_error(csv_goprofailled=row[5])

                meta = RederbroMeta(timestamp=timestamp, geopoint=point, orientation=orientation, gopro_errors=gp_err)

                metas.append(meta)

        return metas

    def get_metas(self) -> List[RederbroMeta]:
        """
        Fetch or returned cached metas.

        :return: Rederbro meta.
        :rtype: List[RederbroMeta]
        """
        if self._metas is None:
            self._metas = self.fetch_metas()

        return self._metas

    def get_meta(self, index: int) -> RederbroMeta:
        """
        Get a meta at a specific index (start at 0).

        :param index: Position of the meta in the CSV.
        :type index: int
        :return: A meta.
        :rtype: RederbroMeta
        """
        metas = self.get_metas()
        return metas[index]
