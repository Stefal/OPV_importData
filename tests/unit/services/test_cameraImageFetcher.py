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
# Description: Unit test camera image fetcher.

import pytest
import opv_import
from unittest.mock import patch, MagicMock, call, DEFAULT
from opv_import.services import CameraImageFetcher
from opv_import.model import CameraImage

MOCKED_DIRS = ["/dir", "/dir/subdir"]

Path = opv_import.services.camera_image_fetcher.Path  # Prevent namespace errors


class TestCameraImageFetcher(object):

    def start_fake_env(self, directories_files):
        """
        Fake the existance of directories and files in it.

        :param directories_files: List of tuples :
            [ (Path('/root/'),
                [Path('/root/pica.JPG'), Path('/root/picb.JPG')],
                [Path('/root/dira'), Path('/root/dirb')]),
              ...
            ]
        """
        files_path = []
        dirs_path = []
        for d_f in directories_files:
            dirpath, dir_files_paths, dirs = d_f
            files_path.extend(dir_files_paths)
            dirs_path.extend(dirs_path)
            dirs_path.extend(dirs)

        def exists(p):
            return p in files_path

        def isfile(p):
            return p in files_path

        def isdir(p):
            return p in dirs_path

        def files(p):
            for d_f in directories_files:
                dirpath, dir_files_paths, _ = d_f
                if p == dirpath:
                    print(dir_files_paths)
                    return dir_files_paths
            return []

        def dirs(p):
            for d_f in directories_files:
                dirpath, _, dirs = d_f
                if p == dirpath:
                    return dirs
                return []

        self.fake_env_patcher = patch.multiple(
            "path.Path",
            isdir=DEFAULT,
            isfile=DEFAULT,
            files=DEFAULT,
            dirs=DEFAULT,
            exists=DEFAULT,
            autospec=True
        )
        self.fake_env_patcher_mocks = self.fake_env_patcher.start()
        self.fake_env_patcher_mocks['isdir'].side_effect = isdir
        self.fake_env_patcher_mocks['isfile'].side_effect = isfile
        self.fake_env_patcher_mocks['files'].side_effect = files
        self.fake_env_patcher_mocks['dirs'].side_effect = dirs
        self.fake_env_patcher_mocks['exists'].side_effect = exists

    def stop_fake_env(self):
        """
        Stop current fake env.
        """
        print("Stopped fake env")
        self.fake_env_patcher.stop()

    @patch("opv_import.services.CameraImageFetcher._extract_file_names_param")
    def test__init__ok(self, mock_extract_file_names_param):
        fetcher = CameraImageFetcher(dcim_folder=Path("/tmp/"))

        assert fetcher.dcim_folder == "/tmp/", "DCIM folder not correcly set"
        assert fetcher._img_start_index == opv_import.services.camera_image_fetcher.GORPRO_IMG_START_INDEX, "Default start index is wrong"
        assert mock_extract_file_names_param.called, "File format (prefix, extension ..) wasn't called in constructor"

    @patch("opv_import.services.CameraImageFetcher._extract_file_names_param", side_effect=opv_import.services.camera_image_fetcher.MissingDcfFolderError)
    def test__init__fail(self, mock_extract_file_names_param):
        with pytest.raises(opv_import.services.camera_image_fetcher.MissingDcfFolderError) as e:
            fetcher = CameraImageFetcher(dcim_folder=Path("/tmp/"))

    def test__order_dcf_dir_ok(self):
        fetcher = object.__new__(CameraImageFetcher)
        dcf_folders = [Path('130TXT'), Path('005TXT')]

        ordered = fetcher._order_dcf_dir(dcf_dirs=dcf_folders)
        assert len(ordered) == 2, "Missing folders during ordering"
        assert dcf_folders[0] == ordered[1], "Folders weren't ordered by dcf number"
        assert dcf_folders[1] == ordered[0], "Folders weren't ordered by dcf number"

    def test_order_dcf_files_ok(self):
        fetcher = object.__new__(CameraImageFetcher)
        dcf_files = [Path("3D_L0938.JPG"), Path("3D_L0900.JPG")]

        ordered = fetcher._order_dcf_files(dcf_files=dcf_files)

        assert len(ordered) == 2, "Missing files path after ordering"
        assert ordered[0] == Path("3D_L0900.JPG"), "Files weren't ordered by dcf number"
        assert ordered[1] == Path("3D_L0938.JPG"), "Files weren't ordered by dcf number"

    def test__extract_file_names_param_ok(self):
        fetcher = object.__new__(CameraImageFetcher)
        fetcher._extract_file_names_param(Path("DCIM/101S3D_L/3D_L0000.JPG"))

        assert fetcher._f_prefix == "3D_L", "Image prefix file not correctly extracted"
        assert fetcher._f_digit_len == 4, "Image index digit lenght not correctly extracted"
        assert fetcher._f_ext == ".JPG", "Image extension not correctly extracted"

    def test__make_dcf_pic_filename_ok(self):
        fetcher = object.__new__(CameraImageFetcher)
        fetcher._f_prefix = "3D_L"
        fetcher._f_digit_len = 4
        fetcher._f_ext = ".JPG"
        name = fetcher._make_dcf_pic_filename(index=10)

        assert name == "3D_L0010.JPG", "File names formatting is wrong"

    @patch("opv_import.services.CameraImageFetcher._order_dcf_files")
    @patch("opv_import.services.CameraImageFetcher._make_dcf_pic_filename")
    @patch("path.Path.exists", autospec=True)
    def test___fetch_pic_files_from_dcf_dir(self, mock_path_exists, mock_name, mock_order_file):
        dcf_dir = Path("DCIM/101S3D_L/")
        files = [
            Path("DCIM/101S3D_L/3D_L0000.JPG"),
            Path("DCIM/101S3D_L/3D_L0001.JPG"),
            Path("DCIM/101S3D_L/3D_L0010.JPG"),  # should not be returned
            Path("DCIM/101S3D_L/3D_L0100.JPG"),
            Path("DCIM/101S3D_L/3D_L0101.JPG")]
        dcf_dir.files = MagicMock()
        dcf_dir.files.return_value = files

        def exists(p):
            return p in files

        def make_name_mocked(index):
            return Path("3D_L{}.JPG".format(str(index).zfill(4)))

        mock_order_file.return_value = files
        mock_name.side_effect = make_name_mocked
        mock_path_exists.side_effect = exists

        fetcher = object.__new__(CameraImageFetcher)   # dcim_folder="DCIM"
        fetcher.logger = MagicMock()
        next_index, images = fetcher._fetch_pic_files_from_dcf_dir(dcf_dir=dcf_dir, start_index=100)

        assert dcf_dir.files.call_count == 1, "Files were listed more than once"
        assert mock_order_file.call_count == 1, "Files weren't ordered by index"

        expected_camimg = [
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0100.JPG")),
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0101.JPG")),
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0000.JPG")),
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0001.JPG"))
        ]

        assert next_index == 2, "Wrong next index for search"
        assert len(images) == 4, "Should find 4 images"
        assert images == expected_camimg, "Wrong result in file order"

    @patch("opv_import.services.CameraImageFetcher._make_dcf_pic_filename")
    @patch("path.Path.exists", autospec=True)
    def test__check_serie_continue_in_folder_ok(self, mock_path_exists, mock_name):
        files = [
            Path("DCIM/101S3D_L/3D_L0100.JPG")]

        def make_name_mocked(index):
            return Path("3D_L{}.JPG".format(str(index).zfill(4)))

        def exists(p):
            return p in files

        mock_name.side_effect = make_name_mocked
        mock_path_exists.side_effect = exists

        fetcher = object.__new__(CameraImageFetcher)
        r = fetcher._check_serie_continue_in_folder(next_index=100, next_dcf_folder_path=Path("DCIM/101S3D_L/"))
        assert r, "Serie should continue"

    @patch("opv_import.services.CameraImageFetcher._make_dcf_pic_filename")
    @patch("path.Path.exists", autospec=True)
    def test__check_serie_continue_in_folder_fail(self, mock_path_exists, mock_name):
        files = [
            Path("DCIM/101S3D_L/3D_L0099.JPG"),
            Path("DCIM/101S3D_L/3D_L0100.JPG")]

        def make_name_mocked(index):
            return Path("3D_L{}.JPG".format(str(index).zfill(4)))

        def exists(p):
            return p in files

        mock_name.side_effect = make_name_mocked
        mock_path_exists.side_effect = exists

        fetcher = object.__new__(CameraImageFetcher)
        r = fetcher._check_serie_continue_in_folder(next_index=100, next_dcf_folder_path=Path("DCIM/101S3D_L/"))
        assert not r, "Serie should not continue (conflicting case)"

    @patch("opv_import.services.CameraImageFetcher._order_dcf_dir")
    @patch("opv_import.services.CameraImageFetcher._check_serie_continue_in_folder")
    @patch("opv_import.services.CameraImageFetcher._fetch_pic_files_from_dcf_dir")
    def test_fetch_images(self, mock_fetch_dir, mock_serie_check, mock_ordered_dir):
        dirs = [
            Path("DCIM/100S3D_L/"),
            Path("DCIM/101S3D_L/")]
        dir_a_files = [
            CameraImage(path=Path("DCIM/100S3D_L/3D_L0001.JPG")),
            CameraImage(path=Path("DCIM/100S3D_L/3D_L0002.JPG"))]
        dir_b_files = [
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0003.JPG")),
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0004.JPG")),
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0000.JPG"))]

        def fetch_dir(dcf_dir, start_index):
            if dcf_dir == Path("DCIM/100S3D_L/"):
                return (3, dir_a_files)
            if dcf_dir == Path("DCIM/101S3D_L/"):
                return (1, dir_b_files)
            return (1, [])

        mock_fetch_dir.side_effect = fetch_dir
        fetcher = object.__new__(CameraImageFetcher)
        fetcher.dcim_folder = MagicMock()
        fetcher.logger = MagicMock()

        mock_ordered_dir.return_value = dirs
        mock_serie_check.return_value = True

        res_img_cam = fetcher.fetch_images()
        expected_img_cam = [
            CameraImage(path=Path("DCIM/100S3D_L/3D_L0001.JPG")),
            CameraImage(path=Path("DCIM/100S3D_L/3D_L0002.JPG")),
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0003.JPG")),
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0004.JPG")),
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0000.JPG"))
        ]

        fetch_dcf_calls = [
            call(dcf_dir=Path("DCIM/100S3D_L/"), start_index=1),
            call(dcf_dir=Path("DCIM/101S3D_L/"), start_index=3)]

        assert mock_ordered_dir.called, "Dir weren't ordered"
        assert mock_serie_check.call_args_list == [call(next_index=3, next_dcf_folder_path=Path("DCIM/101S3D_L/"))], "Check serie wasn't called"

        assert mock_fetch_dir.call_args_list == fetch_dcf_calls, "DCF fetch not called correctly"
        assert res_img_cam == expected_img_cam, "Fetcher isn't fetch images in correct order"

    @patch("opv_import.services.CameraImageFetcher.fetch_images")
    def test_get_images(self, mock_fetch_images):
        mock_fetch_images.return_value = [CameraImage(path=Path("DCIM/101S3D_L/3D_L0003.JPG"))]

        fetcher = object.__new__(CameraImageFetcher)
        fetcher._cache_camimg = None
        r = fetcher.get_images()

        fetcher.get_images()

        assert mock_fetch_images.call_count == 1, "Not lazy fetch called too much times"
        assert r == mock_fetch_images.return_value, "Result is incorrect"

    @pytest.fixture
    def test_dir_env(self, request):
        dir_a_files = [
            Path("DCIM/100S3D_L/3D_L0001.JPG"),
            Path("DCIM/100S3D_L/3D_L0002.JPG")
        ]
        dir_b_files = [
            Path("DCIM/101S3D_L/3D_L0003.JPG"),
            Path("DCIM/101S3D_L/3D_L0004.JPG"),
            Path("DCIM/101S3D_L/3D_L0000.JPG")
        ]

        files_path = []
        files_path.extend(dir_a_files)
        files_path.extend(dir_b_files)

        dir_env = [
            (Path("DCIM/"), [], [Path("DCIM/100S3D_L"), Path("DCIM/101S3D_L")]),
            (Path("DCIM/100S3D_L"), dir_a_files, []),
            (Path("DCIM/101S3D_L"), dir_b_files, [])
        ]

        request.addfinalizer(self.stop_fake_env)
        print("test_dir_env")
        return self.start_fake_env(dir_env)

    @patch("logging.getLogger")
    def test_fetchImages_all_inte(self, mock_logger, test_dir_env):
        fetcher = CameraImageFetcher(dcim_folder=Path("DCIM/"))
        res_cam = fetcher.fetch_images()
        expected_cam = [
            CameraImage(path=Path("DCIM/100S3D_L/3D_L0001.JPG")),
            CameraImage(path=Path("DCIM/100S3D_L/3D_L0002.JPG")),
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0003.JPG")),
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0004.JPG")),
            CameraImage(path=Path("DCIM/101S3D_L/3D_L0000.JPG"))
        ]

        assert self.fake_env_patcher_mocks['dirs'].called, "Directories weren't fetch"
        assert res_cam == expected_cam, "Something went wrong"

    @patch("logging.getLogger")
    def test_get_pic(self, mock_logger, test_dir_env):
        fetcher = CameraImageFetcher(dcim_folder=Path("DCIM/"))
        assert fetcher.get_pic(index=1) == CameraImage(path=Path("DCIM/100S3D_L/3D_L0002.JPG"))
        assert fetcher.get_pic(index=30) is None

    @patch("logging.getLogger")
    def test_nb_pic(self, mock_logger, test_dir_env):
        fetcher = CameraImageFetcher(dcim_folder=Path("DCIM/"))
        assert fetcher.nb_pic() == 5, "Wrong number of pictures"

    @patch("logging.getLogger")
    def test_get_first(self, mock_logger, test_dir_env):
        fetcher = CameraImageFetcher(dcim_folder=Path("DCIM/"))
        assert fetcher.get_first() == CameraImage(path=Path("DCIM/100S3D_L/3D_L0001.JPG"))

    @patch("logging.getLogger")
    def test_get_last(self, mock_logger, test_dir_env):
        fetcher = CameraImageFetcher(dcim_folder=Path("DCIM/"))
        assert fetcher.get_last() == CameraImage(path=Path("DCIM/101S3D_L/3D_L0000.JPG"))
