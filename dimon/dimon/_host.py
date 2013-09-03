# -*- coding: utf-8 -*-

"""
Host monitoring daemon
"""

from _common import *
import psutil
from pprint import pprint

class HostMonitor(TaskBase):
    def __init__(self, result_queue, default_interval, name = "", fields = [], pids = []):
        TaskBase.__init__(self, result_queue, default_interval, name)
        self.set_fields(fields)
        for p in list(set(pids)):
            self.register_task(p)

    def set_fields(self, fields):
        if len(fields) > 0:
            self.fields = list(set(fields))
        else:
            # TODO: why does get_boot_time() throw exception?
            self.fields = ['BOOT_TIME', 'cpu_percent', 'cpu_times',
            'virtual_memory','swap_memory', 'disk_usage',
            'disk_io_counters', 'net_io_counters']

            # I hate these version compatibility hack!
            # Even on Ubuntu 13.04, python-psutil point to 0.6
            # while latest version is 1.1 !

            # TODO change fields to dict {attr: psutil function}
            self.net_hack = psutil.version_info < (1, 1, 0)
            if self.net_hack:
                self.fields.append('network_io_counters')


    def register_task_core(self, task):
        """
        Adds a pid to the task_map
        """
        logging.debug("Registering host")
        self.task_map['host'] = psutil


    def remove_task_core(self, task):
        try:
            del self.task_map['host']
        except KeyError:
            logging.warning("Error removing host")

    def do(self):
        data = dict()
        if not 'host' in self.task_map:
            return

        data['host'] = dict()
        for f in self.fields:
            # Due to lots of variation in function calls, it is better
            # to rewrite the code from _process.py
            attr = getattr(psutil, f, None)
            if callable(attr):
                if f == "cpu_percent":
                    dummy = attr(interval = 0, percpu = True)
                elif f == "cpu_times":
                    dummy = attr(percpu = False)
                #elif f in ["disk_io_counters", "disk_usage"]:
                    # TODO: Implement this
                #    continue
                elif f in ["net_io_counters", "network_io_counters"]:
                    # TODO: pernic=True returns a dict to tuples
                    # which psutil_convert() function does not know
                    # how to convert it yet
                    dummy = attr(pernic = False)
                elif f in ["virtual_memory", "swap_memory"]:
                    dummy = attr()
                else:
                    # Not supported yet
                    continue
            elif attr != None:
                dummy = str(attr)
            else:
                logging.debug("[in %s] Attribute `%s` not found."
                    % (self, f))
                continue

            # This is all about the s**t about pickle is not able
            # to encode/decode a nested class (used by psutils)
            # this code converts namedtuples to dict
            #pprint(dummy)
            if self.net_hack and f == 'network_io_counters':
                f = 'net_io_counters'

            data['host'][f] = psutil_convert(dummy)

        if data:
            try:
                self.result_queue.put(data)
            except Queue.Full:
                logging.error("[in %s] Output queue is full in"
                    % (self, ))
            finally:
                pass#pprint(data)
