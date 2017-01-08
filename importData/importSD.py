import json
import pyudev
import threading
import subprocess
import os
from shutil import copyfile

from time import sleep

from path import path

from utils import singleton, ensure_dir


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
        sleep(1)  # wait 1 sec, waiting the system to setup device block file

        if self.foundMountedPath():
            return  # already mounted, error
        success = self.mount()
        success = success and self.getAPNConf()

        if success and Main().APN_treated[self.apn_n]:  # SDCard already treated
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
                    return path(line.split(' ')[1])

    def doClearSD(self):
        """
        Reset the SD card
        return False on error, True otherwise
        """
        ex = True

        c, iso = Main().config.get('clearSD', 'ISO')

        if not c:  # Don't clear anything
            return True

        iso = os.path.expanduser(iso)

        print("Starting to clear APN", self.apn_conf['APN_num'])
        try:
            #subprocess.run(['sudo', 'dd', 'if=' + iso, 'of=' + self.parent_devname])
            pass
        except subprocess.CalledProcessError:
            ex = False
        else:
            sleep(1)  # Wait devname to be updated
            ex = self.mount()

            mountedpath = self.foundMountedPath()

            if ex:
                with open(os.path.join(mountedpath, "APN_config"), "w") as apnConfFile:
                    json.dump(self.apn_conf, apnConfFile)
            self.unmount()
        print("APN", self.apn_conf['APN_num'], "cleared")

        return ex

    def getAPNConf(self):
        src = self.foundMountedPath()  # Where is mounted devname

        try:  # Get config file for APN
            with open(path(src) / "APN_config", "r") as apnConfFile:
                self.apn_conf = json.load(apnConfFile)
        except FileNotFoundError:  # if partition isn't OPV data partition
            print("Error ! No APN_config file founded")
            return False

        self.apn_n = self.apn_conf.get('APN_num', None)
        return True

    def doCopy(self):
        """
        copy all the photo from the SD card
        return False on error, True otherwise
        """
        ex = True  # return code

        dataDir = Main().config.get('data-dir')
        src = self.foundMountedPath()  # Where is mounted devname

        try:
            apn_n = self.apn_conf['APN_num']  # read the APN number in config file
        except KeyError:
            print("We don't know what is the number of APN, aborting")
            return False
        print(apn_n)
        a=dataDir.format(campaign=Main().campaign)
        print(a)
        dest = path(a).expand() / "APN{}".format(apn_n)

        dest.makedirs_p()

        print("Copying started from {} to {}".format(src, dest))

        for f in src.walkfiles('*.JPG'):
            f.copy(dest)

        print("Copying finished from {} to {}".format(src, dest))
        Main().APN_copied(apn_n)

        return ex

    def mount(self):
        """
        mount devname using udisckctl
        return False on error, True otherwise
        """
        try:
            subprocess.call(['udisksctl', 'mount', '-b', self.devname])
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
            subprocess.call(['udisksctl', 'unmount', '-b', self.devname])
        except subprocess.CalledProcessError:
            print("{} not unmounted".format(self.devname))
        except FileNotFoundError:
            print("udisks not installed on system")


@singleton
class Main:
    def __init__(self):
        self.lock = threading.Event()
        self.APN_treated = [False for x in range(6)]

    def init(self, campaign, conf):
        self.campaign = campaign
        self.config = conf

        self.pictInfoLocation = ""

        # get pictInfoLocation
        while self.pictInfoLocation != "0" and not os.path.exists(self.pictInfoLocation):
            self.pictInfoLocation = input("Enter path where is located pictInfo on this PC (or 0 for fetching with scp): ")

        print(self.config.get('data-dir'))

        pictInfoDir = self.config.get('data-dir')
        pictInfoDir = os.path.expanduser(pictInfoDir.format(campaign=campaign))
        ensure_dir(pictInfoDir)
        dest = os.path.join(pictInfoDir, "pictureInfo.csv")

        if self.pictInfoLocation == "0":
            if not self.getPictureInfoFromPi(dest):
                print("Can't get picture info from pi")
        else:
            copyfile(self.pictInfoLocation, dest)

        return self

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

    def getPictureInfoFromPi(self, dest):
        """
        Get the csv file from the raspberry pi
        return False on Error
        """
        ex = True
        try:
            with self.config.get('data-dir', 'pi-location') as (piLocation,):
                subprocess.call(["scp", piLocation, dest])

        except KeyError:
            print("Please check data_dir and pi_location on the json file")
            ex = False
        except subprocess.CalledProcessError:
            ex = False

        return ex

    def start(self):
        if not self.campaign:
            print('Any campaign specified')

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

    def onEvent(self, action, device: pyudev.Device):
        """Called when a device event happen

        :device: A pyudev device object
        """
        if not action == "add" or 'partition' not in device.attributes.available_attributes:  # Not a partition or not added device
            return

        Main().APN_connected(device)
