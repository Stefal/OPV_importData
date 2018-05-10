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

import pytest
from unittest.mock import patch, MagicMock, call

from typing import Callable
from opv_import.helpers import RsyncWrapper
from path import Path

class TestRsyncWrapper(object):


    def test_on_progress_registration_and_fire(self):
        my_listener = MagicMock(Callable)
        my_other_listener = MagicMock(Callable)

        rsync = RsyncWrapper(source_path=Path("/tmp/a"), destination_path=Path("/tmp/b"))
        assert rsync.on_progress(my_listener) == "progress_0", "Default event listener name, first one"
        assert rsync.on_progress(my_other_listener, even_listener_name="other_listener") == "other_listener", "Named event listener"

        rsync._RsyncWrapper__fire_progress_event(global_progression=0.5)
        rsync._RsyncWrapper__fire_progress_event(global_progression=0.7)
        rsync._RsyncWrapper__fire_progress_event(global_progression=0.9)
        assert my_listener.call_args_list == [call(0.5), call(0.7), call(0.9)]
        assert my_other_listener.call_args_list == [call(0.5), call(0.7), call(0.9)]
        assert rsync.global_progress == 0.9


    def test_on_terminate_registration_and_fire(self):
        my_listener = MagicMock(Callable)
        my_other_listener = MagicMock(Callable)

        rsync = RsyncWrapper(source_path=Path("/tmp/a"), destination_path=Path("/tmp/b"))
        assert rsync.on_terminate(my_listener) == "terminate_0", "Default event listener name, first one"
        assert rsync.on_terminate(my_other_listener, even_listener_name="other_listener") == "other_listener", "Named event listener"

        rsync._RsyncWrapper__fire_terminate_event()
        assert my_listener.call_args_list == [call()]
        assert my_other_listener.call_args_list == [call()]

    def test__read_current_popen_stdout(self):
        # Unable to find a suitable a not too complexe test for it
        assert True

    @patch("opv_import.helpers.RsyncWrapper._RsyncWrapper__fire_terminate_event")
    @patch("opv_import.helpers.RsyncWrapper._RsyncWrapper__fire_progress_event")
    @patch("opv_import.helpers.RsyncWrapper._read_current_popen_stdout")
    @patch("subprocess.Popen")
    def test_run(self, mock_popen, mock_read_iter, mock_fire_progress, mock_terminate):
        # output of popen
        mock_read_iter.return_value = [
            "      2,266,891 50%   30.88MB/s    0:00:00 (xfr#1, to-chk=1/4)",
            "      2,266,891 100%   30.88MB/s    0:00:00 (xfr#1, to-chk=1/4)",
            "     30,566,258 100%   29.50MB/s    0:00:00 (xfr#2, to-chk=0/4)"
        ]

        rsync = RsyncWrapper(source_path=Path("/tmp/a"), destination_path=Path("/tmp/b"))
        rsync.run()

        assert mock_popen.call_args_list == [call(['rsync', '-P', '-av', Path('/tmp/a'), Path('/tmp/b')], stdout=-1)]
        assert mock_fire_progress.call_args_list == [call(global_progression=0.75), call(global_progression=0.75), call(global_progression=1.0)]
        assert mock_terminate.call_args_list == [call()]
