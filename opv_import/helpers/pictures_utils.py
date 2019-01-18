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
# Description: Utils functions for pictures managment.

import datetime
import exifread

def read_exif_time(pic_path: str) -> int:
    """
    Read DateTimeOriginal tag from exif data.

    :param pic_path: Pictures location.
    :type pic_path: str
    :return: Pictures taken time, timestamp.
    :rtype: float (timestamp)
    """
    with open(pic_path, "rb") as f:
        tags = exifread.process_file(f, details=False)
    
    subsec = 0
    if "EXIF SubSecTimeOriginal" in tags.keys():
        subsec = tags['EXIF SubSecTimeOriginal'].values

    capture_time = datetime.datetime.strptime(tags['EXIF DateTimeOriginal'].values[:19], "%Y:%m:%d %H:%M:%S")
    capture_time += datetime.timedelta(seconds=float("0." + subsec))
    timestamp = float(capture_time.timestamp)

    return timestamp
