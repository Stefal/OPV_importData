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
# Description: Unit test of the rsync wrapper.

from tempfile import TemporaryDirectory
from opv_import.helpers import RsyncWrapper
from path import Path

from typing import Callable

from unittest.mock import MagicMock, call

class TestInteRsyncWrapper:

    def test_all(self):
        # listeners
        on_progress = MagicMock(Callable)
        on_terminate = MagicMock(Callable)

        def create_test_file(file_path):
            with open(file_path, "w") as f:
                f.write("Test file")

        with TemporaryDirectory() as source:
            source_path = Path(source)
            for i in range(0, 10):
                create_test_file(file_path=(source_path / "test_file_{n}.txt".format(n=i)))

            with TemporaryDirectory() as dest:
                dest_path = Path(dest)

                rsync = RsyncWrapper(source_path=source_path / "", destination_path=dest_path)
                rsync.on_progress(on_progress)
                rsync.on_terminate(on_terminate)
                rsync.run()

                assert Path(dest_path / "test_file_{n}.txt".format(n=9)).exists()
                assert len(on_progress.call_args_list) > 1
                assert on_terminate.call_args_list == [call()]
