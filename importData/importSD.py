#!/usr/bin/python3
# coding: utf-8

import json
import pyudev
import threading
import subprocess
import os

import logging
from shutil import copyfile
from time import sleep
from path import Path

logger = logging.getLogger(__name__)

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
        logger.info("APN_copy -- run ", self.devname)
        # Boooooouuuuuhhh ugly
        sleep(1)  # wait 1 sec, waiting the system to setup device block file

        if not self.foundMountedPath():
            self.mount()

        success = self.foundMountedPath() and self.getAPNConf()

        if success and Main().APN_treated[self.apn_n]:  # SDCard already treated
            self.unmount()
            return

        success = success and self.doCopy()

        self.unmount()

        if not success:
            logger.warning("Tutute ! Erreur lors de la copie")

    def foundMountedPath(self):
        """
        Return the path of the mounted path of self.devname
        """
        with open("/proc/mounts", "r") as mounts:
            for line in mounts:
                if line.startswith(self.devname):
                    return Path(line.split(' ')[1])

    def getAPNConf(self):
        src = self.foundMountedPath()  # Where is mounted devname

        try:  # Get config file for APN
            with open(Path(src) / "APN_config", "r") as apnConfFile:
                self.apn_conf = json.load(apnConfFile)
        except FileNotFoundError:  # if partition isn't OPV data partition
            logging.error("Error ! No APN_config file founded")
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
            logger.error("We don't know what is the number of APN, aborting")
            return False
        a = dataDir.format(campaign=Main().campaign)
        dest = Path(a).expand() / "APN{}".format(apn_n)

        dest.makedirs_p()

        logger.info("Copying started from {} to {}".format(src, dest))

        for f in src.walkfiles('*.JPG'):
            f.copy(dest)

        logger.info("Copying finished from {} to {}".format(src, dest))
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
            logger.error("{} not mounted".format(self.devname))
            return False
        except FileNotFoundError:
            logger.error("udisks not installed on system")
            return False
        return True

    def unmount(self):
        """
        unmount devname using udisckctl
        """
        try:
            subprocess.call(['udisksctl', 'unmount', '-b', self.devname])
        except subprocess.CalledProcessError:
            logger.error("{} not unmounted".format(self.devname))
        except FileNotFoundError:
            logger.error("udisks not installed on system")


class Main:
    def __init__(self):
        self.lock = threading.Event()
        self.APN_treated = [False for x in range(6)]

    def init(self, campaign, conf):
        self.campaign = campaign
        self.config = conf
        self.pictInfoLocation = self.config.get('csv-path', None)

        # get pictInfoLocation if None
        if not self.pictInfoLocation:
            while not self.pictInfoLocation or self.pictInfoLocation != "0" and not os.path.exists(self.pictInfoLocation):
                self.pictInfoLocation = input("Enter path where is located pictInfo on this PC (or 0 for fetching with scp): ")
        logger.info("... CSV path : %s" % (self.pictInfoLocation))
        logger.info("... Campaign : %s" % (self.campaign))
        logger.info("... Let's work on : %s" % (self.config.get('data-dir')))

        pictInfoDir = self.config.get('data-dir')
        pictInfoDir = os.path.expanduser(pictInfoDir.format(campaign=campaign))
        ensure_dir(pictInfoDir)
        dest = os.path.join(pictInfoDir, "pictureInfo.csv")

        if self.pictInfoLocation == "0":
            if not self.getPictureInfoFromPi(dest):
                logger.critical("Can't get picture info from pi")
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
        if 'parent' in device:
            parent_devname = device.parent['DEVNAME']
        else:
            parent_devname = device['DEVNAME'][:-1]
        logger.info("APN_connected : ", devname, "--", parent_devname)
        APN_copy(devname, parent_devname)

    def getPictureInfoFromPi(self, dest):
        """
        Get the csv file from the raspberry pi
        return False on Error
        """
        ex = True
        try:
            piLocation = self.config['pi-location']
            subprocess.call(["scp", piLocation, dest])
        except KeyError:
            logger.error("Please check and pi_location on the json file")
            ex = False
        except subprocess.CalledProcessError:
            ex = False

        return ex

    def start(self):
        if not self.campaign:
            logging.critical('Any campaign specified')
            return

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

        if action == "add" and 'DEVNAME' in device.keys() and "partition" in device.attributes.available_attributes:
            Main().APN_connected(device)
