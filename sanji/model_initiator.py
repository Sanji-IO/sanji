#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import logging
import simplejson as json
import os
import shutil
import subprocess
import time
from threading import Thread
from threading import Event
from threading import RLock

_logger = logging.getLogger("sanji.sdk.model_initiator")


class ModelInitiator(object):
    """
    "   Deal with some model initialization works like DB
    "   and Condifuration files creating.
    "   [backup_inteval]: backup db every hours(s), minus means no backup.
    """
    def __init__(
            self, model_name, model_path, db_type="json", backup_interval=720):
        self.model_name = model_name
        self.model_path = model_path
        self.db = None
        self.data_folder_path = self.model_path + "/data"
        self.factory_json_db_path = self.model_path + "/data/" + \
            self.model_name + ".json.factory"
        self.backup_json_db_path = self.model_path + "/data/" + \
            self.model_name + ".json.backup"
        self.json_db_path = self.model_path + "/data/" + \
            self.model_name + ".json"
        self.db_type = db_type
        self.db_status = None
        self.backup_interval = backup_interval * 3600  # hour
        self.db_mutex = RLock()
        self.db_manager()

        self._backup_thread = Thread(target=self.thread_backup_db)
        self._backup_thread.daemon = True
        self._backup_thread_event = Event()
        if self.backup_interval > 0:
            self.start_backup()

    def db_manager(self):
        """
        " Do series of DB operations.
        """
        rc_create = self.create_db()    # for first create
        try:
            self.load_db()  # load existing/factory
        except Exception as e:
            _logger.debug("*** %s" % str(e))
            try:
                self.recover_db(self.backup_json_db_path)
            except Exception:
                pass
        else:
            if rc_create is True:
                self.db_status = "factory"
            else:
                self.db_status = "existing"
            return True

        try:
            self.load_db()  # load backup
        except Exception as b:
            _logger.debug("*** %s" % str(b))
            self.recover_db(self.factory_json_db_path)
            self.load_db()  # load factory
            self.db_status = "factory"
        else:
            self.db_status = "backup"
        finally:
            return True

    def create_db(self):
        """
        "   Create a db file for model if there is no db.
        "   User need to prepare thier own xxx.json.factory.
        """
        if self.db_type != "json":
            raise RuntimeError("db_type only supports json now")

        if os.path.exists(self.json_db_path):
            return False

        if os.path.exists(self.factory_json_db_path):
            with self.db_mutex:
                shutil.copy2(
                    self.factory_json_db_path, self.json_db_path)
            return True

        _logger.debug(
            "*** NO such file: %s" % self.factory_json_db_path)
        raise RuntimeError("No *.json.factory file")

    def recover_db(self, src_file):
        """
        " Recover DB from xxxxx.backup.json or xxxxx.json.factory to xxxxx.json
        " [src_file]: copy from src_file to xxxxx.json
        """
        with self.db_mutex:
            try:
                shutil.copy2(src_file, self.json_db_path)
            except IOError as e:
                _logger.debug("*** NO: %s file." % src_file)
                raise e

    def backup_db(self):
        """
        " Generate a xxxxx.backup.json.
        """
        with self.db_mutex:
            if os.path.exists(self.json_db_path):
                try:
                    shutil.copy2(self.json_db_path, self.backup_json_db_path)
                except (IOError, OSError):
                    _logger.debug("*** No file to copy.")

    def load_db(self):
        """
        " Load json db as a dictionary.
        """
        try:
            with open(self.json_db_path) as fp:
                self.db = json.load(fp)
        except Exception as e:
            _logger.debug("*** Open JSON DB error.")
            raise e

    def save_db(self):
        """
        " Save json db to file system.
        """
        with self.db_mutex:
            if not isinstance(self.db, dict) and not isinstance(self.db, list):
                return False
            try:
                with open(self.json_db_path, "w") as fp:
                    json.dump(self.db, fp, indent=4)
            except Exception as e:
                # disk full or something.
                _logger.debug("*** Write JSON DB to file error.")
                raise e

            else:
                self.sync()
                return True

    def start_backup(self):
        if self._backup_thread.is_alive():
            raise RuntimeError("Stop previous backup thread first.")

        self._backup_thread = Thread(target=self.thread_backup_db)
        self._backup_thread.daemon = True
        self._backup_thread.start()
        return True

    def stop_backup(self, timeout=None):
        if self._backup_thread.is_alive():
            self._backup_thread_event.set()
            if timeout:
                self._backup_thread.join(timeout)
            else:
                self._backup_thread.join()
            return True
        return False

    def thread_backup_db(self):
        single_sleep_time = 2
        sleep_count = self.backup_interval
        while not self._backup_thread_event.is_set():
            if sleep_count >= self.backup_interval:
                self.backup_db()
                sleep_count = 0
            else:
                time.sleep(single_sleep_time)
                sleep_count += single_sleep_time

    def sync(self):
        """
        " Call Linux 'sync' command to write data from RAM to flash.
        """
        cmd = "sync"
        subprocess.call(cmd, shell=True)
