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
# Description: Unit test lot maker.

import pytest
import opv_import
from path import Path
from opv_import.makelot import LotMaker, CameraImage, ImageSet, CameraImageFetcher, MetaCsvParser, CameraBackInTimeError
from opv_import.makelot.lotMaker import SearchedRefImgSet, ImageSetWithFetcherIndexes
from unittest.mock import patch, call, DEFAULT

def cam_img(p, ts):
    c = CameraImage(path=Path(p))
    c._ts = ts
    return c

offset_a = 30
offset_b = 40

class TestLotMaker(object):

    def test__init__ok(self):
        pass

    @patch("opv_import.makelot.CameraImageFetcher.__init__")
    @patch("opv_import.makelot.CameraImageFetcher.fetch_images")
    def test_load_cam_images(self, mock_fetch_images, mock_fetchers_init):
        mock_fetchers_init.return_value = None

        lm = LotMaker(pictures_path=Path("picPath/"), rederbro_csv_path=None, nb_cams=2)
        r = lm.load_cam_images()

        assert mock_fetchers_init.call_args_list == [call(dcim_folder=Path("picPath/APN0/DCIM")), call(dcim_folder=Path("picPath/APN1/DCIM"))], \
            "Not instanciating 2 fetchers"
        assert mock_fetch_images.call_count == 2, "Didn't fetch images on the 2 cameras"
        assert len(r) == 2, "Should have 2 fetchers"

    def start_img_fetcher_fake_env(self, cameras):

        def fetcher_init(s, dcim_folder):
            s.dcim_folder = dcim_folder
            return None

        def fetcher_images(s):
            for (cam_path, pics) in cameras:
                if cam_path == s.dcim_folder:
                    return pics
            return []

        def fetcher_get_pic(s, index):
            return fetcher_images(s)[index]

        def fetcher_nb_pic(s):
            return len(fetcher_images(s))

        self.fetcher_patch = patch.multiple(
            CameraImageFetcher,
            __init__=DEFAULT,
            fetch_images=DEFAULT,
            get_pic=DEFAULT,
            nb_pic=DEFAULT,
            autospec=True)
        self.fetcher_mocks = self.fetcher_patch.start()
        self.fetcher_mocks['__init__'].side_effect = fetcher_init
        self.fetcher_mocks['fetch_images'].side_effect = fetcher_images
        self.fetcher_mocks['get_pic'].side_effect = fetcher_get_pic
        self.fetcher_mocks['nb_pic'].side_effect = fetcher_nb_pic

        return self.fetcher_mocks

    def stop_img_fetcher_fake_env(self):
        self.fetcher_patch.stop()

    @pytest.fixture
    def fetcher_test_env(self, request):
        """
        Mock with a test environnement with 2 cameras.
        """
        cam_a = [
            cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0000.JPG", offset_a + -2),  # TS : 28
            cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0001.JPG", offset_a + 10),  # SET 1, TS : 40
            cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0002.JPG", offset_a + 12),  # TS : 42
            cam_img("picPath/APN0/DCIM/101S3D_L/3D_L0000.JPG", offset_a + 20)   # SET 2, TS : 50
        ]
        cam_b = [
            cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0000.JPG", offset_b + 10),  # SET 1, TS : 50
            cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0001.JPG", offset_b + 20),  # SET 2, TS : 60
        ]

        cameras = [
            (Path("picPath/APN0/DCIM"), cam_a),
            (Path("picPath/APN1/DCIM"), cam_b),
        ]

        request.addfinalizer(self.stop_img_fetcher_fake_env)
        return self.start_img_fetcher_fake_env(cameras)

    @pytest.fixture
    def fetcher_test_env_back_in_time(self, request):
        """
        Mock with a test environnement with 2 cameras.
        """
        cam_a = [
            cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0000.JPG", offset_a + -2),  # TS : 28
            cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0001.JPG", offset_a + 10),  # SET 1, TS : 40
            cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0002.JPG", offset_a + 0),  # TS : 42
            cam_img("picPath/APN0/DCIM/101S3D_L/3D_L0000.JPG", offset_a + 20)   # SET 2, TS : 50
        ]
        cam_b = [
            cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0000.JPG", offset_b + 10),  # SET 1, TS : 50
            cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0001.JPG", offset_b + 20),  # SET 2, TS : 60
        ]

        cameras = [
            (Path("picPath/APN0/DCIM"), cam_a),
            (Path("picPath/APN1/DCIM"), cam_b),
        ]

        request.addfinalizer(self.stop_img_fetcher_fake_env)
        return self.start_img_fetcher_fake_env(cameras)

    def test_get_images(self, fetcher_test_env):
        lm = LotMaker(pictures_path=Path("picPath/"), rederbro_csv_path=None, nb_cams=2)
        img_set = lm.get_images(indexes=[0, 1])

        expected_img_set = ImageSet(
            l={
                0: CameraImage(path=Path("picPath/APN0/DCIM/100S3D_L/3D_L0000.JPG")),
                1: CameraImage(path=Path("picPath/APN1/DCIM/100S3D_L/3D_L0001.JPG"))
            },
            number_of_pictures=2)

        assert img_set == expected_img_set, "Wrong image set"

    def test_cam_set_generator(self, fetcher_test_env):
        lm = LotMaker(pictures_path=Path("picPath/"), rederbro_csv_path=None, nb_cams=2)
        lm.load_cam_images()

        reference_set = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0001.JPG", offset_a + 10),  # SET 1 cam A
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0000.JPG", offset_b + 10)   # SET 1 cam B
        })

        set_1 = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0001.JPG", offset_a + 10),
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0000.JPG", offset_b + 10)
        })
        set_2 = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/101S3D_L/3D_L0000.JPG", offset_a + 20),
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0001.JPG", offset_b + 20)
        })

        sets = [
            ImageSet(l={0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0000.JPG", offset_a + 0)}),
            set_1,
            ImageSet(l={0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0002.JPG", offset_a + 12)}),
            set_2
        ]

        set_gen = lm.cam_set_generator(reference_set=reference_set)

        assert set_gen.__next__() == ImageSetWithFetcherIndexes(set=sets[0], fetcher_next_indexes=[1, 0])
        assert set_gen.__next__() == ImageSetWithFetcherIndexes(set=sets[1], fetcher_next_indexes=[2, 1])
        assert set_gen.__next__() == ImageSetWithFetcherIndexes(set=sets[2], fetcher_next_indexes=[3, 1])
        assert set_gen.__next__() == ImageSetWithFetcherIndexes(set=sets[3], fetcher_next_indexes=[4, 2])

    def test_cam_set_generator_backintime_exception(self, fetcher_test_env_back_in_time):
        lm = LotMaker(pictures_path=Path("picPath/"), rederbro_csv_path=None, nb_cams=2)
        lm.load_cam_images()

        reference_set = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0001.JPG", offset_a + 10),  # SET 1 cam A
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0000.JPG", offset_b + 10)   # SET 1 cam B
        })

        set_gen = lm.cam_set_generator(reference_set=reference_set)

        with pytest.raises(CameraBackInTimeError) as excinfo:
            set_gen.__next__()
            set_gen.__next__()
            set_gen.__next__()

        assert excinfo.value.indexes == [2, 1]

    def test_is_equiv_ref(self, fetcher_test_env):
        lm = LotMaker(pictures_path=Path("picPath/"), rederbro_csv_path=None, nb_cams=2)

        set_1 = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0001.JPG", offset_a + 10),
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0000.JPG", offset_b + 10)
        })
        set_2 = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/101S3D_L/3D_L0000.JPG", offset_a + 20),
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0001.JPG", offset_b + 20)
        })
        set_3 = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0002.JPG", offset_a + 12),
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0001.JPG", offset_b + 20)
        })

        assert lm.is_equiv_ref(set_1, set_2), "Set should be considered equivalent"
        assert not lm.is_equiv_ref(set_1, set_3), "Set should be considered not equivalent"

    def test_make_gopro_lot_inte_mocked(self, fetcher_test_env):
        lm = LotMaker(pictures_path=Path("picPath/"), rederbro_csv_path=None, nb_cams=2)
        lm.load_cam_images()

        set_1 = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0001.JPG", offset_a + 10),
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0000.JPG", offset_b + 10)
        })
        set_2 = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/101S3D_L/3D_L0000.JPG", offset_a + 20),
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0001.JPG", offset_b + 20)
        })

        reference_set = ImageSet(l={
            0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0001.JPG", offset_a + 10),  # SET 1 cam A
            1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0000.JPG", offset_b + 10)   # SET 1 cam B
        })

        gp_sets = lm.make_gopro_lot(reference_set=reference_set)
        # gp_sets = None
        expected_sets = [set_1, set_2]

        assert gp_sets == expected_sets, "Correct sets weren't found"

    # def test_find_cam_img_set_ref_int_mocked(self, fetcher_test_env):
    #     lm = LotMaker(pictures_path=Path("picPath/"), rederbro_csv_path=None, nb_cams=2)
    #     lm.load_cam_images()
    #     search_ref_gen = lm.find_cam_img_set_ref(lot_count_for_test=4, max_incomplete_sets=2)
    #
    #     incomplete_set_first = ImageSet(l={
    #         0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0000.JPG", offset_a + -2)
    #     }, number_of_pictures=2)
    #     set_1 = ImageSet(l={
    #         0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0001.JPG", offset_a + 10),
    #         1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0000.JPG", offset_b + 10)
    #     }, number_of_pictures=2)
    #     second_incomplet_set = ImageSet(l={
    #         0: cam_img("picPath/APN0/DCIM/100S3D_L/3D_L0002.JPG", offset_a + 12)
    #     }, number_of_pictures=2)
    #     set_2 = ImageSet(l={
    #         0: cam_img("picPath/APN0/DCIM/101S3D_L/3D_L0000.JPG", offset_a + 20),
    #         1: cam_img("picPath/APN1/DCIM/100S3D_L/3D_L0001.JPG", offset_b + 20)
    #     }, number_of_pictures=2)
    #
    #     first_ref, first_sets, frist_gen = search_ref_gen.__next__()
    #     print("first_ref")
    #     print(first_ref)
    #     print("first_sets")
    #     print(first_sets)
    #
    #     assert first_ref == set_1, "Frist valid reference set found is not valid"
    #     assert first_sets == [incomplete_set_first, set_1, second_incomplet_set, set_2], "First images set not found"

    @patch("opv_import.makelot.MetaCsvParser.__init__")
    @patch("opv_import.makelot.MetaCsvParser.get_metas")
    def test_load_metas(self, mock_parser_metas, mock_parser_init):
        mock_parser_init.return_value = None
        mock_parser_metas.return_value = []

        lm = LotMaker(pictures_path=None, rederbro_csv_path="toto.csv", nb_cams=2)
        lm.load_metas()
        r = lm.load_metas()

        mock_parser_init.assert_called_with(csv_path="toto.csv")
        assert mock_parser_init.call_count == 1, "Init not cached"
        assert mock_parser_metas.call_count == 2
        assert r == mock_parser_metas.return_value

    def test_inte_find_meta_ref(self):

        pass
