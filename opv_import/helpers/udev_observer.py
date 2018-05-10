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
# Description: Simply create an udev observer.

import pyudev

def create_udev_block_observer(event_listener, observer_name: str) -> pyudev.MonitorObserver:
    """
    Create an udev block observer.
    :param event_listener: Lambda executed when a new block device is detected. Will be executed with and : action: str, device: pyudev.Device
    :param observer_name: Name of the observer.
    :return: The created observer.
    """
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by(subsystem='block')

    return pyudev.MonitorObserver(monitor, event_listener, name=observer_name)