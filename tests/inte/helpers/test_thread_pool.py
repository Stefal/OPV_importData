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
# Description: Thread pool integration test.

import threading
import time
from opv_import.helpers import ThreadPool


class TestInteThreadPool:

    def test_all(self):
        common_result_list = []
        common_result_lock = threading.Lock()

        def generate_task(id: int):
            def task():
                if id == 1:
                    time.sleep(1)

                common_result_lock.acquire()
                common_result_list.append(id)
                common_result_lock.release()
            return task

        pool = ThreadPool(number_of_workers=2)
        pool.start()
        pool.add_task(generate_task(0))
        pool.add_task(generate_task(1))
        pool.add_task(generate_task(2))
        pool.add_task(generate_task(3))
        pool.stop()

        assert len(common_result_list) == 4
        assert 0 in common_result_list
        assert 1 in common_result_list
        assert 2 in common_result_list
        assert 3 in common_result_list
        assert common_result_list[-1] == 1
