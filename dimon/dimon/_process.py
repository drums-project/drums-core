# -*- coding: utf-8 -*-

"""
Process monitoring daemon
"""

from _common import *
import psutil

# TODO: Filter out input pids for positive integers only
class ProcessMonitor(TaskBase):
    def __init__(self, result_queue, default_interval, name = "", fields = [], pids = []):
        TaskBase.__init__(self, result_queue, default_interval, name)
        self.set_fields(fields)
        for p in list(set(pids)):
            self.register_task(p)

    # TODO: This is not thread safe
    def set_fields(self, fields):
        if fields:
            self.fields = list(set(fields))
        else:
            self.fields = ['name', 'status','get_cpu_percent', 'get_cpu_times',
            'get_memory_info','get_io_counters', 'get_threads']

    def register_task_core(self, task):
        """
        Adds a pid to the task_map
        """
        try:
            logging.debug("Registering pid: %s" % (task,))
            self.task_map[task] = psutil.Process(task)
            return ERR_SUCCESS
        except psutil.NoSuchProcess:
            logging.error("[in %s] Error adding PID (NoSuchProcess) `%s`"
                % (self, task))
            return ERR_NOTFOUND
        except psutil.AccessDenied:
            logging.error("[in %s] Error adding PID (AccessDenied) `%s`"
                % (self, task))
            return ERR_ACCESSDENIED

    def remove_task_core(self, task):
        try:
            del self.task_map[task]
            return ERR_SUCCESS
        except KeyError:
            logging.error("[in %s] Error removing PID `%s`"
                % (self, task))
            return ERR_NOTFOUND

    def do(self):
        data = dict()
        for pid, proc in self.task_map.items():
            data[pid] = dict()
            for f in self.fields:
                attr = getattr(proc, f, None)
                try:
                    if callable(attr):
                        if f == "get_cpu_percent":
                            dummy = attr(0)
                        else:
                            dummy = attr()
                    elif attr != None:
                        dummy = str(attr)
                    else:
                        logging.warning("[in %s] Attribute `%s` not found."
                            % (self, f))
                        continue
                # TODO: Fix the following circular loop
                except psutil.NoSuchProcess:
                    logging.warning("NoSuchProcess for %s, removing it", pid)
                    #self.remove_task(pid)
                except psutil.AccessDenied:
                    logging.warning("AccessDenied for %s, removing it", pid)
                    #self.remove_task(pid)

                # This is all about the s**t about pickle is not able
                # to encode/decode a nested class (used by psutils)
                # this code converts namedtuples to dict
                data[pid][f] = psutil_convert(dummy)

        if data:
            try:
                self.result_queue.put(data)
            except Queue.Full:
                logging.error("[in %s] Output queue is full in"
                    % (self, ))
            finally:
                pass#pprint(data)


