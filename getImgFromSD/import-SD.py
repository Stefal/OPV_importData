import json
import csv
import threading
import subprocess
import os

from time import sleep
from collections import UserDict

import pyudev

from utils import singleton


class APN_copy(threading.Thread):
    """A class which will mount and copy the APN data to work dir"""
    def __init__(self, devname):
        threading.Thread.__init__(self)
        self.devname = devname
        self.start()

    def run(self):
        # Boooooouuuuuhhh ugly
        sleep(1) # wait 1 sec, waiting the system to setup device block file

        success = self.mount()
        success = success and self.doCopy()

        self.unmount()

        if not success:
            print("Tutute ! Erreur lors de la copie")

    def foundMountedPath(self):
        with open("/proc/mounts", "r") as mounts:
            for line in mounts:
                if line.startswith(self.devname):
                    return line.split(' ')[1]

    def doCopy(self):
        src = self.foundMountedPath()

        try: # Get config file for APN
            with open(os.path.join(src, "APN_config"), "r") as apnConfFile:
                apn_conf = json.load(apnConfFile)
        except FileNotFoundError: # if partition isn't OPV data partition
            return False

        apn_n = apn_conf['APN_num'] # read the APN number in config file

        dest = os.path.expanduser(
                os.path.join(Main().config['data_dir'].format(campaign = Main().campaign),
                             "APN{}".format(apn_n))
                )

        try:
            print("Copying started from {} to {}".format(src,dest))
            subprocess.run(['mkdir', '-p', dest]) # create structure
            subprocess.run(['rsync', '-a', src, dest]) # copy files
            print("Copying finished from {} to {}".format(src,dest))
            Main().APN_copied(apn_n)
        except subprocess.CalledProcessError:
            return False
        return True

    def mount(self):
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
        while self.pictInfoLocation != "0" or os.path.exists(self.pictInfoLocation):
            self.pictInfoLocation = input("Enter path where is located pictInfo on this PC (or 0 for fetching with scp): ")
        if self.pictInfoLocation == "0":
            self.getPictureInfoFromPi()


    def APN_copied(self, apn_n):
        self.APN_treated[apn_n] = True
        if all(self.APN_treated):
            self.stop()

    def APN_connected(self, device: pyudev.Device):
        """ A fct which will start a thread to copy the SDCARD
        :device: the device where is situed the APN
        """
        devname = device['DEVNAME']
        APN_copy(devname)

    def getPictureInfoFromPi(self):
        self.pictInfoLocation = os.path.join(self.config['data_dir'], "pictureInfo.csv")
        subprocess.run(["scp", "pi@192.168.42.1:/home/pi/opv/lastPictureInfo.csv", self.pictInfoLocation])

    def start(self):
        self.lock.clear()
        WaitForSDCard().start()
        self.getPictureInfo()

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
