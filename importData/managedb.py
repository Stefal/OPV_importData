#!/usr/bin/python3
# coding: utf-8

from potion_client import Client

client = None


def make_client(api_uri='http://localhost:5000'):
    """
    Have to be called before any use of function from this file !
    """
    global client
    client = Client(api_uri)


def make_campaign(name, id_rederbro, description):
    campaign = client.Campaign()
    campaign.name = name
    campaign.id_rederbro = id_rederbro
    campaign.description = description
    campaign.save()
    return campaign


def make_lot(campaign, pictures_path, sensors, goprofailed, takenDate, tile=None):
    lot = client.Lot()
    lot.campaign = campaign
    lot.pictures_path = pictures_path
    lot.sensors = sensors
    lot.goprofailed = goprofailed
    lot.takenDate = takenDate
    lot.tile = tile
    lot.save()
    return lot

def make_sensors(alt, lng, lat, degrees, minutes):
    sensors = client.Sensors()
    sensors.alt = alt
    sensors.lat = lat
    sensors.lng = lng
    sensors.degrees = degrees
    sensors.minutes = minutes
    sensors.save()
    return sensors


def make_cp(search_algo_version, nb_cp, stichable, optimized, lot):
    cp = client.Cp()
    cp.search_algo_version = search_algo_version
    cp.nb_cp = nb_cp
    cp.stichable = stichable
    cp.optimized = optimized
    cp.lot = lot
    cp.save()
    return cp


def make_panorama(equirectangular_path, cp):
    panorama = client.Panorama()
    panorama.equirectangular_path = equirectangular_path
    panorama.cp = cp
    panorama.save()
    return panorama


def make_tile(param_location, fallback_path, extension, resolution, max_level, cube_resolution, panorama):
    tile = client.Tile()
    tile.param_location = param_location
    tile.fallback_path = fallback_path
    tile.extension = extension
    tile.resolution = resolution
    tile.max_level = max_level
    tile.cube_resolution = cube_resolution
    tile.panorama = panorama
    tile.save()
    return tile
