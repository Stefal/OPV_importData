import managedb
import filemanager
import datetime

def treat(campaign, l):

    try:
        sensorsData = l['csv'].data
    except KeyError:
        sensorsData = {'gps': {'lat': 0, 'lon': 0, 'alt': 0},
                       'compass': {'degree': 0, 'minutes': 0},
                      'takenDate': 0,
                       'goproFailed': 0}

    sensors = managedb.make_sensors(sensorsData['gps']['lat'],
                                    sensorsData['gps']['lon'],
                                    sensorsData['gps']['alt'],
                                    sensorsData['compass']['degree'],
                                    sensorsData['compass']['minutes'])

    pictures_path = filemanager.addFiles(l.copy())

    date = datetime.datetime.fromtimestamp(sensorsData['takenDate'])
    lot = managedb.make_lot(campaign,
                            pictures_path,
                            sensors,
                            sensorsData['goproFailed'],
                            date)

    if len(l) != 7:
        print("Malformed lot n°{}".format(lot.id))
    print("Lot n°{} generated".format(lot.id))
