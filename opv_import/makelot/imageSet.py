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
# Description: Represent a image set, image set are several images used to make a panorama.

from typing import Dict, List
from collections import UserDict
from opv_import.makelot import CameraImage

IMAGESET_DEFAULT_SIZE = 6  # should be somewhere else

class ImageSet(UserDict):

    def __init__(self, l: Dict[int, CameraImage]={}, number_of_pictures: int=IMAGESET_DEFAULT_SIZE):
        """
        Initialize a set of pictures.

        :param number_of_pictures: Number of pictures in a complete set. Default is IMAGESET_DEFAULT_SIZE.
        :type number_of_pictures: int
        """
        UserDict.__init__(self, l)
        self.number_of_pictures = number_of_pictures

    def is_complete(self) -> bool:
        """
        Check if the set is complete.

        :return: True if the set is complete.
        :rtype: bool
        """
        return len(self.data) == self.number_of_pictures

    def get_pic_taken_before(self, img_set: 'ImageSet') -> List[int]:
        """
        Compare current camera images timestamps to img_set camera images timestamps.
        If at least one camera (let say cam number "x") picture of current set as a taken date before the same camera (cam "x") picture of img_set return True.
        This method might be used to detect anormal set with pictures taken before some other set (back in time issues).

        :param img_set: Image set that should be have pictures taken after current set.
        :type img_set: ImageSet
        :return: List of apn_id of pictures in current set, taken before img_set.
        :rtype: List[int]
        """
        ids = []
        for apn_id in self.data.keys():
            if apn_id in img_set and self.data[apn_id].get_timestamp() < img_set[apn_id].get_timestamp():
                ids.append(apn_id)

        return ids
