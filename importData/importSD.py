#!/usr/bin/python3
# coding: utf-8

import os
import json
import shutil
import pyudev
import logging
import threading
import subprocess

from time import sleep
from shutil import copyfile

logger = logging.getLogger(__name__)


class APN_copy(threading.Thread):
    """
    A class which will mount and copy the APN data to work dir
    """
    def __init__(self, devname, parent_devname, pictDir):
        threading.Thread.__init__(self)
        self.devname = devname
        self.parent_devname = parent_devname
        self.pictDir = pictDir
        self.src = ''
        self.start()

    def run(self):
        logger.info("Mounting %s ...", self.devname)
        # Boooooouuuuuhhh ugly
        sleep(1)  # wait 1 sec, waiting the system to setup device block file

        if not self.foundMountedPath():
            self.mount()

        success = self.getAPNConf()
        logger.info("APN%s detected", self.apn_n)

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
                    return line.split(' ')[1]

    def getAPNConf(self):
        self.src = self.foundMountedPath()  # Where is mounted devname

        try:  # Get config file for APN
            with open(self.src + "/APN_config.json", "r") as apnConfFile:
                self.apn_conf = json.load(apnConfFile)
        except FileNotFoundError:  # if partition isn't OPV data partition
            logger.error("Error ! No APN_config file founded")
            return False

        self.apn_n = self.apn_conf.get('APN_num', None)
        return True

    def doCopy(self):
        """
        copy all the photo from the SD card
        """
        self.dest = self.pictDir + "APN" + str(self.apn_n)
        # Creation of dir with the name of the apn
        os.makedirs(self.dest, exist_ok=True)
        logger.info("Copying started from %s to %s ...", self.src, self.dest)

        # BE CARREFUL we can have multiple directories whith same filename
        for root, dirs, files in os.walk(self.src):
            for filename in files:
                # I use absolute path, case you want to move several dirs.
                old_name = os.path.join(os.path.abspath(root), filename)

                # Separate base from extension
                base, extension = os.path.splitext(filename)
                if extension != ".JPG":
                    # not a JPG let's continue
                    continue
                # Initial new name
                new_name = os.path.join(self.dest, base + "_" + filename)

                # import pdb; pdb.set_trace()
                if not os.path.exists(new_name):  # folder exists, file does not
                    shutil.copy(old_name, new_name)
                    logger.info("Copied %s to %s", old_name, new_name)

        logger.info("... Copy finished")
        return self.apn_n

    def mount(self):
        """
        mount devname using udisckctl
        return False on error, True otherwise
        """
        try:
            p = subprocess.Popen(['udisksctl', 'mount', '-b', self.devname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            logger.info("..." + out.decode('ascii'))
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
        logger.info("* CSV path : %s" % (self.pictInfoLocation))
        logger.info("* Campaign : %s" % (self.campaign))

        self.pictDir = self.config.get('data-dir')
        self.pictDir = os.path.expanduser(self.pictDir.format(campaign=campaign))

        os.makedirs(self.pictDir, exist_ok=True)
        dest = os.path.join(self.pictDir, "pictureInfo.csv")

        if self.pictInfoLocation == "0":
            if not self.getPictureInfoFromPi(dest):
                logger.critical("Can't get picture info from pi")
        else:
            logger.info("Let's copy pictureInfo.csv in : %s ..." % (dest))
            copyfile(self.pictInfoLocation, dest)
            logger.info("... copy done !")
            logger.info("Let's import photos in : %s ..." % (self.pictDir))
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
        logger.info("... APN detected on %s", devname)
        APN_copy(devname, parent_devname, pictDir=self.pictDir)

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
            logger.critical('Any campaign specified')
            return

        self.lock.clear()

        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='block')

        self.observer = pyudev.MonitorObserver(self.monitor, self.onEvent, name='OPV SD observer')
        logger.info("You can plug SD cards in the hub")
        self.observer.start()

        try:
            while not self.lock.is_set():
                pass
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.lock.set()
        self.observer.stop()

    def onEvent(self, action, device: pyudev.Device):
        """Called when a device event happen

        :device: A pyudev device object
        """
        if action == "add" and 'DEVNAME' in device.keys() and "partition" in device.attributes.available_attributes:
            logger.info("... Device detected")
            self.APN_connected(device)
