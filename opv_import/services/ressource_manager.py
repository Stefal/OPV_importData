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
# Description: Service to save ressources using business logic (API and DM).

import os
import logging
import datetime

from opv_api_client import RestClient as DbRestClient
from opv_api_client import ressources as DbRestRessources
from opv_directorymanagerclient import DirectoryManagerClient as DmClient

from typing import Dict

from path import Path

from opv_import import model

from geojson import Point

class RessourceManager():
    """
    Service to manage ressources with database.
    """

    def __init__(self, opv_api_client: DbRestClient, opv_dm_client: DmClient, id_malette: int, use_hardlink: bool=False):
        """
        Intentiate a ressource manager, with APIs URI.

        :param opv_api_uri: URI of the DBRest API.
        :param opv_dm_uri: URI of the Directory Manager API.
        :param id_malette: Current malette ids.
        :param use_hardlink: If true will use hardlinking with Directory Manager.
        """
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self._opv_api_client = opv_api_client
        self._opv_dm_client = opv_dm_client
        self._id_malette = id_malette
        self._use_hardlink = use_hardlink

    def make_campaign(self, name: str, id_rederbro: int, description: str) -> DbRestRessources.Campaign:
        """
        Create a campaign.

        :param id_malette: Malette ID.
        :param name: Campaign name.
        :param id_rederbro: Rederbro/backpack ID.
        :param description: Description of the campaign.
        :return: The created campaign.
        """
        self.logger.debug("Creating campaign in database, with name : %s ", name)

        campaign = self._opv_api_client.make(DbRestRessources.Campaign)
        campaign.id_malette = self._id_malette
        campaign.name = name
        campaign.id_rederbro = id_rederbro
        campaign.description = description
        campaign.create()

        self.logger.debug("Created campaign in database, id_campaign: %i, id_malette: %i", campaign.id_campaign, campaign.id_malette)
        return campaign

    def _model_gp_error_to_db(self, bools: Dict[int, bool]) -> int:
        """
        Convert model GP_error to db representation.

        :param bools: Rederbro Meta GP errors.
        :return: Corresponding database representation as integer.
        """
        val = 0
        for k in bools:
            mask = bools[k] << k
            val |= mask
        return val

    def make_sensors(self, meta: model.RederbroMeta) -> DbRestRessources.Sensors:
        """
        Create/save a sensors in DB.

        :param meta: RederbroMeta datas used to create the sensor.
        :return: The created sensors.
        """
        self.logger.debug("Saving sensors/rederbrometa : %r", meta)

        dbsensors = self._opv_api_client.make(DbRestRessources.Sensors)
        dbsensors.id_malette = self._id_malette
        dbsensors.gps_pos = Point(coordinates=meta.geopoint.coordinates)
        dbsensors.degrees = meta.orientation.degree
        dbsensors.minutes = meta.orientation.minutes
        dbsensors.create()

        self.logger.debug("Saved sensors with id : %i, id_malette: %i", dbsensors.id_sensors, dbsensors.id_malette)
        return dbsensors

    def make_picture_path(self, img_set: model.ImageSet) -> str:
        """
        Save image set in Directory Manager and return it's uuid.

        :param img_set: Image set to be saved in DM.
        :return: The directory manager UUID.
        """
        with self._opv_dm_client.Open() as (uuid, dir_path):
            for key, photo in img_set.items():
                dest = Path(dir_path) / 'APN{}{}'.format(key, photo.path.ext.upper())
                if self._use_hardlink:
                    self.logger.debug("Hardlinking : {} -> {}".format(photo.path, dest))
                    os.link(photo.path, dest)
                else:
                    photo.path.copy(dest)

        self.logger.debug("Imageset stored in uuid : %s", uuid)
        return uuid

    def make_lot(self, lot: model.Lot, campaign: DbRestRessources.Campaign) -> DbRestRessources.Lot:
        """
        Create a lot.

        :param lot: OPV Import lot.
        :param campaign: Associated campaign.
        :return: The database created lot.
        """
        self.logger.debug("Saving lot : %r, for campaign.id_campaign: %i", lot, campaign.id_campaign)

        if lot.meta is None or lot.meta.geopoint is None or lot.cam_set is None:
            raise InvalidLotForDbError("Lot must have meta, sensors and cam_set ...")


        dblot = self._opv_api_client.make(DbRestRessources.Lot)
        dblot.id_malette = self._id_malette
        dblot.campaign = campaign
        dblot.pictures_path = self.make_picture_path(img_set=lot.cam_set)  # creates DM uuid
        dblot.tile = None   # No tile at this stage
        dblot.sensors = self.make_sensors(meta=lot.meta)
        dblot.goprofailed = self._model_gp_error_to_db(lot.meta.gopro_errors)
        dblot.takenDate = datetime.datetime.fromtimestamp(lot.meta.timestamp, tz=datetime.timezone.utc).isoformat()

        dblot.create()

        self.logger.debug("Saved lot with id_lot: %i, id_malette: %i", dblot.id_lot, dblot.id_malette)
        return dblot


class InvalidLotForDbError(model.OpvImportError):
    """
    When a lot is not valid for saving in database.
    """
