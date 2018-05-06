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
# Description: A simple thread pool with queue.

import logging
from queue import Queue
import threading


class ThreadPool:

    def __init__(self, number_of_workers):
        """
        Initiate a thread pool.
        :param number_of_workers: Number of max allowed threads at the same time.
        """
        self.logger = logging.getLogger(self.__module__ + "." + self.__class__.__name__)
        self._number_of_workers = number_of_workers
        self.__task_queue = Queue()   # creates a FIFO queue

    def __worker(self):
        """ Main thread task runner. """
        while True:
            task = self.__task_queue.get()
            if task is None:
                break
            task()
            self.__task_queue.task_done()

    def __init_threads(self):
        """
        Init workers.
        """
        self.logger.debug("Initing thread with pool size of %i", self._number_of_workers)
        self.__threads = []
        for i in range(0, self._number_of_workers):
            t = threading.Thread(target=self.__worker)
            t.start()
            self.__threads.append(t)

    def add_task(self, task):
        """
        Add a task to be threated.
        :param task: Simply a callable with no arguments.
        """
        self.logger.debug("Task added to thread pool")
        self.__task_queue.put_nowait(task)

    def stop(self):
        """
        Stop the thead pull.
        :return:
        """
        self.logger.debug("Stopping thread pool ...")
        for i in range(0, self._number_of_workers):   # Send None task to all workers to kill them
            self.__task_queue.put(None)

        for t in self.__threads:  # wait for all threads to join, before releasing
            t.join()
        self.logger.debug("Thread pool stopped")

    def start(self):
        """
        Start the workers.
        """
        self.logger.debug("Starting thread pool ...")
        self.__init_threads()
        self.logger.debug("Thread started")
