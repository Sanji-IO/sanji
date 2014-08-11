#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import mosquitto
import json
import time
import copy
import logging
import sys
import sqlite3
import glob
import inspect 	# for debug frame
import os
import shutil

from router import *
from random import randint
from threading import Thread
from threading import Lock
from datetime import datetime


path_root = os.path.abspath(os.path.dirname(__file__))
sys.path.append(path_root + '/../')
from sanjilogger import *


CODE_OK = 200
CODE_BAD_REQUEST = 400
CODE_INTERNAL_SERVER_ERROR = 500


try:
	broker_ip = os.environ['BROKER_IP']
except:
	broker_ip = "127.0.0.1"

try:
	broker_port = int(os.environ['BROKER_PORT'])
except:
	broker_port = 1883



class Sanji(object):
	'''
	' This is for sanji framework.
	'''
	def __init__(self, model_name, model_path):
		self.model_name = model_name
		self.model_path = model_path
		self.model_initiator = ModelInitiator(self.model_name, self.model_path)
		self.model_initiator.mkdir()
		self.model_initiator.create_db()
		


class ModelInitiator(object):
	'''
	'	Deal with some model initialization works like DB and Condifuration files creating.
	'''
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



class SanjiJSON(object):
	'''
	' Provide JSON operations.
	' Format Example:
		{
			"id":3,
			"method":"get",
			"resource": "/services",
			"code": 200,
			"data": {
				"resources":["http_server","dhcp_server"]
			}
		}
	'''
	def __init__(self, model_name):
		pass


		


class SanjiURI(object):
	'''
	' Provide URI operations.
	' We could use URI parser to parsing uri in resources.
	'''
	def __init__(self, model_name):
		self.resource_dict = {"index": "", 			# 7
								"full_name": "", 	# /network/ethernet
								"full_uri": "", 	# /network/ethernet/7
								"short_name": "", 	# /ethernet
							}

		pass





class Session(object):
	def __init__(self):
		pass










class JsonDB(object):
	def __init__(self):
		pass





class Model2Model(object):
	def __init__(self):
		pass


if __name__ == '__main__':
	pass