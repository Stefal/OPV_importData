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
# Description: Start rsync with progress, and onProgress

import logging
import subprocess

from path import Path
from typing import Iterator

RSYNC_ARG_PROGRESS = ["-P"]
RSYNC_DEFAULT_ARGS = ["-av"]

class RsyncWrapper():
    """ Simple rsync wrapper with progress events. Works with rsync version 3.1.1."""

    def __init__(self, source_path: Path, destination_path: Path):
        """
        Initiate a simple rsync wrapper/
        :param source_path: Source folder/file to be transfered.
        :param destination_path: Destination folder/file to be transfered.
        """
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)

        self._source = source_path
        self._destination = destination_path
        self._progression_listeners = {}  # dict of listeners listener name/id => lambda to execute
        self._terminate_listeners = {}  # dict of listeners listener name/id => lambda to execute

        self._current_proc = None  # popen returned object
        self._global_progress = 0  # Last global progress

    def on_progress(self, event_listener, even_listener_name: str = None) -> str:
        """
        Register a progress event. Lambda "event_listener" will be executed each time the transfert
        progression evolves. For instance at 10% (global progression) the wrapper will call : event_listener(0.1)
        At the end it will call your lambda with event_listener(1).

        Your lambda should not return any value, you can set a name to your lambda if you want to override it
        otherwise an id will be attributed. The name/id of the listener will be returned, you can't have 2 listeners
        with the same id.
        :param event_listener: Your lamabda listener will be called at each step of the progression (Callable[int])
        :param even_listener_name: A listener unique name, can be used to override your listener. Optional.
        :return: The listener unique name.
        """
        if even_listener_name is None:
            even_listener_name = "progress_{id}".format(id=len(self._progression_listeners))

        self._progression_listeners.update({even_listener_name: event_listener})
        return even_listener_name

    def __fire_progress_event(self, global_progression: float):
        """
        Fire global progression event.
        :param global_progression: Global progression from 0 to 1.
        """
        self._global_progress = global_progression
        for listener in self._progression_listeners.values():
            listener(global_progression)

    def on_terminate(self, event_listener, even_listener_name: str = None) -> str:
        """
        Register a terminate event. Lambda "event_listener" will be executed at the end of the transfert with no arguments.

        Your lambda should not return any value, you can set a name to your lambda if you want to override it
        otherwise an id will be attributed. The name/id of the listener will be returned, you can't have 2 listeners
        with the same id.
        :param event_listener: Your lamabda listener will be called at the end of the transfert (Callable[])
        :param even_listener_name: A listener unique name, can be used to override your listener. Optional.
        :return: The listener unique name.
        """
        if even_listener_name is None:
            even_listener_name = "terminate_{id}".format(id=len(self._progression_listeners))

        self._terminate_listeners.update({even_listener_name: event_listener})
        return even_listener_name

    def __fire_terminate_event(self):
        """ Fire terminate event."""
        for listener in self._terminate_listeners.values():
            listener()

    def _read_current_popen_stdout(self) -> Iterator[str]:
        """
        Consume the ouput of the rsync command and give lines.
        Break at the end.
        :return: The last line.
        """
        line = ''
        while self._current_proc.stdout:
            try:
                c = self._current_proc.stdout.read(1)
                c = c.decode("utf8")
            except IOError as e:
                self.logger.error(e)
                continue
            if c == '\r':
                # line is being updated
                yield line
                line = ''
            elif c == '\n':
                # line is done
                yield line
                line = ''
            elif c == '':
                break
            else:
                line += c

    def _run_command(self):
        """
        Run the transfert. Works with rsync version 3.1.1.
        """
        self.logger.debug("Running rsync, copy %s -> %s", self._source, self._destination)
        args = RSYNC_ARG_PROGRESS + RSYNC_DEFAULT_ARGS + [self._source, self._destination]
        self._current_proc = subprocess.Popen(['rsync'] + args,
                                              stdout=subprocess.PIPE)

        # Consume the output
        for line in self._read_current_popen_stdout():
            parts = line.split()
            if len(parts) == 6 and parts[1].endswith('%') and parts[-1].startswith('to-chk='):
                # file progress -P
                # file_progress = parts[1]
                # file_speed = parts[2]
                # file_eta = parts[3]
                istr, ntotalstr = parts[-1][len('to-chk='):-1].split('/')
                ntotal = int(ntotalstr)
                i = int(istr)
                j = ntotal - i
                total_progress = j / int(ntotal)
                self.__fire_progress_event(global_progression=total_progress)

        self.__fire_terminate_event()

    def run(self):
        """ Run the copy."""
        self._run_command()

    @property
    def global_progress(self) -> float:
        """
        Get global progress from 0 to 1.
        :return: Global progression (between 0 to 1)
        """
        return self._global_progress
