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
# Description: Unit test for ressource-db service.

import pytest
from opv_import.services import RessourceManager
from opv_import.model import RederbroMeta, OrientationAngle, GeoPoint, Lot, ImageSet, CameraImage
from opv_api_client import ressources
from unittest.mock import patch, call, MagicMock
from path import Path

from typing import List

ID_MALETTE = 1

def cam_img(p, ts):
    c = CameraImage(path=Path(p))
    c._ts = ts
    return c


class TestRessourceManager(object):

    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    def test_make_campaign(self, mock_dbrest_client, mock_dm_client):
        mock_make = MagicMock()
        mock_campaign_create = MagicMock()
        mock_dbrest_client.make = mock_make
        generated_campaign = MagicMock(ressources.Campaign)
        generated_campaign.id_campaign = 42
        generated_campaign.create = mock_campaign_create
        mock_make.return_value = generated_campaign

        ress_man = RessourceManager(opv_api_client=mock_dbrest_client, opv_dm_client=mock_dm_client, id_malette=ID_MALETTE)
        result_campaign = ress_man.make_campaign(name="my campaign", id_rederbro=1, description="my description")

        mock_make.call_args_list[0] = call(ressources.Campaign)

        assert result_campaign.id_malette == ID_MALETTE, "Wrong id malette on campaign"
        assert result_campaign.name == "my campaign", "Wrong campaign name"
        assert result_campaign.id_rederbro == 1, "Wrong id_rederbro"
        assert result_campaign.description == "my description", "Wrong description"
        assert mock_campaign_create.call_count == 1

    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    def test__model_gp_error_to_db(self, mock_dbrest_client, mock_dm_client):
        ress_man = RessourceManager(opv_api_client=mock_dbrest_client, opv_dm_client=mock_dm_client,
                                    id_malette=ID_MALETTE)

        assert ress_man._model_gp_error_to_db(bools={0:False, 1:False}) == 0
        assert ress_man._model_gp_error_to_db(bools={0: True, 1: False}) == 1
        assert ress_man._model_gp_error_to_db(bools={0: False, 1: True}) == 2
        assert ress_man._model_gp_error_to_db(bools={0: True, 1: True}) == 3

    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    def test_make_sensors(self, mock_dbrest_client, mock_dm_client):
        # mocking a RederbroMeta
        meta = MagicMock(RederbroMeta)
        meta.geopoint = MagicMock(GeoPoint)
        meta.geopoint.coordinates = [0, 1, 2]
        meta.orientation = MagicMock(OrientationAngle)
        meta.orientation.degree = 42.01
        meta.orientation.minutes = 4.04
        meta.get_timestamp = MagicMock()
        meta.get_timestamp.return_value = 1509154772  # Sat Oct 28 01:39:32 2017, UTC timestamp
        meta.gopro_errors = {0: True, 1: False}

        # OPV_client dbrest mock
        mock_make = MagicMock()
        mock_sensors_create = MagicMock()
        mock_dbrest_client.make = mock_make
        generated_sensors = MagicMock(ressources.Sensors)
        generated_sensors.id_sensors = 42
        generated_sensors.create = mock_sensors_create
        mock_make.return_value = generated_sensors

        ress_man = RessourceManager(opv_api_client=mock_dbrest_client, opv_dm_client=mock_dm_client,
                                    id_malette=ID_MALETTE)
        result_sensors = ress_man.make_sensors(meta=meta)

        mock_make.call_args_list[0] = call(ressources.Sensors)

        assert result_sensors.id_malette == ID_MALETTE, "Wrong id malette on campaign"
        assert result_sensors.gps_pos.coordinates == meta.geopoint.coordinates
        assert result_sensors.degrees == meta.orientation.degree
        assert result_sensors.minutes == meta.orientation.minutes
        assert mock_sensors_create.call_count == 1

    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    @patch("os.link")
    @patch("path.Path.copy")
    def test_make_picture_path_no_hardlink(self, mock_path_copy, mock_os_link, mock_dbrest_client, mock_dm_client):

        # mocking DM Client
        dm_ctx = MagicMock()
        dm_ctx.__enter__ = MagicMock()
        dm_ctx.__enter__.return_value = ("uuid-42", "/tmp")
        dm_ctx.__exit__ = MagicMock()
        mock_dm_client.Open.return_value = dm_ctx

        # Image set
        img_set = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0001.JPG", 10),
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0000.JPG", 15)
        })

        ress_man_no = RessourceManager(opv_api_client=mock_dbrest_client, opv_dm_client=mock_dm_client,
                                    id_malette=ID_MALETTE, use_hardlink=False)
        result_uuid = ress_man_no.make_picture_path(img_set=img_set)

        assert result_uuid == "uuid-42"
        assert mock_path_copy.call_count == 2, "Path copy wasn't call to copy the pictures"
        assert mock_os_link.call_count == 0, "Os.link should be called only in hardlink mode"

    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    @patch("os.link")
    @patch("path.Path.copy")
    def test_make_picture_path_hardlink(self, mock_path_copy, mock_os_link, mock_dbrest_client, mock_dm_client):
        # mocking DM Client
        dm_ctx = MagicMock()
        dm_ctx.__enter__ = MagicMock()
        dm_ctx.__enter__.return_value = ("uuid-42", "/tmp")
        dm_ctx.__exit__ = MagicMock()
        mock_dm_client.Open.return_value = dm_ctx

        # Image set
        img_set = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0001.JPG", 10),
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0000.JPG", 15)
        })

        ress_man_no = RessourceManager(opv_api_client=mock_dbrest_client, opv_dm_client=mock_dm_client,
                                       id_malette=ID_MALETTE, use_hardlink=True)
        result_uuid = ress_man_no.make_picture_path(img_set=img_set)

        assert result_uuid == "uuid-42"
        assert mock_path_copy.call_count == 0, "Path copy wasn't call to copy the pictures"
        assert mock_os_link.call_count == 2, "Os.link should be called only in hardlink mode"


    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    def test_make_lot(self, mock_dbrest_client, mock_dm_client):
        # mocking a lot
        meta = MagicMock(RederbroMeta)
        meta.geopoint = MagicMock(GeoPoint)
        meta.geopoint.coordinates = [0, 1, 2]
        meta.orientation = MagicMock(OrientationAngle)
        meta.orientation.degree = 42.01
        meta.orientation.minutes = 4.04
        meta.get_timestamp = MagicMock()
        meta.get_timestamp.return_value = 1509154772  # Sat Oct 28 01:39:32 2017, UTC timestamp
        meta.gopro_errors = {0: True, 1: False}

        # OPV_client dbrest mock
        mock_make = MagicMock()
        mock_sensors_create = MagicMock()
        mock_dbrest_client.make = mock_make
        generated_sensors = MagicMock(ressources.Sensors)
        generated_sensors.id_sensors = 42
        generated_sensors.create = mock_sensors_create
        mock_make.return_value = generated_sensors

        ress_man = RessourceManager(opv_api_client=mock_dbrest_client, opv_dm_client=mock_dm_client,
                                    id_malette=ID_MALETTE)
        result_sensors = ress_man.make_sensors(meta=meta)

        mock_make.call_args_list[0] = call(ressources.Sensors)

        assert result_sensors.id_malette == ID_MALETTE, "Wrong id malette on campaign"
        assert result_sensors.gps_pos.coordinates == meta.geopoint.coordinates
        assert result_sensors.degrees == meta.orientation.degree
        assert result_sensors.minutes == meta.orientation.minutes
        assert mock_sensors_create.call_count == 1