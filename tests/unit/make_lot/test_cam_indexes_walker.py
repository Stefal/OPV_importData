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
# Description: Unit test for walk util functions.

import opv_import.makelot.cam_indexes_walker as iwalker

def test_get_bit_pos_in_global_index():
    assert iwalker.get_bit_pos_in_global_index(apn_no=0, cam_bit_pos=0, nb_cams=3) == 0, "Wrong bit position"
    assert iwalker.get_bit_pos_in_global_index(apn_no=3, cam_bit_pos=0, nb_cams=3) == 3, "Wrong bit position"
    assert iwalker.get_bit_pos_in_global_index(apn_no=2, cam_bit_pos=2, nb_cams=3) == 8, "Wrong bit position"

def test_get_cam_indexes():
    assert iwalker.get_cam_indexes(global_index=int('110', 2), nb_cams=3, nb_of_bit_per_index=2) == [0, 1, 1]
    assert iwalker.get_cam_indexes(global_index=int('100110', 2), nb_cams=3, nb_of_bit_per_index=2) == [0, 1, 3]

def test_get_global_index():
    assert iwalker.get_global_index(list_cam_indexes=[0, 1, 1]) == int('110', 2)
    assert iwalker.get_global_index(list_cam_indexes=[0, 1, 3]) == int('100110', 2)

def test_indexes_walk():
    gen = iwalker.indexes_walk(nb_cams=2, cam_max_indexes=[3, 3])
    gen_with_start = iwalker.indexes_walk(nb_cams=2, cam_max_indexes=[3, 3], cam_start_indexes=[1, 2])

    assert gen.__next__() == [0, 0]
    assert gen.__next__() == [1, 0]
    assert gen.__next__() == [0, 1]
    assert gen.__next__() == [1, 1]
    assert gen_with_start.__next__() == [1, 2]
    assert gen_with_start.__next__() == [2, 2]
