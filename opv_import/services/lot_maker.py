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

import logging
import os
from path import Path
from opv_import.helpers import indexes_walk
from opv_import.services import CameraImageFetcher
from typing import List, Iterator, Dict, Tuple, NamedTuple
from opv_import.model import ImageSet, RederbroMeta, Lot, CameraImage, OpvImportError, CameraSetPartition, LotPartition
from opv_import.helpers import MetaCsvParser
from opv_import.config import APN_NUM_TO_APN_OUTPUT_DIR

import datetime
def dt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

TIME_MARGING = 3  # max time difference accepted in picture exif metadata
CAM_DCIM_PATHS = APN_NUM_TO_APN_OUTPUT_DIR
REF_SEARCH_NB_LOT_GENERATED = 30  # default number lot generated for camera set reference search
REF_SEARCH_MAX_INCOMPLET_CONSECUTIVE_SET = 7  # Maximum number of accepted consecutive incomplete sets during reference search
REF_SEARCH_MAX_INCOMPLET_SETS = 10  # Maximum total number of incomplete sets during reference search

THRESHOLD_MAX_CONSECUTIVE_INCOMPLETE_SETS = 10
THRESHOLD_WINDOW_SIZE = 10
THRESHOLD_WINDOW_MAX_ERRORS = 6
SUCCESS_WINDOW_SIZE_NEXT_PARTITION_START_SAVING_POINT = 10

ImageSetWithFetcherIndexes = NamedTuple('ImageSetWithFetcherIndexes', [('fetcher_next_indexes', List[int]), ('set', ImageSet)])
LotWithIndexes = NamedTuple('LotWithIndexes', [('next_meta_index', int), ('next_img_set_index', int), ('lot', Lot)])

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

        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

    def load_cam_images(self) -> List[CameraImageFetcher]:
        """
        Load camera images from pictures_path/APNxx/DCIM. Using camera fetcher.
        Lazy only start camera image fetchers once and fetch the images.
        """
        if self.fetchers is not None:
            return self.fetchers

        dir_list = self.pictures_path.dirs()
       
        # compare if there are n folders for n cams
        if len(CAM_DCIM_PATHS) != self.nb_cams:
            raise ValueError("You should have the same number of folder and cam number")
        
        self.fetchers = []
        import ipdb; ipdb.set_trace()
        for string in CAM_DCIM_PATHS:
            try:
                idx = [path.name.lower() for path in dir_list].index(string.lower())
                cam_pictures_path = dir_list[idx]
            except ValueError:
                print("I can't find folder with {0} in its name".format(string))
            fetcher = CameraImageFetcher(dcim_folder=cam_pictures_path) 
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
                    self.logger.warning("Detected back in time in cameras : %r", back_in_time_apns)
                    pic_path = {apnid: (last_cam[apnid], cam_img[apnid]) for apnid in back_in_time_apns}
                    raise CameraBackInTimeError(indexes=n_i, pictures_paths=pic_path)  # TODO unit test it

            leveled_ts = {apn_no: img.get_timestamp() - ref_ts[apn_no] for apn_no, img in cam_img.items()}
            oldest_leveled_ts = min(leveled_ts.values())
            cam_no_in_acceptance = [apn_no for apn_no, lvl_ts in leveled_ts.items() if abs(lvl_ts - oldest_leveled_ts) < TIME_MARGING]

            # increment consumed indexes
            img_set = ImageSet(l={}, number_of_pictures=self.nb_cams)
            for apn_no in range(0, self.nb_cams):
                if apn_no in cam_no_in_acceptance:
                    img_set[apn_no] = cam_img[apn_no]
                    n_i[apn_no] += 1

            yield ImageSetWithFetcherIndexes(set=img_set, fetcher_next_indexes=n_i)

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

    def make_gopro_set_new(
            self,
            threshold_max_consecutive_incomplete_sets: int=THRESHOLD_MAX_CONSECUTIVE_INCOMPLETE_SETS,
            threshold_incomplete_set_window_size: int=THRESHOLD_WINDOW_SIZE,
            threshold_incomplete_set_max_in_window: int=THRESHOLD_WINDOW_MAX_ERRORS) -> List[ImageSet]:
        """
        Make camera images sets (doesn't use metadata).

        :param threshold_max_consecutive_incomplete_sets: Set the max consecutive incomplete sets that will be accepted when searching the reference.
        :param threshold_incomplete_set_window_size: Set the size of the incomplete set window (error window).
        :param threshold_incomplete_set_max_in_window: Maximum number of incomplete set in the error window.
        :return: A list of generated ImageSet.
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
            partition_start: List[int],
            threshold_max_consecutive_incomplete_sets: int=THRESHOLD_MAX_CONSECUTIVE_INCOMPLETE_SETS,
            threshold_incomplete_set_window_size: int=THRESHOLD_WINDOW_SIZE,
            threshold_incomplete_set_max_in_window: int=THRESHOLD_WINDOW_MAX_ERRORS) -> CameraSetPartition:
        """
        Make camera images sets partitions (doesn't use metadata).

        :param partition_start: The begening indexes of the partition.
        :param threshold_max_consecutive_incomplete_sets: Set the max consecutive incomplete sets that will be accepted when searching the reference.
        :param threshold_incomplete_set_window_size: Set the size of the incomplete set window (error window).
        :param threshold_incomplete_set_max_in_window: Maximum number of incomplete set in the error window.
        :return: A CameraSetPartition.
        """
        self.logger.debug("generate_cam_partition : Start generating camera partitions")
        cam_max_indexes = [f.nb_pic() - 1 for f in self.fetchers]  # end indexes
        fetcher_next_indexes = [0] * self.nb_cams   # correspond to the begining of the next partition

        # for debug and tracking purposes
        id_set = 0

        indexe_gen = indexes_walk(nb_cams=self.nb_cams, cam_start_indexes=partition_start, cam_max_indexes=cam_max_indexes)
        for cam_indexes in indexe_gen:
            self.logger.debug("Camera current indexes are : %r", cam_indexes)
            cam_set = self.get_images(cam_indexes)
            self.logger.debug("Current reference set is : %r", cam_set)

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
                # Generating sets with the current reference
                for gen_img_set_with_fetcher_indexes in img_set_generator:
                    gen_img_set = gen_img_set_with_fetcher_indexes.set
                    self.logger.debug("Generated set : %r", gen_img_set)
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

                    # rejection or stop conditions
                    if (incomplete_consecutive_sets_count > threshold_max_consecutive_incomplete_sets):
                        self.logger.debug("Maximum incomplete set count reached, rejecting current reference %r ", cam_set)
                        break

                    gen_img_index += 1
                    self.logger.debug("Success window : %r", success_window)

                    if sum(success_window) == len(success_window):
                        gp_sets.extend(gp_set_since_last_save)   # adding set to generated sets
                        gp_set_since_last_save = []   # clearing set since last save has we just save this point
                        fetcher_next_indexes = list(gen_img_set_with_fetcher_indexes.fetcher_next_indexes)
                        self.logger.debug("Good success windows saving rollback point : fetcher_next_indexes = %r", fetcher_next_indexes)
            except CameraBackInTimeError as backintime_err:
                break_reason = "BACK IN TIME"
                fetcher_next_indexes = backintime_err.indexes  # Next indexes has this indexes weren't used to make an actual set
                self.logger.debug("Detected back in time error : fetcher_next_indexes = %r", fetcher_next_indexes)

            if fetcher_next_indexes != partition_start:
                # generator should not suggest already used image, setting start indexes to the end of the partition
                self.logger.debug("Indexes generator : fetcher_next_indexes = %r", fetcher_next_indexes)
                indexe_gen.send(list(fetcher_next_indexes))  # copy list so that there are no reference issues

                # for tracking and debug purposes
                for s in gp_sets:
                    s.id_set = id_set
                    id_set += 1

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
        self.logger.debug("Loading meta from file : %r", self.rederbrometa)
        if self.rederbrometa is None:
            self.rederbrometa = MetaCsvParser(csv_path=self.rederbro_csv_path)

        return self.rederbrometa.get_metas()

    def get_metas(self) -> List[RederbroMeta]:
        return self.load_metas()

    def associate_meta(self, reference_lot: Lot, img_sets: List[ImageSet], start_meta_index: int=0, start_img_set_index: int=0) -> Iterator[LotWithIndexes]:
        """
        Generate all lot (event incomplete).

        :param reference_lot: Reference valid lot used to generate the others.
        :param img_sets: Images sets use to generate lots.
        :param start_meta_index: Start meta index.
        :param start_img_set_index: Start image set.
        """
        self.logger.debug(
            "Associating meta with reference lot : %r, start meta indexes : %i, start img_set indexes : %i",
            reference_lot, start_meta_index, start_img_set_index)
        K_META = 0
        K_SET = 1
        rederbrometa = self.get_metas()

        # checking reference lot can be a valid reference
        if reference_lot.meta is None or reference_lot.cam_set is None or not(reference_lot.cam_set.is_complete()):
            raise InvalidReferenceLotError()

        # extracting timestamps
        ref_ts = {
            K_META: reference_lot.meta.get_timestamp(),
            K_SET: {k: reference_lot.cam_set[k].get_timestamp() for k in reference_lot.cam_set.keys()}
        }
        start_indexes = [start_meta_index, start_img_set_index]
        last_indexes = [max(len(rederbrometa) - 1, 0), max(len(img_sets) - 1, 0)]  # first is meta index, second img_set index

        n_i = start_indexes if start_indexes is not None else [0] * 2   # next indexes Start at the begining (oldest images)

        lot = None  # init for last cam images (back in time issue)

        while n_i <= last_indexes:
            # compute leveled ts DONE
            # list cam in accepted zone
            # compute new next_indexes

            if n_i[K_SET] >= len(img_sets):  # image set index is too high
                break

            last_lot = lot  # will be used to detect back in time issu

            lot = Lot(meta=rederbrometa[n_i[K_META]], cam_set=img_sets[n_i[K_SET]])

            # detecting back in time issu with cameras timestamp
            if last_lot is not None:
                back_in_time_apns = lot.cam_set.get_pic_taken_before(img_set=lot.cam_set)
                if back_in_time_apns != []:
                    self.logger.warning("Backintime detected for cameras : %r ", back_in_time_apns)
                    pic_path = {apnid: (last_lot.cam_set[apnid], lot.cam_set[apnid]) for apnid in back_in_time_apns}
                    raise CameraBackInTimeError(indexes=n_i, pictures_paths=pic_path)  # TODO unit test it
                if lot.meta.get_timestamp() < last_lot.meta.get_timestamp():
                    self.logger.warning("Back in time detected in Metas, between : %r | %r", lot.meta, last_lot.meta)
                    raise MetaBackInTimeError(indexes=n_i)

            apn_key = list(lot.cam_set.keys())[0]  # selecting an APN which is present in the current set to compare timestamp with reference
            leveled_ts = {K_META: lot.meta.get_timestamp() - ref_ts[K_META], K_SET: lot.cam_set[apn_key].get_timestamp() - ref_ts[K_SET][apn_key]}
            oldest_leveled_ts = min(leveled_ts.values())
            in_acceptance = [k for k, lvl_ts in leveled_ts.items() if abs(lvl_ts - oldest_leveled_ts) < 3]
            self.logger.debug("Keys in acceptance zone (%i is for meta and %i is for camera image set) : %r", K_META, K_SET, in_acceptance)

            # increment consumed indexes, those in acceptance zone
            if K_SET in in_acceptance and K_META in in_acceptance:
                lot_with_acceptance = Lot(meta=rederbrometa[n_i[K_META]], cam_set=img_sets[n_i[K_SET]])
                n_i[K_META] += 1
                n_i[K_SET] += 1
            elif K_SET in in_acceptance:
                lot_with_acceptance = Lot(meta=None, cam_set=img_sets[n_i[K_SET]])
                n_i[K_SET] += 1
            elif K_META in in_acceptance:
                lot_with_acceptance = Lot(meta=rederbrometa[n_i[K_META]], cam_set=None)
                n_i[K_META] += 1
            else:
                self.logger.error("Oups clearly something went wrong, nothing in the acceptance zone : %r", in_acceptance)
                lot_with_acceptance = None

            yield LotWithIndexes(next_meta_index=n_i[K_META], next_img_set_index=n_i[K_SET], lot=lot_with_acceptance)

    def correct_missing_meta_or_set(self, lots: List[Lot]) -> List[Lot]:
        """
        Correct lot when 1 lot has a missing meta and the following lot has missing set.

        :param lots: List of lots to be corrected.
        :return: The corrected list of lots.
        """
        result = []
        might_be_corrected = []
        for l in lots:
            if l.meta is not None and l.cam_set is not None:
                # Try to merge lots
                if len(might_be_corrected) == 2:
                    la = might_be_corrected[0]
                    lb = might_be_corrected[1]

                    if la.meta is None and lb.meta is not None:  # merging meta
                        la.meta = lb.meta
                    if la.cam_set is None and lb.cam_set is not None:  # merging cam_set
                        la.cam_set = lb.cam_set

                    # adding corrected set
                    result.append(la)
                    might_be_corrected = []
            else:
                might_be_corrected.append(l)

            if len(might_be_corrected) > 2:  # empty set as we will ne correct if they are more than 2 incomplete sets
                result.extend(might_be_corrected)
                might_be_corrected = []

            if l.meta is not None and l.cam_set is not None:  # append set if complete
                result.append(l)

        return result

    def generate_meta_cam_partitions(
            self,
            img_sets: List[ImageSet],
            partition_start_img_set_index: int=0,
            partition_start_meta_index: int=0,
            threshold_max_consecutive_incomplete_sets: int=THRESHOLD_MAX_CONSECUTIVE_INCOMPLETE_SETS,
            threshold_incomplete_set_window_size: int=THRESHOLD_WINDOW_SIZE,
            threshold_incomplete_set_max_in_window: int=THRESHOLD_WINDOW_MAX_ERRORS) -> Iterator[LotPartition]:
        """
        Generate partition of association of meta data and cam_set images.

        :param img_set: Images sets.
        :param partition_start_img_set_index: Index where we start partition generation (for images sets). Default 0.
        :param partition_start_meta_index: Index where we start partition (for metas). Default 0.
        :param threshold_max_consecutive_incomplete_sets: Tolerance max consecutive incomplete sets for a valid partition.
        :param threshold_incomplete_set_window_size: Tolerance size of the error window.
        :param threshold_incomplete_set_max_in_window: Max tolerated incomplete sets in the error window.
        :return: LotPartition (as an Iterator).
        """
        self.logger.debug("Generating camera and meta partitions.")
        # test/search reference cycle
        I_META = 0
        I_SET = 1
        rederbrometa = self.rederbrometa.get_metas()
        max_indexes = [0] * 2
        max_indexes[I_META] = len(rederbrometa)
        max_indexes[I_SET] = len(img_sets)
        next_indexes = [0] * 2
        next_indexes[I_META] = 0
        next_indexes[I_SET] = 0
        partition_start = [0] * 2
        partition_start[I_META] = partition_start_meta_index
        partition_start[I_SET] = partition_start_img_set_index
        fetcher_next_indexes = list(partition_start)

        indexe_gen = indexes_walk(nb_cams=2, cam_start_indexes=partition_start, cam_max_indexes=max_indexes)
        for indexes in indexe_gen:  # this will generate all possible index associations between meta and cam_sets in an optimal order
            self.logger.debug("Current indexes : %r", indexes)

            if indexes[I_SET] >= max_indexes[I_SET] or indexes[I_META] >= max_indexes[I_META]:  # max indexes reached, shouldn't happened
                raise StopIteration()

            lot = Lot(meta=rederbrometa[indexes[I_META]], cam_set=img_sets[indexes[I_SET]])
            while not(lot.cam_set.is_complete()) and indexes[I_SET] < max_indexes[I_SET]:  # reference indexes should be complete images sets
                indexes[I_SET] += 1
                lot = Lot(meta=rederbrometa[indexes[I_META]], cam_set=img_sets[indexes[I_SET]])

            if indexes[I_SET] >= max_indexes[I_SET] or not(lot.cam_set.is_complete()):
                raise StopIteration()

            self.logger.debug("Current lot to be used as reference for partitionning : %r ", lot)

            # Test cam_set as reference set
            incomplete_consecutive_sets_count = 0
            lots = []
            lot_since_last_save = []
            break_reason = 'NORMAL'
            incomplete_set_count = 0
            complete_set_count = 0
            partition_start = list(fetcher_next_indexes)  # updating start
            lot_generator = self.associate_meta(
                reference_lot=lot,
                img_sets=img_sets,
                start_meta_index=indexes[I_META],
                start_img_set_index=indexes[I_SET])
            max_consecutive_incomplete_sets = 0

            error_window = [0] * threshold_incomplete_set_window_size     # 1 when error, 0 when no errors
            success_window = [0] * 15  # success window, use to save fetcher_indexes
            # so that we rollback at the right position

            gen_img_index = 0

            try:
                for lot_with_indexes in lot_generator:
                    gen_lot = lot_with_indexes.lot
                    self.logger.debug("Generated log by lot_generator : %r", gen_lot)
                    lot_since_last_save.append(gen_lot)
                    if not(gen_lot.meta is None) and not(gen_lot.cam_set is None):
                        complete_set_count += 1
                        max_consecutive_incomplete_sets = max(max_consecutive_incomplete_sets, incomplete_consecutive_sets_count)
                        incomplete_consecutive_sets_count = 0
                    else:
                        incomplete_consecutive_sets_count += 1
                        incomplete_set_count += 1

                    error_window[gen_img_index % len(error_window)] = int(gen_lot.meta is None or gen_lot.cam_set is None)
                    success_window[gen_img_index % len(success_window)] = int(not(gen_lot.meta is None) and not(gen_lot.cam_set is None))

                    # rejection or stop conditions
                    if (incomplete_consecutive_sets_count > threshold_max_consecutive_incomplete_sets):
                        break_reason = "TOO MUCH INCOMPLETE CONSECUTIVE SETS"
                        self.logger.debug("Too much incomplete sets rejecting reference : %r", lot)
                        break

                    if sum(error_window) >= threshold_incomplete_set_max_in_window:
                        break_reason = "TOO MUCH INCOMPLETE LOT IN WINDOW (error_window)"
                        self.logger.debug("Too much incomplete sets in the error window, rejecting reference lot : %r", lot)
                        break

                    gen_img_index += 1

                    if sum(success_window) == len(success_window):
                        self.logger.debug("Success window completed saving current next indexes : fetcher_next_indexes = %r", fetcher_next_indexes)
                        lot_since_last_save = self.correct_missing_meta_or_set(lot_since_last_save)  # Correct lot simple lot_since_last_save

                        lots.extend(lot_since_last_save)   # adding set to generated sets
                        lot_since_last_save = []   # clearing set since last save has we just save this point
                        fetcher_next_indexes = [lot_with_indexes.next_meta_index, lot_with_indexes.next_img_set_index]

                        self.logger.debug("Found reference lot.cam_set.id_set: %i, lot.meta.id_meta: %i", lot.cam_set.id_set, lot.meta.id_meta)
            except CameraBackInTimeError as backintime_err:
                self.logger.warning("Catching CameraBackInTimeError : %r", backintime_err)
                break_reason = "BACK IN TIME CAMERA"
                fetcher_next_indexes = backintime_err.indexes  # Next indexes has this indexes weren't used to make an actual set
            except MetaBackInTimeError as backintime_err:
                self.logger.warning("Catching MetaBackInTimeError : %r", backintime_err)
                break_reason = "BACK IN TIME META"
                fetcher_next_indexes = backintime_err.indexes  # Next indexes has this indexes weren't used to make an actual set

            if fetcher_next_indexes != partition_start:
                self.logger.debug("Generating LotPartition, partition_start = %r, fetcher_next_indexes = %r", partition_start, fetcher_next_indexes)
                # generator should not suggest already used image, setting start indexes to the end of the partition
                indexe_gen.send(list(fetcher_next_indexes))  # copy list so that there are no reference issues

                # returning the generated partition
                yield LotPartition(
                    ref_lot=lot,
                    lots=lots,
                    start_imgset_index=partition_start[I_SET],
                    start_meta_index=partition_start[I_META],
                    break_reason=break_reason,
                    number_of_good_associations=complete_set_count)

    def generate_all_lot(
            self,
            img_sets: List[ImageSet],
            threshold_max_consecutive_incomplete_sets: int=THRESHOLD_MAX_CONSECUTIVE_INCOMPLETE_SETS,
            threshold_incomplete_set_window_size: int=THRESHOLD_WINDOW_SIZE,
            threshold_incomplete_set_max_in_window: int=THRESHOLD_WINDOW_MAX_ERRORS) -> List[Lot]:
        """
        Generate list of Lot from partitions.

        :param img_set: Images sets.
        :param threshold_max_consecutive_incomplete_sets: Tolerance max consecutive incomplete sets for a valid partition.
        :param threshold_incomplete_set_window_size: Tolerance size of the error window.
        :param threshold_incomplete_set_max_in_window: Max tolerated incomplete sets in the error window.
        :return: A list of generated lots.
        """
        lots = []
        partition_start_img_set_index = 0
        partition_start_meta_index = 0

        self.logger.debug("Start generating all lots")
        for partition in self.generate_meta_cam_partitions(
                img_sets=img_sets,
                partition_start_img_set_index=partition_start_img_set_index,
                partition_start_meta_index=partition_start_meta_index,
                threshold_max_consecutive_incomplete_sets=threshold_max_consecutive_incomplete_sets,
                threshold_incomplete_set_window_size=threshold_incomplete_set_window_size,
                threshold_incomplete_set_max_in_window=threshold_incomplete_set_max_in_window):
            lots.extend(partition.lots)

        return lots


class InvalidReferenceSetError(OpvImportError):
    pass

class InvalidReferenceLotError(OpvImportError):
    pass

class MetaBackInTimeError(OpvImportError):

    def __init__(self, indexes: List[int]=None):
        """
        When back in time occured with rederbro metas.

        :param indexes: indexes where back in time where detected (back in time bewteen indexes[x]-1 and indexes).
        :type indexes: List[int], first is meta index, second image set index.
        """
        self.indexes = indexes

        Exception.__init__(self, self.__repr__())

    def __repr__(self) -> str:
        return "Back in time at meta/img_sets indexes {}.".format(str(self.indexes))


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
