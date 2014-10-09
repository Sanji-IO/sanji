#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import json
import os
import shutil
import subprocess
import time
import threading


class ModelInitiator(object):
    """
    "   Deal with some model initialization works like DB
    "   and Condifuration files creating.
    "   [backup_inteval]: backup db every hours(s)
    """
    def __init__(
            self, model_name, model_path, db_type="json", backup_interval=720):
        self.model_name = model_name
        self.model_path = model_path
        self.db = None
        self.data_folder_path = self.model_path + "/data"
        self.factory_json_db_path = self.model_path + "/data/" + \
            self.model_name + ".factory.json"
        self.backup_json_db_path = self.model_path + "/data/" + \
            self.model_name + ".backup.json"
        self.json_db_path = self.model_path + "/data/" + \
            self.model_name + ".json"
        self.db_type = db_type
        self.backup_interval = backup_interval * 3600  # hour
        self.db_mutex = threading.RLock()
        self.db_manager()

        if self.backup_interval > 0:
            self.periodic_backup_db()

    def db_manager(self):
        """
        " Do series of DB operations.
        """
        self.create_db()
        try:
            self.load_db()
        except Exception as e:
            print "***", e
            self.recover_db(self.backup_json_db_path)
        else:
            return True

        try:
            self.load_db()
        except Exception as b:
            print "***", b
            self.revocer_db(self.factory_json_db_path)

    def create_db(self):
        """
        "   Create a db file for model if there is no db.
        "   User need to prepare thier own xxx.factory.json.
        """
        if self.db_type == "json":
            if not os.path.exists(self.json_db_path):
                if os.path.exists(self.factory_json_db_path):
                    with self.db_mutex:
                        shutil.copy2(
                            self.factory_json_db_path, self.json_db_path)
                    return True
                else:
                    print "*** NO: " + self.factory_json_db_path

        return False

    def recover_db(self, src_file):
        """
        " Recover DB from xxxxx.backup.json or xxxxx.factory.json to xxxxx.json
        " [src_file]: copy from src_file to xxxxx.json
        """
        with self.db_mutex:
            shutil.copy2(src_file, self.json_db_path)

    def backup_db(self):
        """
        " Generate a xxxxx.backup.json.
        """
        with self.db_mutex:
            shutil.copy2(self.json_db_path, self.backup_json_db_path)

    def load_db(self):
        """
        " Load json db as a dictionary.
        """
        try:
            with open(self.json_db_path) as fp:
                self.db = json.load(fp)
        except Exception as e:
            print "*** Open JSON DB error."
            raise e

    def save_db(self):
        """
        " Save json db to file system.
        """
        with self.db_mutex:
            try:
                with open(self.json_db_path, "w") as fp:
                    json.dump(self.db, fp, indent=4)
            except Exception:
                print "*** Write JSON DB to file error."
            else:
                self.sync()

    def periodic_backup_db(self):
        """
        " Fork a thread to backup db periodically.
        """
        t = threading.Thread(target=self.thread_backup_db)
        t.daemon = True
        t.start()

    def thread_backup_db(self):
        while True:
            self.backup_db()
            time.sleep(self.backup_interval)

    def sync(self):
        """
        " Call Linux 'sync' command to write data from RAM to flash.
        """
        cmd = "sync"
        subprocess.call(cmd, shell=True)

    def __del__(self):
        pass
