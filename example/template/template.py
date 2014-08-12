#!/usr/bin/env python
# -*- coding: UTF-8 -*-

import sys
import json
import sqlite3
import logging
import subprocess
import time



import os
path_root = os.path.abspath(os.path.dirname(__file__))

sys.path.append(path_root + "/../../lib/")

from sanji import Sanji
from sanjilogger import *


CODE_OK = 200
CODE_BAD_REQUEST = 400
CODE_INTERNAL_SERVER_ERROR = 500

model_name = "template"

# Sanji's model profile (for MQTT usage)
sanji_profile = {
			"client_id": model_name,
			"tunnel": "/" + model_name,
			"name": model_name,
			"description": model_name,
			"resources": ["/system" + "/" + model_name],
			"role": "model",
			"ttl": 60,
			"hook": [],
		}


# Model's profile. (for Model usage)
model_profile = {
			"model_db": path_root + "/db/" + model_name + ".json",
			"model_factory_db": path_root + "/db/" + model_name + ".factory" + ".json",
		}

class Template(Sanji):
	def __init__(self, *args, **kwargs):
		super(Template, self).__init__(model_name, path_root)
		



if __name__ == '__main__':
	t = Template()
