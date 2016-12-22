import managedb
import filemanager
import datetime

def treat(campaign, l):
    sensorsData = l['csv'].data

    sensors = managedb.make_sensors(sensorsData['gps']['lat'],
                                    sensorsData['gps']['lon'],
                                    sensorsData['gps']['alt'],
                                    sensorsData['compass']['degree'],
                                    sensorsData['compass']['minutes'])

    pictures_path = filemanager.addFiles(l)

    date = datetime.datetime.fromtimestamp(sensorsData['takenDate'])
    lot = managedb.make_lot(campaign,
                            pictures_path,
                            sensors,
                            sensorsData['goproFailed'],
                            date)

    print("Lot n°{} generated".format(lot.id))
    if len(lot) != 7:
        print("Malformed lot n°{}".format(lot.id))
    print("All lots generated")
