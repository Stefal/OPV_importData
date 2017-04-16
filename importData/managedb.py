#!/usr/bin/python3
# coding: utf-8

from opv_api_client import RestClient, RessourceEnum

client = None


def make_client(api_uri='http://localhost:5000'):
    """
    Have to be called before any use of function from this file !
    """
    global client
    client = RestClient(api_uri)


def make_campaign(id_malette, name, id_rederbro, description):
    campaign = client.make(RessourceEnum.campaign)
    campaign.id_malette = id_malette
    campaign.name = name
    campaign.id_rederbro = id_rederbro
    campaign.description = description
    campaign.create()
    return campaign


def make_lot(id_malette, campaign, pictures_path, sensors, goprofailed, takenDate, tile=None):
    lot = client.make(RessourceEnum.lot)
    lot.id_malette = id_malette
    lot.id_campaign = campaign.id_campaign
    lot.id_campaign_malette = campaign.id_malette
    lot.pictures_path = pictures_path
    lot.id_sensors_malette = sensors.id_malette
    lot.id_sensors = sensors.id_sensors
    lot.goprofailed = goprofailed
    lot.takenDate = takenDate.isoformat()
    lot.tile = tile
    lot.create()
    return lot

def make_sensors(id_malette, alt, lng, lat, degrees, minutes):
    sensors = client.make(RessourceEnum.sensors)
    sensors.id_malette = id_malette
    sensors.alt = alt
    sensors.lat = lat
    sensors.lng = lng
    sensors.degrees = degrees
    sensors.minutes = minutes
    sensors.create()
    return sensors


def make_cp(id_malette, search_algo_version, nb_cp, stichable, optimized, lot):
    cp = client.make(RessourceEnum.cp)
    cp.id_malette = id_malette
    cp.search_algo_version = search_algo_version
    cp.nb_cp = nb_cp
    cp.stichable = stichable
    cp.optimized = optimized
    cp.id_lot = lot.id_lot
    cp.id_lot_malette = lot.id_malette
    cp.create()
    return cp


def make_panorama(id_malette, equirectangular_path, cp):
    panorama = client.make(RessourceEnum.panorama)
    panorama.id_malette = id_malette
    panorama.equirectangular_path = equirectangular_path
    panorama.id_cp = cp.id_cp
    panorama.id_cp_malette = cp.id_cp_malette
    panorama.create()
    return panorama


def make_tile(id_malette, param_location, fallback_path, extension, resolution, max_level, cube_resolution, panorama):
    tile = client.make(RessourceEnum.tile)
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
