#!/usr/bin/env python
# -*- coding: UTF-8 -*-


class ModelInitiator(object):
    """
    "   Deal with some model initialization works like DB and Condifuration files creating.
    """
    def __init__(self, model_name, model_path, db_type="json"):
        self.model_name = model_name
        self.model_path = model_path
        self.db_type = db_type

    def mkdir(self):
        data_folder_path = self.model_path + "/data"

        if not os.path.exists(data_folder_path):
            os.mkdir(data_folder_path)

    def create_db(self):
        factory_json_db_path = self.model_path + "/data/" + self.model_name + ".factory.json"
        json_db_path = self.model_path + "/data/" + self.model_name + ".json"

        if self.db_type == "json":
            if not os.path.exists(json_db_path):
                if os.path.exists(factory_json_db_path):
                    shutil.copy2(factory_json_db_path, json_db_path)


    def __del__(self):
        pass