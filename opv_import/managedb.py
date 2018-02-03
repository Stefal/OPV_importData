#!/usr/bin/python3
# coding: utf-8

from opv_api_client import RestClient, ressources
from opv_api_client.exceptions import RequestAPIException
from geojson import Point

client = None


def make_client(api_uri='http://localhost:5000'):
    """
    Have to be called before any use of function from this file !
    """
    global client
    client = RestClient(api_uri)


def make_campaign(id_malette, name, id_rederbro, description):
    campaign = client.make(ressources.Campaign)
    campaign.id_malette = id_malette
    campaign.name = name
    campaign.id_rederbro = id_rederbro
    campaign.description = description
    campaign.create()
    return campaign


def make_lot(id_malette, campaign, pictures_path, sensors, goprofailed, takenDate, tile=None):
    lot = client.make(ressources.Lot)
    lot.id_malette = id_malette
    lot.campaign = campaign
    lot.pictures_path = pictures_path
    lot.sensors = sensors
    lot.goprofailed = goprofailed
    lot.takenDate = takenDate.isoformat()
    lot.tile = tile
    lot.create()
    return lot

def make_sensors(id_malette, alt, lng, lat, degrees, minutes):
    sensors = client.make(ressources.Sensors)
    sensors.id_malette = id_malette

    sensors.gps_pos = Point((lat, lng, alt))

    sensors.degrees = degrees
    sensors.minutes = minutes
    sensors.create()
    return sensors


def make_cp(id_malette, search_algo_version, nb_cp, stichable, optimized, lot):
    cp = client.make(ressources.Cp)
    cp.id_malette = id_malette
    cp.search_algo_version = search_algo_version
    cp.nb_cp = nb_cp
    cp.stichable = stichable
    cp.optimized = optimized
    cp.lot = lot
    cp.create()
    return cp


def make_panorama(id_malette, equirectangular_path, cp):
    panorama = client.make(ressources.Panorama)
    panorama.id_malette = id_malette
    panorama.equirectangular_path = equirectangular_path
    panorama.cp = cp
    panorama.create()
    return panorama


def make_tile(id_malette, param_location, fallback_path, extension, resolution, max_level, cube_resolution, panorama):
    tile = client.make(ressources.Tile)
    tile.id_malette = id_malette
    tile.param_location = param_location
    tile.fallback_path = fallback_path
    tile.extension = extension
    tile.resolution = resolution
    tile.max_level = max_level
    tile.cube_resolution = cube_resolution
    tile.id_panorama = panorama.id_panorama
    tile.id_malette = panorama.id_malette
    tile.create()
    return tile
