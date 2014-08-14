#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import os
import shutil
import subprocess

class ModelInitiator(object):
    """
    "   Deal with some model initialization works like DB
    "   and Condifuration files creating.
    """
    def __init__(self, model_name, model_path, db_type="json"):
        self.model_name = model_name
        self.model_path = model_path
        self.data_folder_path = self.model_path + "/data"
        self.factory_json_db_path = self.model_path + "/data/" + self.model_name + \
                                ".factory.json"
        self.json_db_path = self.model_path + "/data/" + self.model_name + ".json"
        self.db_type = db_type
        

    def mkdir(self):
        """
        "   Make a data folder for model
        """
        try:
            if not os.path.exists(self.data_folder_path):
                cmd = "mkdir -p %s" % self.data_folder_path
                subprocess.call(cmd, shell=True)
            return True
            
        except:
            return False


    def create_db(self):
        """
        "   Create a db file for model.
        """
        self.factory_json_db_path = self.model_path + "/data/" + self.model_name + \
                                ".factory.json"
        self.json_db_path = self.model_path + "/data/" + self.model_name + ".json"

        if self.db_type == "json":
            if not os.path.exists(self.json_db_path):
                if os.path.exists(self.factory_json_db_path):
                    shutil.copy2(self.factory_json_db_path, self.json_db_path)
                    return True
                else:
                    print "NO: " + self.factory_json_db_path

        return False

    def __del__(self):
        pass
        