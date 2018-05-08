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
# Description: Unit test DeviceApn tasker.

import pytest
from unittest.mock import patch, MagicMock, call

import pyudev

from opv_import.model import ApnDevice
from opv_import.services import AbstractApnDeviceTasker
from opv_import.services.abstract_apn_device_tasker import SD_UDEV_OBSERVER_NAME

import threading

class TestAbstractApnDeviceTasker(object):

    @patch("threading.Lock")
    def test_seen_device(self, mock_lock_init):
        # lock
        mock_lock = MagicMock()
        mock_lock.acquire = MagicMock()
        mock_lock.release = MagicMock()
        mock_lock_init.return_value = mock_lock

        apn_device = MagicMock(ApnDevice)
        apn_device.apn_number = 0

        apn_device_other = MagicMock(ApnDevice)
        apn_device_other.apn_number = 1

        tasker = AbstractApnDeviceTasker(number_of_devices=2, number_of_worker=2)
        tasker._add_seen_device(device=apn_device)

        assert mock_lock.acquire.call_count == 1
        assert mock_lock.release.call_count == 1
        assert tasker._is_seen_device(apn_device)
        assert mock_lock.acquire.call_count == 2
        assert mock_lock.release.call_count == 2
        assert not tasker._is_seen_device(apn_device_other)

    @patch("threading.Lock")
    @patch("opv_import.services.AbstractApnDeviceTasker._add_seen_device")
    @patch("opv_import.services.AbstractApnDeviceTasker._generate_task")
    def test__add_device_to_treatment(self, mock_generate_task, mock_add_seen, mock_lock_init):
        # lock
        mock_lock = MagicMock()
        mock_lock.acquire = MagicMock()
        mock_lock.release = MagicMock()
        mock_lock_init.return_value = mock_lock

        # apn_device mock
        apn_device = MagicMock(ApnDevice)
        apn_device.apn_number = 0

        # mock generated task
        generated_task = MagicMock()
        mock_generate_task.return_value = generated_task

        tasker = AbstractApnDeviceTasker(number_of_devices=2, number_of_worker=2)
        tasker._copy_thread_pool = MagicMock()
        tasker._copy_thread_pool.add_task = MagicMock()
        tasker._add_device_to_treatment(device=apn_device)

        assert mock_add_seen.call_args_list == [call(device=apn_device)]
        assert mock_generate_task.call_args_list == [call(device=apn_device)]
        assert tasker._copy_thread_pool.add_task.call_args_list == [call(generated_task)]

    @patch("threading.Lock")
    @patch("opv_import.services.AbstractApnDeviceTasker._add_seen_device")
    @patch("opv_import.services.AbstractApnDeviceTasker._generate_task")
    def test__add_device_to_treatment_seen_disble(self, mock_generate_task, mock_add_seen, mock_lock_init):
        # lock
        mock_lock = MagicMock()
        mock_lock.acquire = MagicMock()
        mock_lock.release = MagicMock()
        mock_lock_init.return_value = mock_lock

        # apn_device mock
        apn_device = MagicMock(ApnDevice)
        apn_device.apn_number = 0

        # mock generated task
        generated_task = MagicMock()
        mock_generate_task.return_value = generated_task

        tasker = AbstractApnDeviceTasker(number_of_worker=2)  # number of devices unset
        tasker._copy_thread_pool = MagicMock()
        tasker._copy_thread_pool.add_task = MagicMock()
        tasker._add_device_to_treatment(device=apn_device)

        assert mock_add_seen.call_args_list == []
        assert mock_generate_task.call_args_list == [call(device=apn_device)]
        assert tasker._copy_thread_pool.add_task.call_args_list == [call(generated_task)]

    @patch("opv_import.model.ApnDevice")
    @patch("opv_import.services.AbstractApnDeviceTasker._is_seen_device")
    @patch("opv_import.services.AbstractApnDeviceTasker._add_device_to_treatment")
    def test__on_udev_event(self, mock_add_treat, mock_is_seen, mock_apn_device):
        # mock pyudev.Device
        udev_dev = MagicMock(pyudev.Device)
        udev_dev.__dict__['DEVNAME'] = "/dev/sdc1"
        udev_dev.keys = MagicMock()
        udev_dev.keys.return_value = ['DEVNAME']
        udev_dev.attributes = MagicMock()
        udev_dev.attributes.available_attributes = ["partition"]

        # apn_device mock
        apn_device = MagicMock(ApnDevice)
        apn_device.apn_number = 0
        mock_apn_device.return_value = apn_device

        # mock is seen
        mock_is_seen.return_value = False

        tasker = AbstractApnDeviceTasker(number_of_devices=2, number_of_worker=2)
        tasker._on_udev_event("add", udev_dev)

        assert mock_apn_device.call_args_list[-1] == call(device_name=udev_dev['DEVNAME'])
        assert mock_is_seen.call_args_list[-1] == call(device=apn_device)
        assert mock_add_treat.call_args_list[-1] == call(device=apn_device)

        # mock is seen
        mock_is_seen.return_value = True

        # repeating same call
        tasker._on_udev_event("add", udev_dev)

        assert mock_apn_device.call_args_list[-1] == call(device_name=udev_dev['DEVNAME'])
        assert mock_is_seen.call_args_list[-1] == call(device=apn_device)
        assert mock_add_treat.call_count == 1

    @patch("opv_import.services.abstract_apn_device_tasker.ThreadPool")
    @patch("opv_import.services.abstract_apn_device_tasker.create_udev_block_observer")
    def test_start_stop(self, mock_observer_fact, mock_thread_pool):
        observer_mock = MagicMock()
        observer_mock.start = MagicMock()
        observer_mock.stop = MagicMock()
        mock_observer_fact.return_value = observer_mock

        mock_pool_instance = MagicMock()
        mock_pool_instance.start = MagicMock()
        mock_pool_instance.stop = MagicMock()
        mock_thread_pool.return_value = mock_pool_instance

        tasker = AbstractApnDeviceTasker(number_of_devices=2, number_of_worker=2)
        tasker.start()

        assert mock_thread_pool.call_args_list == [call(number_of_workers=2)]
        assert mock_pool_instance.start.call_count == 1
        assert mock_observer_fact.call_args_list == [call(tasker._on_udev_event, observer_name=SD_UDEV_OBSERVER_NAME)]
        assert observer_mock.start.call_count == 1

        tasker.stop()
        assert observer_mock.start.call_count == 1
        assert mock_pool_instance.stop.call_count == 1

    @patch("opv_import.services.abstract_apn_device_tasker.create_udev_block_observer")
    @patch("opv_import.services.abstract_apn_device_tasker.ThreadPool")
    @patch("threading.Event")
    def test_wait(self, mock_event, mock_thread_pool, mock_observer_fact):
        observer_mock = MagicMock()
        observer_mock.start = MagicMock()
        observer_mock.stop = MagicMock()
        mock_observer_fact.return_value = observer_mock

        mock_pool_instance = MagicMock()
        mock_pool_instance.wait_all_task_treated = MagicMock()
        mock_thread_pool.return_value = mock_pool_instance

        mock_event_instance = MagicMock(threading.Event)
        mock_event_instance.wait = MagicMock()
        mock_event.return_value = mock_event_instance

        tasker = AbstractApnDeviceTasker(number_of_devices=2, number_of_worker=2)
        tasker.start()
        tasker.wait()

        assert mock_event_instance.wait.call_count == 1
        assert mock_pool_instance.wait_all_task_treated.call_count == 1