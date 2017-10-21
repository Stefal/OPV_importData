#!/usr/bin/python3
# coding: utf-8

import os
import glob
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
    """A class which will mount and copy the APN data to work dir."""
    def __init__(self, devname, pictDir):
        threading.Thread.__init__(self)
        self.devname = devname
        self.pictDir = pictDir
        self.src = ''
        self.start()

    # Print iterations progress
    def printProgressBar(self, iteration, total, prefix='', suffix='', decimals=1, length=100, fill='█'):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print('\r%s |%s| %s%% %s' % (prefix, bar, percent, suffix), end='\r')
        # Print New Line on Complete
        if iteration == total:
            print()

    def run(self):
        logger.info("Mounting %s ...", self.devname)
        # Boooooouuuuuhhh ugly
        sleep(1)  # wait 1 sec, waiting the system to setup device block file

        if not self.foundMountedPath():
            self.mount()

        success = self.getAPNConf()
        logger.info("APN%s detected", self.apn_n)

        success = success and self.doCopy()

        self.unmount()

        if not success:
            logger.warning("Erreur lors de la copie")

    def foundMountedPath(self):
        """Return the path of the mounted path of self.devname."""
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
        """Copy all photos from the SD card."""
        self.dest = self.pictDir + "APN" + str(self.apn_n)
        # Creation of dir with the name of the apn
        os.makedirs(self.dest, exist_ok=True)
        source_dir = self.src + "/DCIM/"

        for dir in os.listdir(source_dir):
            dir_path = source_dir + dir
            logger.info("Copying started from %s to %s ...", dir_path, self.dest)
            # Get only JPG file
            files = glob.iglob(os.path.join(dir_path, "*.JPG"))
            images = glob.iglob(os.path.join(dir_path, "*.JPG"))
            l = len(list(images))
            self.printProgressBar(0, l, prefix="APN" + str(self.apn_n), suffix='Complete', length=50)
            i = 0
            for file in files:
                if os.path.isfile(file):
                    i = i + 1
                    dest_dir = self.dest + "/" + os.path.split(os.path.split(file)[0])[1] + "_" + os.path.split(file)[1]
                    command = "cp " + file + " " + dest_dir
                    self.printProgressBar(i, l, prefix="APN" + str(self.apn_n), suffix='Complete', length=50)
                    os.system(command)

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
            logger.info("... " + out.decode('ascii'))
        except subprocess.CalledProcessError:
            logger.error("{} not mounted".format(self.devname))
            return False
        except FileNotFoundError:
            logger.error("udisks not installed on system")
            return False
        return True

    def unmount(self):
        """Unmount devname using udisckctl."""
        try:
            p = subprocess.Popen(['udisksctl', 'unmount', '-b', self.devname], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = p.communicate()
            logger.info("... " + out.decode('ascii'))
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
        """ Set as True when apn is finish to copy."""
        self.APN_treated[apn_n] = True
        logger.info("APN %s finished", apn_n)
        if all(self.APN_treated):
            self.stop()

    def APN_connected(self, device: pyudev.Device):
        """ A fct which will start a thread to copy the SDCARD
        :device: the device where is situed the APN
        """
        devname = device['DEVNAME']
        logger.info("... APN detected on %s", devname)
        APN_copy(devname, pictDir=self.pictDir)
        self.APN_copied(apn_n)

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
