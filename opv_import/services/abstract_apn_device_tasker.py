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
# Description: Handle a set of ApnDevices and apply (only once) a task on each device.
#              Abstract class need to be implemented (implement the task).

import logging
import pyudev
from abc import abstractmethod
from typing import Callable

from opv_import.helpers.udev_observer import create_udev_block_observer
from opv_import.helpers import ThreadPool

from opv_import import model

import threading

SD_UDEV_OBSERVER_NAME = "OPV SD card import"
UNTRACK_SEEN_DEVICE = -1  # Allow same device to be seen multiple times, usefull for setting the devices conf


class AbstractApnDeviceTasker:

    def __init__(self, number_of_worker: int, number_of_devices: int=UNTRACK_SEEN_DEVICE):
        """
        Initiate an AbstractApnDeviceTasker class. Used to watch an apply a task on each devices.
        :param number_of_worker: Number of thread that can run simultaneously.
        :param number_of_devices: Number of devices to watch (used to know when we have finished. Default -1, disable devices seen notions.
        """
        self.logger = logging.getLogger(AbstractApnDeviceTasker.__module__ + "." + AbstractApnDeviceTasker.__class__.__name__)

        self._number_of_devices = number_of_devices
        self._number_of_workers = number_of_worker

        self._udev_observer = None
        self._copy_thread_pool = None

        # List of devices that where already seen by udev (are treated already or in pool for treatment)
        self._seen_devices = []  # list of model.ApnDevices
        self._seen_devices_lock = threading.Lock()

        # Event to know when a device
        self._see_all_event = threading.Event()

    def _add_seen_device(self, device: model.ApnDevice):
        """
        Add Device APN to treated list and remove it from the waiting list (in pool).
        :param device: Device to be added.
        """
        self.logger.debug("Adding to treated device : %r", device)

        self._seen_devices_lock.acquire()
        self._seen_devices.append(device)
        self._seen_devices_lock.release()

    @abstractmethod
    def _generate_task(self, device: model.ApnDevice) -> Callable:
        """
        Generate the task lambda for a device. ABSTRACT.
        :param device: Device APN.
        :raises: NotImplemented
        """
        raise NotImplemented()

    def _is_seen_device(self, device: model.ApnDevice) -> bool:
        """
        Tells if the device was already seen by udev, so assuming treatment will or is already done.
        :param device: Device.
        :return: True if treatment will or is already done.
        """
        is_in = False
        self._seen_devices_lock.acquire()
        for d in self._seen_devices:
            if d.apn_number == device.apn_number:
                is_in = True
                break

        # telling we have seen all devices
        if len(self._seen_devices) == self._number_of_devices:
            self._see_all_event.set()
            self._see_all_event.clear()

        self._seen_devices_lock.release()

        return is_in

    def _add_device_to_treatment(self, device: model.ApnDevice):   # abstract method
        """
        Add a device to the treament chain (for copy).
        :param device:
        :return:
        """
        # You need to add task to Queue first, because the seen event will wait on the queue
        # and is triggered by the add_seen_device
        self._copy_thread_pool.add_task(self._generate_task(device=device))

        if UNTRACK_SEEN_DEVICE != self._number_of_devices:
            self._add_seen_device(device=device)

    def _on_udev_event(self, action: str, device: pyudev.Device):
        """
        When a device change, called by udev observer.
        :param action: Device action state.
        :param device: The udev device.
        """
        if action == "add" and 'DEVNAME' in device.keys() and "partition" in device.attributes.available_attributes:
            self.logger.debug("Device %s added", device['DEVNAME'])
            device_model = model.ApnDevice(device_name=device['DEVNAME'])

            if not self._is_seen_device(device=device_model):
                self._add_device_to_treatment(device=device_model)
            else:
                self.logger.debug("Device already seen")

    def start(self):
        """
        Start observing for new devices plugged-in.
        """
        # Starting thread pool
        self._copy_thread_pool = ThreadPool(number_of_workers=self._number_of_workers)
        self._copy_thread_pool.start()

        # Observing for storage devices to be plugged in
        self._udev_observer = create_udev_block_observer(self._on_udev_event, observer_name=SD_UDEV_OBSERVER_NAME)
        self._udev_observer.start()

    def wait(self):
        """ Wait for all devices to be treated"""
        self._see_all_event.wait()  # Wait until we have seen all devices
        self._copy_thread_pool.wait_all_task_treated()   # Wait until all copy task are done

    def stop(self, force: bool=False):
        """
        Stop watching for new devices and thread pool.
        :param force: If True will try to unlock waiting also.
        """
        if force:
            self._see_all_event.set()
            self._see_all_event.clear()

        try:
            self._udev_observer.stop()
        except ValueError:  # Observer pipe migth be already closed which though a I/O operation on closed file.
            pass
        finally:
            self._copy_thread_pool.stop()