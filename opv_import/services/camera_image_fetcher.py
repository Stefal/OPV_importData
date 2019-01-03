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
# Description: Fetch images in correct order from a camera folder DCIM.
#              Based on standards DCF (Design rule for Camera File system) for fetching order.
#              DCF rules are a bit customized as GoPro camera doesn't follow them strictly, should not impact other cameras

import logging
import os
from path import Path
from typing import List
from opv_import.model import CameraImage
from opv_import.model import OpvImportError
from opv_import.helpers import pictures_utils

DCF_FILE_ALPHADIGIT_LEN = 4  # according to DCF specification DCF files have 4 alphadigit at the begining
DCF_FOLDERS_DIGIT_LEN = 3    # according to DCF specification DCF directories (DCMI subdirectories) have 3 digit at the begining

GORPRO_IMG_START_INDEX = 1   # GoPro start index for DCF/images files

class CameraImageFetcher:

    def __init__(self, dcim_folder: Path, img_start_index: int = GORPRO_IMG_START_INDEX):
        """
        Initialize a CameraImageFetcher.

        :param dcim_folder: Path of the camera DCIM folder.
        :type dcim_folder: Path
        """
        self.dcim_folder = dcim_folder
        self._img_start_index = img_start_index
        self._cache_camimg = None

        self._extract_file_names_param()  # extract prefix, ext, digit len used after

        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def _order_dcf_dir(self, dcf_dirs: List[Path]) -> List[Path]:
        """
        Order a list of standards DCF (Design rule for Camera File system) named directories.

        :param dcf_dirs: List of path to DFC_directories.
        :type dcf_dirs: List[Path]
        :return: Ordered list of Path.
        :rtype: List[Path]
        """
        # According to the DCF specification DCMI subdirectories names begin by 3 digits and should be incremental
        # we use these digits to order the folders
        return sorted(dcf_dirs, key=lambda path: int(Path(path).basename()[0:DCF_FOLDERS_DIGIT_LEN]))

    def _order_dcf_files(self, dcf_files: List[Path]) -> List[Path]:
        """
        Order a list of standards DCF (Design rule for Camera File system) named directories.

        :param dcf_dirs: List of path to DFC_directories.
        :type dcf_dirs: List[Path]
        :return: Ordered list of files path.
        :rtype: List[Path]
        """
        # According to the DCF specification DCF files names begin by 4 alpha digit followed by there id (digits)
        # we use these digits to order the files
        return sorted(dcf_files, key=lambda path: int(Path(path).namebase[DCF_FILE_ALPHADIGIT_LEN:]))

    def _extract_file_names_param(self, pic_path: Path = None):
        """
        Extract file prefix, digit_len and extension.

        :param pic_path: Path to a picture file.
        :type pic_path: Path
        """

        # basing naming on the first file of the first dcf (sub DCIM ) folder
        if pic_path is None:
            dirs = self.dcim_folder.dirs()

            if len(dirs) == 0:
                raise MissingDcfFolderError()
            files = dirs[0].files()
            if len(files) == 0:
                raise MissingPictureFileError()

            pic_path = files[0]

        self._f_prefix = pic_path.namebase[0:DCF_FILE_ALPHADIGIT_LEN]  # the prefix of jpg files, for instance "3D_L" for "3D_L0000.JPG"
        self._f_digit_len = len(pic_path.namebase) - DCF_FILE_ALPHADIGIT_LEN
        # the len of the index part in the name, for instance 4 for "3D_L0000.JPG"
        self._f_ext = pic_path.ext

    def _make_dcf_pic_filename(self, index: int):
        """
        Return a picture filname based on the current DCF name formatting.

        :param index: File index.
        :type index: int
        :return: A DCF filename.
        :rtype: str
        """
        return self._f_prefix + str(index).zfill(self._f_digit_len) + self._f_ext

    def _fetch_pic_files_from_dcf_dir(
            self, dcf_dir: Path, start_index: GORPRO_IMG_START_INDEX = int) -> (int, List[CameraImage]):
        """
        Get pictures in a DCIM folder from a start index using DCF standard name convention.

        :param dcf_dir: Should be a directory which is under the DCIM directory (full path).
        :type dcf_dir: Path
        :param start_index: Index of the picture we will start at. Might not be 0 if we are continuing a serie from an other folder.
        :type start_index: int
        :return: The next index (to continue a serie in the next folder), the list of ordered CameraImage.
        :rtype: (next_index, pic_list)
        """
        files = self._order_dcf_files(dcf_dir.files())
        pic_files = []    # Files that should be returned in the correct order
        next_index = start_index

        if len(files) == 0:  # No files nothing to do
            return (next_index, [])

        start_at_first_pic_index = self._make_dcf_pic_filename(index=next_index) == files[0].basename()
        while len(files) > 0:  # since all files aren't treated

            next_file = dcf_dir / self._make_dcf_pic_filename(index=next_index)

            while next_file.exists():
                pic_files.append(CameraImage(path=next_file))
                files.remove(next_file)
                next_index += 1
                next_file = dcf_dir / self._make_dcf_pic_filename(index=next_index)

            self.logger.debug("This file {} doesn't exists".format(next_file))

            if len(files):  # some files still need to be added
                if not start_at_first_pic_index:   # we didn't start with the lower index in the current directory
                    next_index = int(files[0].namebase[DCF_FILE_ALPHADIGIT_LEN:])  # starting over a new serie using the lower index in directory
                    start_at_first_pic_index = True
                    self.logger.debug("Some files missing resseting index to {} ".format(str(next_index)))
                    continue
                else:  # break in file indexing serie, shouldn't happened, will not treat orther files
                    self.logger.error("Some files weren't added are they aren't part of the lower serie in the DCF directory :")
                    self.logger.error("Latest added file is {} but file {} doesn't exists.".format(pic_files[-1], next_file))
                    files = []

        return (next_index, pic_files)

    def _check_serie_continue_in_folder(self, next_index: int, next_dcf_folder_path: Path):
        """
        Check a serie started folder continues in next_dcf_folder.
        That mean's a file with next_index is in next_dcf_folder but there isn't next_index - 1 in it.
        Continution of the serie of a previous folder by not part of a serie starting in next_dcf_folder.

        :param next_index: Next index in the current serie.
        :type next_index: int
        :param next_dcf_folder: Folder where the serie might continue.
        :type next_dcf_folder: Path
        :return: True if the serie continu in the folder and isn't part of a new serie of that folder.
        :rtype: Boolean
        """
        next_file = next_dcf_folder_path / self._make_dcf_pic_filename(index=next_index)
        prev_file = next_dcf_folder_path / self._make_dcf_pic_filename(index=next_index - 1)

        return next_file.exists() and not prev_file.exists()

    def fetch_images(self) -> List[CameraImage]:
        """
        Return a list of pictures ordered by their timestamp

        :param dcim_folder: Path to dcmi folder.
        :return: ordered list of pictures path.
        """
        
        self.logger.debug(" Searching for jpeg images in ")
        self.logger.debug(self.dcim_folder)

        file_list = []
        for root, sub_folders, files in os.walk(self.dcim_folder):
            file_list += [os.path.join(root, filename) for filename in files if filename.lower().endswith(".jpg")]

        files = []
        # get DateTimeOriginal data from the images and sort the list by timestamp
        for filepath in file_list:
            #print(filepath)
            #metadata = EXIFRead(filepath)
            
            try:
                timestamp = pictures_utils.read_exif_time(filepath)
                
                files.append((filepath, timestamp))
                # print t
                # print type(t)
            except KeyError as e:
                # if any of the required tags are not set the image is not added to the list
                print("Skipping {0}: {1}".format(filepath, e))

        files.sort(key=lambda file: file[1])
        # print_list(files)
        
        pic_files = [CameraImage(pic[0]) for pic in files]

        return pic_files

    def get_images(self) -> List[CameraImage]:
        """
        Returns fetch images if they are already fetched get it from cache.
        Otherwise fetch same and save them to a cache.

        :return: Ordered by gopro order list of camera images.
        :rtype: List[CameraImage]
        """
        if self._cache_camimg is None:
            self._cache_camimg = self.fetch_images()

        return self._cache_camimg

    def get_pic(self, index: int) -> CameraImage:
        """
        Return picture at a specific index.

        :param index: 0 for first (oldest) picture, -1 for lastest (newest) picture
        :type index: int
        :return: a camera image, None if index doesn't exists
        :rtype: CameraImage
        """
        img = self.get_images()
        return img[index] if index < len(img) else None

    def nb_pic(self) -> int:
        """
        Returns the number of pictures.

        :return: number of pictures
        :rtype: int
        """
        return len(self.get_images())

    def get_first(self) -> CameraImage:
        """
        Return first CameraImage, if it exists.

        :return: First camera picture.
        :rtype: CameraImage
        """
        return self.get_pic(index=0)

    def get_last(self) -> CameraImage:
        """
        Return last CameraImage, if it exists.

        :return: Last camera picture.
        :rtype: CameraImage
        """
        return self.get_pic(index=-1)

class MissingDcfFolderError(OpvImportError):
    """ Raised when they is no DCF folder inside DCIM folder """
    pass

class MissingPictureFileError(OpvImportError):
    """ Raise when there is no picture file inside DCF folder """
    pass
