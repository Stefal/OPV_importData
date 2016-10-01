import json
import threading
import subprocess
import os

from time import sleep
from collections import UserDict

import pyudev

from utils import singleton


class APN_copy(threading.Thread):
    """
    A class which will mount and copy the APN data to work dir
    """
    def __init__(self, devname, parent_devname):
        threading.Thread.__init__(self)
        self.devname = devname
        self.parent_devname = parent_devname
        self.start()

    def run(self):
        # Boooooouuuuuhhh ugly
        sleep(1) # wait 1 sec, waiting the system to setup device block file

        if self.foundMountedPath():
            return #already mounted, error
        success = self.mount()
        success = success and self.getAPNConf()

        if success and Main().APN_treated[self.apn_n]:# SDCard already treated
            self.unmount()
            return

        success = success and self.doCopy()

        self.unmount()

        success = success and self.doClearSD()

        if not success:
            print("Tutute ! Erreur lors de la copie")

    def foundMountedPath(self):
        """
        Return the path of the mounted path of self.devname
        """
        with open("/proc/mounts", "r") as mounts:
            for line in mounts:
                if line.startswith(self.devname):
                    return line.split(' ')[1]

    def doClearSD(self):
        """
        Reset the SD card
        return False on error, True otherwise
        """
        ex = True

        if(Main().config['clearSD']):
            print("Starting to clear APN", self.apn_conf['APN_num'])
            iso = os.path.expanduser(Main().config['ISO'])

            try:
               subprocess.run(['sudo', 'dd', 'if=' + iso, 'of=' + self.parent_devname])
            except subprocess.CalledProcessError:
                ex = False
            else:
                sleep(1) #Wait devname to be updated
                ex = self.mount()

                mountedpath = self.foundMountedPath()

                if ex:
                    with open(os.path.join(mountedpath, "APN_config"), "w") as apnConfFile:
                        json.dump(self.apn_conf ,apnConfFile)
                self.unmount()
            print("APN", self.apn_conf['APN_num'], "cleared")

        return ex

    def getAPNConf(self):
        src = self.foundMountedPath() #Where is mounted devname

        try: # Get config file for APN
            with open(os.path.join(src, "APN_config"), "r") as apnConfFile:
                self.apn_conf = json.load(apnConfFile)
        except FileNotFoundError: # if partition isn't OPV data partition
            print("Error ! No APN_config file founded")
            return False

        self.apn_n = self.apn_conf.get('APN_num', None)
        return True

    def doCopy(self):
        """
        copy all the photo from the SD card
        return False on error, True otherwise
        """
        ex = True #return code

        src = self.foundMountedPath() #Where is mounted devname

        try:
            apn_n = self.apn_conf['APN_num'] # read the APN number in config file
        except KeyError:
            print("We don't know what is the number of APN, aborting")
            return False

        dest = os.path.expanduser(
                os.path.join(Main().config['data_dir'].format(campaign = Main().campaign),
                    "APN{}".format(apn_n))
                )

        print("Copying started from {} to {}".format(src,dest))
        try:
            subprocess.run(['mkdir', '-p', dest]) # create structure
            subprocess.run(['rsync', '-a', src, dest]) # copy files
        except subprocess.CalledProcessError:
            ex = False
        else:
            print("Copying finished from {} to {}".format(src,dest))
            Main().APN_copied(apn_n)

        return ex

    def mount(self):
        """
        mount devname using udisckctl
        return False on error, True otherwise
        """
        try:
            subprocess.run(['udisksctl', 'mount', '-b',self.devname])
        except subprocess.CalledProcessError:
            print("{} not mounted".format(self.devname))
            return False
        except FileNotFoundError:
            print("udisks not installed on system")
            return False
        return True

    def unmount(self):
        """
        unmount devname using udisckctl
        """
        try:
            subprocess.run(['udisksctl', 'unmount', '-b',self.devname])
        except subprocess.CalledProcessError:
            print("{} not unmounted".format(self.devname))
        except FileNotFoundError:
            print("udisks not installed on system")


@singleton
class Main:
    def __init__(self):
        self.config = Config()
        self.lock = threading.Event()
        self.APN_treated = [False for x in range(6)]
        self.campaign = input("Please, enter the campaign name: ")

        self.pictInfoLocation = ""

        #get pictInfoLocation
        while self.pictInfoLocation != "0" and not os.path.exists(self.pictInfoLocation):
            self.pictInfoLocation = input("Enter path where is located pictInfo on this PC (or 0 for fetching with scp): ")

        if self.pictInfoLocation == "0":
            if not self.getPictureInfoFromPi():
                print("Can't get picture info from pi")


    def APN_copied(self, apn_n):
        self.APN_treated[apn_n] = True
        if all(self.APN_treated):
            self.stop()

    def APN_connected(self, device: pyudev.Device):
        """ A fct which will start a thread to copy the SDCARD
        :device: the device where is situed the APN
        """
        devname = device['DEVNAME']
        parent_devname = device.parent['DEVNAME']
        APN_copy(devname, parent_devname)

    def getPictureInfoFromPi(self):
        """
        Get the csv file from the raspberry pi
        return False on Error
        """
        ex = True
        try:
            pictInfoDir = self.config['data_dir']
            piLocation = self.config["pi_location"]
        except KeyError:
            print("Please check data_dir and pi_location on the json file")
            ex = False
        else:
            self.pictInfoLocation = os.path.join(pictInfoDir, "pictureInfo.csv")
            try:
                subprocess.run(["scp", piLocation, self.pictInfoLocation])
            except subprocess.CalledProcessError:
                ex = False
        return ex

    def start(self):
        self.lock.clear()
        WaitForSDCard().start()

        try:
            while not self.lock.is_set():
                pass
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.lock.set()
        WaitForSDCard().stop()

class Config(UserDict):
    """A class which contain all the configuration"""
    def __init__(self, configFile: str = 'config/main.json'):
        super().__init__()
        self.configFile = configFile
        self._fetchConfig()

    def _fetchConfig(self):
        try:
            with open(self.configFile, "r") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            print("Fatal Error: No config file")
            Main().stop()
        except json.decoder.JSONDecodeError:
            print("Malformed JSON")

    def reloadConfigFile(self):
        self._fetchConfig()

@singleton
class WaitForSDCard:
    def __init__(self):
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='block')

        self.observer = pyudev.MonitorObserver(self.monitor, self.onEvent, name='OPV SD observer')

    def start(self):
        self.observer.start()

    def stop(self):
        self.observer.stop()

    def onEvent(self,action, device: pyudev.Device):
        """Called when a device event happen

        :device: A pyudev device object
        """
        if not action == "add" or not 'partition' in device.attributes.available_attributes: # Not a partition or not added device
            return

        Main().APN_connected(device)

if __name__ == "__main__":
    Main().start()
