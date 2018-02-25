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
# Description: Genrate set of indexes to find cam reference indexes.
#              Generate a list of indexes that can be used to find image indexes references.
#              Exemple :
#                    [0, 0, 0]
#                    [1, 0, 0]
#                    [0, 1, 0]
#                    [1, 1, 0]
#                    [0, 0, 1]
#                    [1, 0, 1]
#                    [0, 1, 1]
#                    [1, 1, 1]
#                    [2, 0, 0]
#                    [3, 0, 0]
#                    [2, 1, 0]
#                    [3, 1, 0]

from typing import List, Iterator
from opv_import.makelot.utils import bit_len

def get_bit_pos_in_global_index(apn_no: int, cam_bit_pos: int, nb_cams: int) -> int:
    """
    Return bit position of cam_bit_pos from apn_no

    :param apn_no: APN number.
    :type apn_no: int
    :param cam_bit_pos: Bit position of the camera index.
    :type cam_bit_pos: int
    :param nb_cams: Number of cameras handled by the global index.
    :type nb_cams: int
    :return: The bit position in global index.
    :rtype: int
    """
    return nb_cams * cam_bit_pos + apn_no

def get_cam_indexes(global_index: int, nb_cams: int, nb_of_bit_per_index: int) -> List[int]:
    """
    Convert global_index init a list of camera indexes.

    :param global_index: Global index contains all camera indexes.
    :type: global_index: int
    :param nb_cams: number of cameras represented in global index.
    :type nb_cams: int
    :param nb_of_bit_per_index: Number of bit per camera index.
    :type nb_of_bit_per_index: int
    :return: list of camera indexes extracted from global_index.
    """
    cam_indexes = [0] * nb_cams

    for bit_pos in range(0, nb_of_bit_per_index):
        for apn_no in range(0, nb_cams):
            bit_val = (global_index >> get_bit_pos_in_global_index(apn_no=apn_no, cam_bit_pos=bit_pos, nb_cams=nb_cams)) & 1
            mask = bit_val << bit_pos
            cam_indexes[apn_no] |= mask

    return cam_indexes

def get_global_index(list_cam_indexes: List[int]) -> int:
    """
    Mix cam indexes bits to generate the corresponding global index.

    :param list_cam_indexes: List of camera indexes, position 0 is for camera 0.
    :type: List[int]
    :return: The corresponding global index.
    :rtype: int
    """
    global_index = 0
    nb_cams = len(list_cam_indexes)
    for apn_no in range(0, nb_cams):
        index_cam = list_cam_indexes[apn_no]
        for bit_pos in range(0, bit_len(index_cam)):
            bit_val = (index_cam >> bit_pos) & 1
            global_index |= bit_val << get_bit_pos_in_global_index(apn_no=apn_no, cam_bit_pos=bit_pos, nb_cams=nb_cams)
    return global_index

def indexes_walk(nb_cams: int, cam_max_indexes: List[int], cam_start_indexes: List[int]=None) -> Iterator[List[int]]:
    """
    Generate list of camera indexes in an optimized order.

    :param nb_cams: Number of cameras.
    :type nb_cams: int
    :param cam_max_indexes: list of camera max indexes (pos 0 for apn0 max indexes or number of pic, ...)
    :type cam_max_indexes: List[int]
    :param cam_start_indexes: Start indexes, Default will start a 0.
    :type cam_start_indexes: List[int]
    :return: Generator, generate list of camera indexes in optimal order for test references.
    :rtype: Iterator[List[int]]
    """
    next_global_index = 0
    cam_start_indexes = [0] * nb_cams if cam_start_indexes is None else cam_start_indexes

    indexes_shift = cam_start_indexes

    last_global_index = get_global_index(cam_max_indexes)
    nb_of_bit_per_index = bit_len(max(cam_max_indexes))

    def is_valid_cam_indexes(cam_indexes):
        for apn_no in range(0, nb_cams):
            if cam_indexes[apn_no] > cam_max_indexes[apn_no] or cam_indexes[apn_no] < cam_start_indexes[apn_no]:
                return False
        return True

    while next_global_index <= last_global_index:
        cam_indexes = get_cam_indexes(global_index=next_global_index, nb_cams=nb_cams, nb_of_bit_per_index=nb_of_bit_per_index)
        cam_indexes = [cam_indexes[i] + indexes_shift[i] for i in range(0, nb_cams)]

        if is_valid_cam_indexes(cam_indexes):
            yield cam_indexes

        next_global_index += 1
