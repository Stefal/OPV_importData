#!/usr/bin/python3
# coding: utf-8

"""
Usage:
   cleanSD <iso-path>
   cleanSD -h | --help
"""


import json
import pyudev
import threading
import subprocess
import os
import docopt

from time import sleep
from path import Path

import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def main():
    args = docopt.docopt(__doc__)
    m = Main(Path(args['<iso-path>']))
    m.start()

class APN_clean(threading.Thread):
    """
    A class which will mount and copy the APN data to work dir
    """
    def __init__(self, devname, parent_devname, main):
        threading.Thread.__init__(self)
        self.devname = devname
        self.parent_devname = parent_devname
        self.start()
        self.main = main

    def run(self):
        logger.info("APN_copy -- run ", self.devname)
        # Boooooouuuuuhhh ugly
        sleep(1)  # wait 1 sec, waiting the system to setup device block file

        if not self.foundMountedPath():
            self.mount()

        self.getAPNConf()

        self.unmount()

        if self.apn_n in self.main.apns_done:
            return

        self.doClearSD()

        self.main.apns_done.add(self.apn_n)

    def foundMountedPath(self):
        """
        Return the path of the mounted path of self.devname
        """
        with open("/proc/mounts", "r") as mounts:
            for line in mounts:
                if line.startswith(self.devname):
                    return Path(line.split(' ')[1])

    def doClearSD(self):
        """
        Reset the SD card
        return False on error, True otherwise
        """
        iso = self.main.iso_path
        iso = os.path.expanduser(iso)

        logger.info("Starting to clear APN", self.apn_conf['APN_num'])
        subprocess.run(['sudo', 'dd', 'if=' + iso, 'of=' + self.parent_devname])
        logger.info("APN", self.apn_n, "cleared")

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
    def __init__(self, iso_path):
        self.cv = threading.Condition()
        self.APN_treated = [False for x in range(6)]
        self.wait_for_sd_card = WaitForSDCard(self)
        self.iso_path = iso_path
        self.apns_done = set()

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
        APN_clean(devname, parent_devname, self)

    def start(self):
        self.wait_for_sd_card.start()

        try:
            with self.cv:
                while True:
                    self.cv.wait()
        except KeyboardInterrupt:
            pass
        self.stop()

    def stop(self):
        self.wait_for_sd_card.stop()

class WaitForSDCard:
    def __init__(self, main):
        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(self.context)
        self.monitor.filter_by(subsystem='block')
        self.main = main
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
            self.main.APN_connected(device)


if __name__ == "__main__":
    main()
