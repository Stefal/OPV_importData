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
# Description: Test the udev observer factory.

import pytest
from unittest.mock import patch, MagicMock, call
from typing import Callable
import pyudev

from opv_import.helpers.udev_observer import create_udev_block_observer

@patch('pyudev.MonitorObserver')
@patch('pyudev.Monitor.from_netlink')
@patch('pyudev.Context')
def test_create_udev_block_observer(udev_context, udev_link, udev_monitor_observer):
    monitor = MagicMock(pyudev.Monitor)
    event_listener = MagicMock(Callable)
    udev_link.return_value = monitor

    assert create_udev_block_observer(event_listener, "Observer toto") != None
    assert udev_monitor_observer.call_args_list == [call(monitor, event_listener, name="Observer toto")]
