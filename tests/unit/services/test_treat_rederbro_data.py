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
# Description: Test - Treat all rederbro datas.

import pytest
from unittest.mock import patch, call, MagicMock
from path import Path

from opv_import.services import TreatRederbroData

class TestTreatRederbroData(object):

    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    @patch("path.Path.exists")
    @patch("opv_import.services.RessourceManager")
    @patch("opv_import.services.LotMaker")
    def test_construct(self, lm, ressman, path_exists, opv_api, opv_dm):
        path_exists.return_value = True

        trd = TreatRederbroData(cam_pictures_dir=Path("/tmp/toto"), id_malette=42, csv_meta_path=Path("/tmp/toto.csv"), opv_api_client=opv_api, opv_dm_client=opv_dm)

        assert path_exists.call_count == 2
        assert ressman.call_args_list == [call(opv_api_client=opv_api, opv_dm_client=opv_dm, id_malette=42)]
        assert lm.call_args_list == [call(pictures_path=Path("/tmp/toto"),
                                          rederbro_csv_path=Path("/tmp/toto.csv"),
                                          nb_cams=6)]

    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    @patch("path.Path.exists")
    @patch("opv_import.services.RessourceManager")
    @patch("opv_import.services.LotMaker")
    def test_parse_metas(self, lm, ressman, path_exists, opv_api, opv_dm):
        path_exists.return_value = True

        mock_lm = MagicMock()
        mock_lm.load_metas = MagicMock()
        lm.return_value = mock_lm

        trd = TreatRederbroData(cam_pictures_dir=Path("/tmp/toto"), id_malette=42, csv_meta_path=Path("/tmp/toto.csv"),
                                opv_api_client=opv_api, opv_dm_client=opv_dm)
        trd.parse_metas()
        trd.parse_metas()

        assert mock_lm.load_metas.call_count == 1

    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    @patch("path.Path.exists")
    @patch("opv_import.services.RessourceManager")
    @patch("opv_import.services.LotMaker")
    def test_generate_camera_sets(self, lm, ressman, path_exists, opv_api, opv_dm):
        path_exists.return_value = True

        mock_lm = MagicMock()
        mock_lm.make_gopro_set_new = MagicMock()
        lm.return_value = mock_lm

        trd = TreatRederbroData(cam_pictures_dir=Path("/tmp/toto"), id_malette=42, csv_meta_path=Path("/tmp/toto.csv"),
                                opv_api_client=opv_api, opv_dm_client=opv_dm)
        trd.generate_camera_sets()
        trd.generate_camera_sets()

        assert mock_lm.make_gopro_set_new.call_count == 1

    @patch("opv_import.services.TreatRederbroData.generate_camera_sets")
    @patch("opv_import.services.TreatRederbroData.parse_metas")
    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    @patch("path.Path.exists")
    @patch("opv_import.services.RessourceManager")
    @patch("opv_import.services.LotMaker")
    def test_make_lot(self, lm, ressman, path_exists, opv_api, opv_dm, parse_meta, generate_cam_set):
        path_exists.return_value = True

        mock_lm = MagicMock()
        mock_lm.generate_all_lot = MagicMock()
        lm.return_value = mock_lm

        trd = TreatRederbroData(cam_pictures_dir=Path("/tmp/toto"), id_malette=42, csv_meta_path=Path("/tmp/toto.csv"),
                                opv_api_client=opv_api, opv_dm_client=opv_dm)
        trd.make_lot()
        trd.make_lot()

        assert parse_meta.call_count == 1
        assert generate_cam_set.call_count == 1
        assert mock_lm.generate_all_lot.call_args_list == [call(img_sets=None, threshold_incomplete_set_max_in_window=4, threshold_incomplete_set_window_size=10, threshold_max_consecutive_incomplete_sets=35),]

    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    @patch("path.Path.exists")
    @patch("opv_import.services.RessourceManager")
    @patch("opv_import.services.LotMaker")
    def test_create_campaign(self, lm, ressman, path_exists, opv_api, opv_dm):
        path_exists.return_value = True

        mock_ressman = MagicMock()
        mock_ressman.make_campaign = MagicMock()
        ressman.return_value = mock_ressman

        trd = TreatRederbroData(cam_pictures_dir=Path("/tmp/toto"), id_malette=42, csv_meta_path=Path("/tmp/toto.csv"),
                                opv_api_client=opv_api, opv_dm_client=opv_dm)

        trd.create_campaign(name="ma campagne", id_rederbro=2, description="my description")
        trd.create_campaign(name="ma campagne", id_rederbro=2, description="my description")

        assert mock_ressman.make_campaign.call_args_list == [call(name="ma campagne", id_rederbro=2, description="my description")]

    @patch("opv_directorymanagerclient.DirectoryManagerClient")
    @patch("opv_api_client.RestClient")
    @patch("path.Path.exists")
    @patch("opv_import.services.RessourceManager")
    @patch("opv_import.services.LotMaker")
    def test_save_all_lot(self, lm, ressman, path_exists, opv_api, opv_dm):
        path_exists.return_value = True

        mock_ressman = MagicMock()
        mock_ressman.make_campaign = MagicMock()
        ressman.return_value = mock_ressman

        trd = TreatRederbroData(cam_pictures_dir=Path("/tmp/toto"), id_malette=42, csv_meta_path=Path("/tmp/toto.csv"),
                                opv_api_client=opv_api, opv_dm_client=opv_dm)
        trd._campaign_created = True
        trd._campaign = MagicMock()
        l1 = MagicMock()
        l2 = MagicMock()
        trd._lots = [l1, l2]
        progress_event = MagicMock()
        trd.save_all_lot(on_progress_listener=progress_event)

        assert mock_ressman.make_lot.call_args_list == [
            call(lot=l1, campaign=trd._campaign),
            call(lot=l2, campaign=trd._campaign)]
        assert progress_event.call_args_list == [call(0.5), call(1)]