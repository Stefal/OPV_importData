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
# Description: Test - Configurer service.

import pytest
from unittest.mock import patch, MagicMock, PropertyMock, call

from opv_import.model.apn_device import ApnDeviceNumberNotFoundError
from opv_import.model import ApnDevice
from opv_import.services import SdConfigurer

class TestSdConfigurer(object):

    @patch("opv_import.services.AbstractApnDeviceTasker.__init__")
    def test_unconfigured_device(self, mock_parent_init):
        ask_pan_num = MagicMock()
        ask_pan_num.return_value = 42

        # apn_device mock
        apn_device = MagicMock(ApnDevice)
        #apn_num_prop = PropertyMock(side_effect=ApnDeviceNumberNotFoundError())
        apn_num_prop = MagicMock()
        apn_num_prop.__get__ = MagicMock(side_effect=ApnDeviceNumberNotFoundError())
        apn_num_prop.__set__ = MagicMock()
        type(apn_device).apn_number = apn_num_prop

        sd_conf = SdConfigurer(ask_apn_num=ask_pan_num)
        task = sd_conf._generate_task(device=apn_device)
        task()

        assert ask_pan_num.call_args_list == [call(apn_device)]
        assert apn_num_prop.__get__.call_count == 0
        assert apn_num_prop.__set__.call_args_list == [call(apn_device, 42)]

    @patch("opv_import.services.AbstractApnDeviceTasker.__init__")
    def test_configured_device(self, mock_parent_init):
        ask_pan_num = MagicMock()
        ask_pan_num.return_value = 42

        # apn_device mock
        apn_device = MagicMock(ApnDevice)
        # apn_num_prop = PropertyMock(side_effect=ApnDeviceNumberNotFoundError())
        apn_num_prop = MagicMock()
        apn_num_prop.__get__ = MagicMock(return_value=30)
        apn_num_prop.__set__ = MagicMock()
        type(apn_device).apn_number = apn_num_prop

        sd_conf = SdConfigurer(ask_apn_num=ask_pan_num)
        task = sd_conf._generate_task(device=apn_device)
        task()

        assert ask_pan_num.call_args_list == [call(apn_device)]
        assert apn_num_prop.__get__.call_count == 0
        assert apn_num_prop.__set__.call_args_list == [call(apn_device, 42)]
