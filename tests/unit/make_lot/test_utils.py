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
# Description: Unit test for utils.

import opv_import.makelot.utils as ut

def test_bit_len():
    assert ut.bit_len(0) == 0, "Wrong bit length"
    assert ut.bit_len(1) == 1, "Wrong bit length"
    assert ut.bit_len(2) == 2, "Wrong bit length"
    assert ut.bit_len(3) == 2, "Wrong bit length"
    assert ut.bit_len(4) == 3, "Wrong bit length"
