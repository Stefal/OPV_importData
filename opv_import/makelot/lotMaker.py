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
from typing import List, Iterator, Dict, Tuple, NamedTuple
from collections import namedtuple
from opv_import import OpvImportError
from opv_import.makelot import ImageSet, CameraImageFetcher, indexes_walk, RederbroMeta, MetaCsvParser, Lot, CameraImage

import datetime
def dt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

TIME_MARGING = 3  # max time difference accepted in picture exif metadata
CAM_DCIM_PATH = "APN{}/DCIM"
REF_SEARCH_NB_LOT_GENERATED = 30  # default number lot generated for camera set reference search
REF_SEARCH_MAX_INCOMPLET_CONSECUTIVE_SET = 7  # Maximum number of accepted consecutive incomplete sets during reference search
REF_SEARCH_MAX_INCOMPLET_SETS = 10  # Maximum total number of incomplete sets during reference search

THRESHOLD_MAX_CONSECUTIVE_INCOMPLETE_SETS = 10
THRESHOLD_WINDOW_SIZE = 10
THRESHOLD_WINDOW_MAX_ERRORS = 6
SUCCESS_WINDOW_SIZE_NEXT_PARTITION_START_SAVING_POINT = 10

# TODO convert all to typed NamedTuple
SearchedRefImgSet = namedtuple('SearchedReferenceImgSet', ['ref_set', 'first_img_sets', 'img_set_generator'])
SearchRefMeta = namedtuple('SearchRefMeta', ['index_meta', 'index_cam_set'])
CameraSetPartition = NamedTuple('CameraSetPartition', [
    ('ref_set', ImageSet),
    ('images_sets', List[ImageSet]),
    ('start_indexes', List[int]),
    ('fetcher_next_indexes', List[int]),
    ('break_reason', str),
    ('number_of_incomplete_sets', int),
    ('number_of_complete_sets', int),
    ('max_consecutive_incomplete_sets', int)])
ImageSetWithFetcherIndexes = NamedTuple('ImageSetWithFetcherIndexes', [('fetcher_next_indexes', List[int]), ('set', ImageSet)])

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

    def cam_set_generator(self, reference_set: ImageSet, start_indexes: List[int]=None) -> Iterator[ImageSetWithFetcherIndexes]:
        """
        Generate all lot (event incomplete).

        :param reference_set: Reference set used to level ts and generate image sets.
        :type reference_set: ImageSet
        :param start_indexes: Start with this list of indexes, will ignore images before.
        :type start_indexes: List[int]
        :return: An Iterator of the generated images sets.
        :rtype: Iterator[ImageSet]
        """
        if len(reference_set) < self.nb_cams:
            raise InvalidReferenceSetError()

        ref_ts = {apn_no: reference_set[apn_no].get_timestamp() for apn_no in range(0, self.nb_cams)}
        print("ref_ts : ", ref_ts)
        last_indexes = [max(f.nb_pic() - 1, 0) for f in self.fetchers]

        n_i = start_indexes if start_indexes is not None else [0] * self.nb_cams   # next indexes Start at the begining (oldest images)

        cam_img = None  # init for last cam images (back in time issue)

        while n_i <= last_indexes:
            # compute leveled ts DONE
            # list cam in accepted zone
            # compute new next_indexes

            last_cam = cam_img
            cam_img = self.get_images(n_i)

            # detecting back in time issu with cameras timestamp
            if last_cam is not None:
                back_in_time_apns = cam_img.get_pic_taken_before(img_set=last_cam)
                if back_in_time_apns != []:
                    print(back_in_time_apns)
                    pic_path = {apnid: (last_cam[apnid], cam_img[apnid]) for apnid in back_in_time_apns}
                    raise CameraBackInTimeError(indexes=n_i, pictures_paths=pic_path)  # TODO unit test it

            leveled_ts = {apn_no: img.get_timestamp() - ref_ts[apn_no] for apn_no, img in cam_img.items()}
            print("leveled_ts : ", leveled_ts)
            oldest_leveled_ts = min(leveled_ts.values())
            cam_no_in_acceptance = [apn_no for apn_no, lvl_ts in leveled_ts.items() if abs(lvl_ts - oldest_leveled_ts) < TIME_MARGING]
            print("cam_no_in_acceptance : ", cam_no_in_acceptance)

            # increment consumed indexes
            img_set = ImageSet(l={}, number_of_pictures=self.nb_cams)
            for apn_no in range(0, self.nb_cams):
                if apn_no in cam_no_in_acceptance:
                    img_set[apn_no] = cam_img[apn_no]
                    n_i[apn_no] += 1

            yield ImageSetWithFetcherIndexes(set=img_set, fetcher_next_indexes=n_i)

    def make_gopro_lot(self, reference_set: ImageSet) -> List[ImageSet]:   # TODO change it top handle partitionment (back in time)
        """
        Generate sets of images based on a reference set.

        :param reference_set: Reference set used to generate images sets.
        :type reference_set: ImageSet
        :return: List of generate images sets, only complete ones.
        :rtype: List[ImageSet]
        """
        gopro_lot = []
        for img_set_with_fetchers_indexes in self.cam_set_generator(reference_set=reference_set):
            img_set = img_set_with_fetchers_indexes.set
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
            input()

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
            img_set_generator = self.cam_set_generator(reference_set=cam_set)
            for gen_img_set_with_fetcher_indexes in img_set_generator:
                gen_img_set = gen_img_set_with_fetcher_indexes.set
                set_count += 1
                gp_sets.append(gen_img_set)
                print(gen_img_set)
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
                    input()
                    break
                if set_count >= lot_count_for_test:
                    print("incomplete_sets_count")
                    print(incomplete_sets_count)
                    print("incomplete_consecutive_sets_count")
                    print(incomplete_consecutive_sets_count)
                    print("exit B")
                    input()
                    break

            tested_set.append(cam_set)
            if not reject:
                yield SearchedRefImgSet(ref_set=cam_set, first_img_sets=gp_sets, img_set_generator=img_set_generator)

    def make_gopro_set_new(
            self,
            threshold_max_consecutive_incomplete_sets: int=THRESHOLD_MAX_CONSECUTIVE_INCOMPLETE_SETS,
            threshold_incomplete_set_window_size: int=THRESHOLD_WINDOW_SIZE,
            threshold_incomplete_set_max_in_window: int=THRESHOLD_WINDOW_MAX_ERRORS) -> List[ImageSet]:
        """
        TODO
        """
        gp_sets = []

        # partition while indexes aren't all consumed
        for p in self.generate_cam_partition(
                [0] * self.nb_cams,
                threshold_max_consecutive_incomplete_sets,
                threshold_incomplete_set_window_size,
                threshold_incomplete_set_max_in_window):

            gp_sets.extend(p.images_sets)

        return gp_sets

    def generate_cam_partition(
            self,
            partition_start,
            threshold_max_consecutive_incomplete_sets: int=THRESHOLD_MAX_CONSECUTIVE_INCOMPLETE_SETS,
            threshold_incomplete_set_window_size: int=THRESHOLD_WINDOW_SIZE,
            threshold_incomplete_set_max_in_window: int=THRESHOLD_WINDOW_MAX_ERRORS) -> CameraSetPartition:
        """
        """
        # test/search reference cycle
        cam_max_indexes = [f.nb_pic() - 1 for f in self.fetchers]
        tested_set = []
        break_reason = "NORMAL"   # change it with constant
        fetcher_next_indexes = [0] * self.nb_cams

        indexe_gen = indexes_walk(nb_cams=self.nb_cams, cam_start_indexes=partition_start, cam_max_indexes=cam_max_indexes)
        for cam_indexes in indexe_gen:
            print("lm - cam_indexes: ", cam_indexes)
            cam_set = self.get_images(cam_indexes)
            print('cam_set')
            print(cam_set)

            # check it's not a similar indexes to what we already tested
            # for s in tested_set:
            #     if self.is_equiv_ref(s, cam_set):
            #         continue

            # Test cam_set as reference set
            incomplete_consecutive_sets_count = 0
            reject = False
            gp_sets = []
            gp_set_since_last_save = []
            break_reason = 'NORMAL'
            incomplete_set_count = 0
            complete_set_count = 0
            partition_start = list(fetcher_next_indexes)  # updating start
            img_set_generator = self.cam_set_generator(reference_set=cam_set, start_indexes=list(cam_indexes))
            max_consecutive_incomplete_sets = 0

            error_window = [0] * threshold_incomplete_set_window_size     # 1 when error, 0 when no errors
            success_window = [0] * SUCCESS_WINDOW_SIZE_NEXT_PARTITION_START_SAVING_POINT  # success window, use to save fetcher_indexes
            # so that we rollback at the right position

            gen_img_index = 0

            try:
                for gen_img_set_with_fetcher_indexes in img_set_generator:
                    gen_img_set = gen_img_set_with_fetcher_indexes.set
                    print("gen_img_set", gen_img_set)
                    gp_set_since_last_save.append(gen_img_set)
                    if gen_img_set.is_complete():
                        complete_set_count += 1
                        max_consecutive_incomplete_sets = max(max_consecutive_incomplete_sets, incomplete_consecutive_sets_count)
                        incomplete_consecutive_sets_count = 0
                    else:
                        incomplete_consecutive_sets_count += 1
                        incomplete_set_count += 1

                    error_window[gen_img_index % len(error_window)] = int(gen_img_set.is_complete())
                    success_window[gen_img_index % len(success_window)] = int(gen_img_set.is_complete())

                    # if sum(error_window) > threshold_incomplete_set_max_in_window:
                    #     reject = True
                    #     print("Thresold max consecutive incomplete sets")
                    #     print("error_window: ", error_window)
                    #     # import pdb; pdb.set_trace()

                    # rejection or stop conditions
                    if (incomplete_consecutive_sets_count > threshold_max_consecutive_incomplete_sets):
                        reject = True
                        print("incomplete_consecutive_sets_count")
                        print(incomplete_consecutive_sets_count)
                        print("exit A")

                        # if cam_indexes[0] > 820:
                        # import pdb; pdb.set_trace()

                        # input()
                        break

                    gen_img_index += 1
                    print("gen_img_set: ", gen_img_index)
                    print("reject: ", reject)
                    print("success_window: ", success_window)

                    if sum(success_window) == len(success_window):
                        print("---> Saving back point (fetcher_next_indexes)")
                        gp_sets.extend(gp_set_since_last_save)   # adding set to generated sets
                        gp_set_since_last_save = []   # clearing set since last save has we just save this point
                        fetcher_next_indexes = list(gen_img_set_with_fetcher_indexes.fetcher_next_indexes)
                        print("---> fetcher_next_indexes: ", fetcher_next_indexes)
            except CameraBackInTimeError as backintime_err:
                break_reason = "BACK IN TIME"
                print("backintime_err: ", backintime_err)
                fetcher_next_indexes = backintime_err.indexes  # Next indexes has this indexes weren't used to make an actual set

            tested_set.append(cam_set)
            print("fetcher_next_indexes: ", fetcher_next_indexes)
            print("partition_start: ", partition_start)
            if fetcher_next_indexes != partition_start:
                # generator should not suggest already used image, setting start indexes to the end of the partition
                print("indexe_gen.send")
                print(fetcher_next_indexes)
                indexe_gen.send(list(fetcher_next_indexes))  # copy list so that there are no reference issues

                # returning the generated partition
                yield CameraSetPartition(
                    ref_set=cam_set, images_sets=gp_sets,
                    start_indexes=partition_start, fetcher_next_indexes=fetcher_next_indexes,
                    break_reason=break_reason, number_of_incomplete_sets=incomplete_set_count,
                    number_of_complete_sets=complete_set_count,
                    max_consecutive_incomplete_sets=incomplete_consecutive_sets_count)

    def load_metas(self) -> List[RederbroMeta]:
        """
        Use parser and fetcher RederbroMeta.

        :return: RederbroMeta
        :rtype: List[RederbroMeta]
        """
        if self.rederbrometa is None:
            self.rederbrometa = MetaCsvParser(csv_path=self.rederbro_csv_path)

        return self.rederbrometa.get_metas()

    def match_metas(self, img_sets: List[ImageSet]):
        """
        Associate meta
        """

    # def find_meta_ref(self, img_sets: List[ImageSet]) -> SearchRefMeta:  # TODO : test it using PNEcrins J1/J2/J3
    #     EPSILON = 3
    #     metas = self.rederbrometa.get_metas()
    #     max_meta_index = len(metas)
    #     max_img_set_index = len(img_sets)
    #
    #     # testing different references
    #     for meta_cam_indexes in indexes_walk(nb_cams=2, cam_max_indexes=[max_meta_index, max_img_set_index]):
    #         meta_start = meta_cam_indexes[0]
    #         img_set_start = meta_cam_indexes[1]
    #         print("Testing with reference indexes : meta_start: ", meta_start, " | img_set_start: ", img_set_start)
    #         print("Start meta set :")
    #         print(metas[meta_start])
    #         print("Image start set")
    #         print(img_sets[img_set_start])
    #         print("--")
    #
    #         lots = []
    #
    #         last_index_meta = meta_start
    #         last_index_img = img_set_start
    #         next_index_meta = meta_start + 1
    #         next_index_img = img_set_start + 1
    #
    #         reject = False
    #
    #         # Generating lot for current reference
    #         while not reject and next_index_meta < max_meta_index and next_index_img < max_img_set_index:
    #             print("next_index_meta : ", next_index_meta, " | next_index_img : ", next_index_img)
    #             last_meta_was_errored = metas[last_index_meta].has_error()
    #
    #             diff_meta = metas[next_index_meta].timestamp - metas[last_index_meta].timestamp
    #             diff_cam = img_sets[next_index_img][0].get_timestamp() - img_sets[last_index_img][0].get_timestamp()
    #
    #             print("diff_cam - next date : ", dt(img_sets[next_index_img][0].get_timestamp()), " | last date : ", dt(img_sets[last_index_img][0].get_timestamp()))
    #
    #             print("diff_meta : ", diff_meta, " | diff_cam : ", diff_cam)
    #             # input()
    #
    #             if diff_meta < diff_cam and abs(diff_meta - diff_cam) > EPSILON:  # CSV entries have less difference than img_sets entries
    #                 if (
    #                     not metas[next_index_meta].has_error() and
    #                     not last_meta_was_errored and img_sets[next_index_img].is_complete()
    #                 ):
    #                     reject = True
    #             elif diff_meta > diff_cam and abs(diff_meta - diff_cam) > EPSILON:
    #                 reject = True
    #
    #             if reject:
    #                 print("REJECTED")
    #                 continue
    #
    #             if not reject:
    #                 lots.append(Lot(meta=metas[next_index_meta], cam_set=img_sets[last_index_img]))
    #                 last_index_meta = next_index_meta
    #                 last_index_img = next_index_img
    #                 next_index_meta += 1
    #                 next_index_img += 1
    #                 # make association and continue
    #                 # create a representation of both data
    #
    #         if not reject:
    #             print("!!!!!!!!!!!!!!!!!!! Got it !!!!!!!!!!!!!")
    #             return lots

class InvalidReferenceSetError(OpvImportError):
    pass

class CameraBackInTimeError(OpvImportError):

    def __init__(self, indexes: List[int]=None, pictures_paths: Dict[int, Tuple[CameraImage, CameraImage]]={}):
        """
        When back in time issue detected on at least 1 camera pictures.

        :param indexes: indexes where back in time where detected (back in time bewteen indexes[x]-1 and indexes).
        :type indexes: List[int]
        :param pictures_paths: Couple of pictures path that have the back in time issu for each affected camera.
                                Eg {0: (CamImg("APN0/picA.jpg", ts=10), CamImg("APN0/picB", ts=5))}
        :type pictures_paths: Dict[int, Tuple[CameraImage, CameraImage]
        """
        self.indexes = indexes
        self.pictures_paths = pictures_paths

        Exception.__init__(self, self.__repr__())

    def __repr__(self) -> str:
        return "Back in time at indexes {} between thoses pictures : {}".format(str(self.indexes), str(self.pictures_paths))
