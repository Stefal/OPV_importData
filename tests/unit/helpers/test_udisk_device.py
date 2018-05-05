# coding: utf-8

# Copyright (C) 2017 Open Path View, Maison Du Libre
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

# Contributors: Benjamin BERNARD <benjamin.bernard@openpathview.fr>
# Email: team@openpathview.fr
# Description: Test - Abstract helper to manage copies from an external device (SD cards, hardrives ...).

import pytest
import subprocess
from opv_import.helpers import UdiskDevice
from opv_import.helpers.udisk_device import MountError, UnMountError, MissingUdiskError
from path import Path
from unittest.mock import patch, call, MagicMock


class TestUdiskDevice(object):

    def test__udisks_extract_mount_path(self):
        dev = UdiskDevice(device_name="/dev/sdc1")
        assert dev._udisks_extract_mount_path(
            udisk_output='Mounted /dev/sdc1 at /media/benjamin/B291-4FA9.\n') == Path("/media/benjamin/B291-4FA9")
        assert dev._udisks_extract_mount_path(
            udisk_output='\nMounted /dev/sdc1 at /media/benjamin/B291-4FA9.\n\n') == Path("/media/benjamin/B291-4FA9")
        assert dev._udisks_extract_mount_path(
            udisk_output='\nMounted /dev/sdc1 at \n') is None

    @patch("subprocess.Popen")
    def test_mount_ok(self, mock_popen):
        p = MagicMock()
        p.communicate = MagicMock()
        out = MagicMock(bytes)
        out.decode = MagicMock()
        out.decode.return_value = 'Mounted /dev/sdc1 at /media/benjamin/B291-4FA9.\n'
        p.communicate.return_value = (out, MagicMock())
        mock_popen.return_value = p

        dev = UdiskDevice(device_name="/dev/sdc1")
        assert dev.mount() == "/media/benjamin/B291-4FA9"
        assert mock_popen.call_args_list == [call(['udisksctl', 'mount', '-b', '/dev/sdc1'], stderr=-1, stdout=-1)]

    @patch("subprocess.Popen")
    def test_mount_udisk_fail(self, mock_popen):
        mock_popen.side_effect = subprocess.CalledProcessError(returncode=-1, cmd=None)
        dev = UdiskDevice(device_name="/dev/sdc1")
        with pytest.raises(MountError):
            dev.mount()

        assert mock_popen.call_args_list == [call(['udisksctl', 'mount', '-b', '/dev/sdc1'], stderr=-1, stdout=-1)]

    @patch("subprocess.Popen")
    def test_mount_udisk_not_installed(self, mock_popen):
        mock_popen.side_effect = FileNotFoundError()
        dev = UdiskDevice(device_name="/dev/sdc1")
        with pytest.raises(MissingUdiskError):
            dev.mount()

        assert mock_popen.call_args_list == [call(['udisksctl', 'mount', '-b', '/dev/sdc1'], stderr=-1, stdout=-1)]

    @patch("subprocess.Popen")
    def test_unmount_ok(self, mock_popen):
        p = MagicMock()
        p.communicate = MagicMock()
        p.communicate.return_value = (MagicMock(), MagicMock())
        mock_popen.return_value = p

        dev = UdiskDevice(device_name="/dev/sdc1")
        dev.unmount()
        assert mock_popen.call_args_list == [call(['udisksctl', 'unmount', '-b', '/dev/sdc1'], stderr=-1, stdout=-1)]

    @patch("subprocess.Popen")
    def test_unmount_udisk_fail(self, mock_popen):
        mock_popen.side_effect = subprocess.CalledProcessError(returncode=-1, cmd=None)
        dev = UdiskDevice(device_name="/dev/sdc1")
        with pytest.raises(UnMountError):
            dev.unmount()

        assert mock_popen.call_args_list == [call(['udisksctl', 'unmount', '-b', '/dev/sdc1'], stderr=-1, stdout=-1)]

    @patch("subprocess.Popen")
    def test_unmount_udisk_not_installed(self, mock_popen):
        mock_popen.side_effect = FileNotFoundError()
        dev = UdiskDevice(device_name="/dev/sdc1")
        with pytest.raises(MissingUdiskError):
            dev.unmount()

        assert mock_popen.call_args_list == [call(['udisksctl', 'unmount', '-b', '/dev/sdc1'], stderr=-1, stdout=-1)]

    @patch("builtins.open", create=True)
    def test__find_mount_path_ok(self, mock_open):
        proc_mounts_fake = """
tmpfs /mnt/lxc/lxd/devlxd tmpfs rw,relatime,size=100k,mode=755 0 0
opv@10.224.142.72:/home/opv/dev/ /home/benjamin/devMaster fuse.sshfs rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
/dev/sda4 /mnt/lxc/lxd/containers/master/rootfs/mnt/opv ext4 rw,relatime,data=ordered 0 0
/dev/sdc1 /media/benjamin/B291-4FA9 vfat rw,nosuid,nodev,relatime,uid=1000,gid=1000,fmask=0022,dmask=0022,codepage=437,iocharset=iso8859-1,shortname=mixed,showexec,utf8,flush,errors=remount-ro 0 0
gvfsd-fuse /run/user/1000/gvfs fuse.gvfsd-fuse rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
"""
        ctx_open = MagicMock()
        ctx_open.__enter__ = MagicMock()
        ctx_open.__enter__.return_value = proc_mounts_fake.split("\n")
        ctx_open.__exit__ = MagicMock()
        mock_open.return_value = ctx_open

        dev = UdiskDevice(device_name="/dev/sdc1")

        assert dev._find_mount_path() == Path("/media/benjamin/B291-4FA9")
        mock_open.assert_called_with("/proc/mounts", 'r')

    @patch("builtins.open", create=True)
    def test__find_mount_path_not_mounted(self, mock_open):
        proc_mounts_fake = """
    tmpfs /mnt/lxc/lxd/devlxd tmpfs rw,relatime,size=100k,mode=755 0 0
    opv@10.224.142.72:/home/opv/dev/ /home/benjamin/devMaster fuse.sshfs rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
    /dev/sda4 /mnt/lxc/lxd/containers/master/rootfs/mnt/opv ext4 rw,relatime,data=ordered 0 0
    gvfsd-fuse /run/user/1000/gvfs fuse.gvfsd-fuse rw,nosuid,nodev,relatime,user_id=1000,group_id=1000 0 0
    """
        ctx_open = MagicMock()
        ctx_open.__enter__ = MagicMock()
        ctx_open.__enter__.return_value = proc_mounts_fake.split("\n")
        ctx_open.__exit__ = MagicMock()
        mock_open.return_value = ctx_open

        dev = UdiskDevice(device_name="/dev/sdc1")

        assert dev._find_mount_path() == None
        mock_open.assert_called_with("/proc/mounts", 'r')

    @patch("opv_import.helpers.UdiskDevice._find_mount_path")
    def test_is_mounted_notmounted(self, mock_find_mount_path):
        dev = UdiskDevice(device_name="/dev/sdc1")

        mock_find_mount_path.return_value = None

        assert not dev.is_mounted()
        assert mock_find_mount_path.call_count == 1

    @patch("opv_import.helpers.UdiskDevice._find_mount_path")
    def test_is_mounted_ok(self, mock_find_mount_path):
        dev = UdiskDevice(device_name="/dev/sdc1")

        mounted_path = MagicMock(Path)
        mounted_path.exists = MagicMock()
        mounted_path.exists.return_value = True
        mock_find_mount_path.return_value = mounted_path

        assert dev.is_mounted()
        assert mock_find_mount_path.call_count == 1