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
# Description: utility function relative to rederbro.

def read_rederbro_csv(csv_path: str) -> list:
    """
    Read the CSV file which correspond to the operation
    CSV is
    timestamp,lat,long,alt,degree°minutes,goproFailed
    return a list of Csv

    :param csv_path: location of a rederbor CSV file.
    :type csv_path: str
    :return: A list of sensorsMeta rederbor sensors data, in the CSV read order.
    :rtype: A list
    """
    data = []

    passHeader = False
    with open(csv_path, 'r') as csvFile:
        d = csv.reader(csvFile, delimiter=';')
        for row in d:

            # pass the first line
            if not passHeader:
                passHeader = True
                continue

            # prevent empty lines
            if len(row) == 0:
                continue

            # Convert data in a more writable way
            timestamp = int(time.mktime(time.strptime(row[0])))
            lat = float(row[1])
            lng = float(row[2])
            alt = float(row[3])
            degree, minutes = row[4].split('\u00b0')
            minutes = minutes.replace(" ", "").replace("'", "")
            degree = float(degree)
            minutes = float(minutes)
            goproFailed = int(row[5])

            sensorsMeta = {
                "takenDate": timestamp,
                "gps": {
                    "lat": lat,
                    "lon": lng,
                    "alt": alt
                },
                "compass": {
                    "degree": degree,
                    "minutes": minutes
                },
                "goproFailed": goproFailed
            }

            data.append(Csv(timestamp, sensorsMeta))
    return data
