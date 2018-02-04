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
# Description: Lot Maker, takes CSV en pictures and manage them to get coherent set of datas.

from path import Path
from typing import List, Iterator
from collections import namedtuple
from opv_import import OpvImportError
from opv_import.makelot import ImageSet, CameraImageFetcher, indexes_walk

TIME_MARGING = 2  # max time difference accepted in picture exif metadata
CAM_DCIM_PATH = "APN{}/DCIM"
REF_SEARCH_NB_LOT_GENERATED = 30  # default number lot generated for camera set reference search
REF_SEARCH_MAX_INCOMPLET_CONSECUTIVE_SET = 7  # Maximum number of accepted consecutive incomplete sets during reference search
REF_SEARCH_MAX_INCOMPLET_SETS = 10  # Maximum total number of incomplete sets during reference search

SearchedRefImgSet = namedtuple('SearchedReferenceImgSet', ['ref_set', 'first_img_sets', 'img_set_generator'])

class LotMaker:

    def __init__(self, rederbro_csv_path: Path, pictures_path: Path, nb_cams: int = 6):
        """
        Init a lot maker with rederbro CSV and pictures path.

        :param rederbro_csv_path: Location of the rederbro CSV file.
        :type rederbro_csv_path: Path
        :param pictures_path: Location of the folder containing each APNx/DCMI
                              folders.
        :type pictures_path: Path
        :param nb_cams: Number of cameras, default is 6 (rederbro backpack).
        :type nb_cams: int
        """
        self.rederbro_csv_path = rederbro_csv_path
        self.pictures_path = pictures_path
        self.nb_cams = nb_cams
        self.fetchers = None
        self.rederbrometa = None

    def load_cam_images(self) -> List[CameraImageFetcher]:
        """
        Load camera images from pictures_path/APNxx/DCIM. Using camera fetcher.
        Lazy only start camera image fetchers once and fetch the images.
        """
        if self.fetchers is not None:
            return self.fetchers

        self.fetchers = []
        for no in range(0, self.nb_cams):
            fetcher = CameraImageFetcher(dcim_folder=self.pictures_path / CAM_DCIM_PATH.format(no))
            fetcher.fetch_images()
            self.fetchers.append(fetcher)

        return self.fetchers

    def get_images(self, indexes: List[int]) -> ImageSet:
        """
        Make an set of picture from indexes (for each camera).

        :param indexes: Indexes of pictures from each camera.
            For instance [0,1], will get first picture of first cam and second of second camera.
        :return: An image set of wanted pictures from each camera.
        :rtype: ImageSet
        """
        self.load_cam_images()

        return ImageSet(
            l={
                apn_no:
                    self.fetchers[apn_no].get_pic(index=indexes[apn_no])
                    for apn_no in range(0, self.nb_cams)
                    if apn_no < len(indexes) and indexes[apn_no] < self.fetchers[apn_no].nb_pic()
            },
            number_of_pictures=self.nb_cams)

    def cam_lot_generator(self, reference_set: ImageSet) -> Iterator[ImageSet]:
        """
        Generate all lot (event incomplete).

        :param reference_set: Reference set used to level ts and generate image sets.
        :type reference_set: ImageSet
        :return: An Iterator of the generated images sets.
        :rtype: Iterator[ImageSet]
        """
        if len(reference_set) < self.nb_cams:
            raise InvalidReferenceSetError()

        ref_ts = {apn_no: reference_set[apn_no].get_timestamp() for apn_no in range(0, self.nb_cams)}
        n_i = [0] * self.nb_cams   # next indexes Start at the begining (oldest images)
        last_indexes = [max(f.nb_pic() - 1, 0) for f in self.fetchers]

        while n_i <= last_indexes:
            # compute leveled ts DONE
            # list cam in accepted zone
            # compute new next_indexes
            cam_img = self.get_images(n_i)
            leveled_ts = {apn_no: img.get_timestamp() - ref_ts[apn_no] for apn_no, img in cam_img.items()}
            oldest_leveled_ts = min(leveled_ts.values())
            cam_no_in_acceptance = [apn_no for apn_no, lvl_ts in leveled_ts.items() if abs(lvl_ts - oldest_leveled_ts) < TIME_MARGING]

            # increment consumed indexes
            img_set = ImageSet(l={}, number_of_pictures=self.nb_cams)
            for apn_no in range(0, self.nb_cams):
                if apn_no in cam_no_in_acceptance:
                    img_set[apn_no] = cam_img[apn_no]
                    n_i[apn_no] += 1

            yield img_set

    def make_gopro_lot(self, reference_set: ImageSet) -> List[ImageSet]:
        """
        Generate sets of images based on a reference set.
        """
        gopro_lot = []
        for img_set in self.cam_lot_generator(reference_set=reference_set):
            if img_set.is_complete():
                gopro_lot.append(img_set)
        return gopro_lot

    def is_equiv_ref(self, set_a: ImageSet, set_b: ImageSet) -> bool:
        """
        Check if 2 set could be equivalent if used as reference set.

        :param set_a: First seta.
        :type set_a: ImageSet
        :param set_b: Second set.
        :type set_b: ImageSet
        :return: True if set refers to same times intervals.
        :rtype: bool
        """
        # considering set_a as reference set and checking set_b is coherent to set_a/ref set
        leveled_ts = {apn_no: set_b[apn_no].get_timestamp() - set_a[apn_no].get_timestamp() for apn_no in range(0, self.nb_cams)}
        oldest_leveled_ts = min(leveled_ts.values())
        cam_no_in_acceptance = [apn_no for apn_no, lvl_ts in leveled_ts.items() if abs(lvl_ts - oldest_leveled_ts) < TIME_MARGING]

        return len(cam_no_in_acceptance) == self.nb_cams

    def find_cam_img_set_ref(
            self,
            lot_count_for_test: int=REF_SEARCH_NB_LOT_GENERATED,
            max_incomplete_sets: int=REF_SEARCH_MAX_INCOMPLET_SETS,
            max_consecutive_incomplete_sets: int=REF_SEARCH_MAX_INCOMPLET_CONSECUTIVE_SET) -> Iterator[SearchedRefImgSet]:  # TODO test
        """
        Test all possible reference set and return the one getting the best number of sets.

        :param lot_count_for_test: Number of lot generated for each reference when testing.
        :type lot_count_for_test: int
        :param max_incomplete_sets: Allowed max incomplete sets in the first (lot_count_for_test) generated.
        :type max_incomplete_sets: int
        :param max_consecutive_incomplete_sets: Allowed max consecutive incomplete sets in the first (lot_count_for_test) generated.
        :type max_consecutive_incomplete_sets: int
        :return: Supposed valid reference set with the first images sets generated and the generator, so that user can continue.
        :rtype: Iterator[SearchedRefImgSet]
        """
        cam_max_indexes = [f.nb_pic() - 1 for f in self.fetchers]
        tested_set = []

        for cam_indexes in indexes_walk(nb_cams=self.nb_cams, cam_max_indexes=cam_max_indexes):
            cam_set = self.get_images(cam_indexes)
            print('cam_set')
            print(cam_set)

            # check it's not a similar indexes to what we already tested
            for s in tested_set:
                if self.is_equiv_ref(s, cam_set):
                    continue

            # Test cam_set as reference set
            incomplete_sets_count = 0
            incomplete_consecutive_sets_count = 0
            reject = False
            gp_sets = []
            set_count = 0
            img_set_generator = self.cam_lot_generator(reference_set=cam_set)
            for gen_img_set in img_set_generator:
                set_count += 1
                gp_sets.append(gen_img_set)
                if gen_img_set.is_complete():
                    incomplete_consecutive_sets_count = 0
                else:
                    incomplete_sets_count += 1
                    incomplete_consecutive_sets_count += 1

                # rejection or stop conditions
                if (incomplete_sets_count > max_incomplete_sets or
                        incomplete_consecutive_sets_count > max_consecutive_incomplete_sets):
                    reject = True
                    print("incomplete_sets_count")
                    print(incomplete_sets_count)
                    print("incomplete_consecutive_sets_count")
                    print(incomplete_consecutive_sets_count)
                    print("exit A")
                    break
                if set_count >= lot_count_for_test:
                    print("incomplete_sets_count")
                    print(incomplete_sets_count)
                    print("incomplete_consecutive_sets_count")
                    print(incomplete_consecutive_sets_count)
                    print("exit B")
                    break

            tested_set.append(cam_set)
            if not reject:
                yield SearchedRefImgSet(ref_set=cam_set, first_img_sets=gp_sets, img_set_generator=img_set_generator)


class InvalidReferenceSetError(OpvImportError):
    pass
